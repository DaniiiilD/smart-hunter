from fastapi import FastAPI, Depends
from database import engine, Base, get_async_session
from models import User, Vacancy, Resume
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import UserCreate, UserLogin, ResumeCreate, MatchRequest
from fastapi import HTTPException
from sqlalchemy import select
from passlib.context import CryptContext
from hh_client import get_vacancies, get_vacancy_full_text
from tasks import analyze_resume_task
from celery.result import AsyncResult
from celery_app import celery_app

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("База данных готова!")
    yield
    
    
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Smart Hunter is alive!"}


@app.post("/register")
async def register_user(user_data: UserCreate,
                        session: AsyncSession = Depends(get_async_session)):
    """
    Эндпоинт регистрации.
    user: данные, которые пришли от пользователя.
    session: подключение к БД (Dependency Injection).
    """
    
    query = select(User).where(User.email == user_data.email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким email уже сущетсвует')
    
    hashed_pass = pwd_context.hash(user_data.password)
    
    new_user = User(email=user_data.email,
                    hashed_password=hashed_pass)
    
    session.add(new_user)
    await session.commit()
    
    return {"status": "success", "msg": "Вы успешно зарегестрированы"}

@app.post("/login")
async def login_user(user_data: UserLogin,
                     session: AsyncSession = Depends(get_async_session)):
    """
    Эндпоинт логина.
    user: данные, которые пришли от пользователя.
    session: подключение к БД (Dependency Injection).
    """
    query = select(User).where(User.email == user_data.email)
    result = await session.execute(query)
    user_from_db = result.scalar_one_or_none()

    if user_from_db is None:
        raise HTTPException(status_code=400, detail='Неверный email или пароль')
    
    password_check = pwd_context.verify(user_data.password, user_from_db.hashed_password)
    
    
    if password_check:
        return {"status": "success", "msg": "Login correct!"}
    else:
        raise HTTPException(status_code=400, detail="Невверный email или пароль ")
    
@app.get("/vacancies")
async def search_vacancies(text: str,
                           session: AsyncSession = Depends(get_async_session)):
    """
    Ищет вакансии по запросу text.
    Пример: /vacancies?text=java
    """
    print(f"Ищу вакансии по запросу: {text}")
    found_jobs = await get_vacancies(text)
    saved_vacancies_counter = 0
    
    for job in found_jobs:
        
        hh_id_from_api = job.get('id')
        query = select(Vacancy).where(Vacancy.hh_id == hh_id_from_api)
        result = await session.execute(query)
        existing_vacancy = result.scalar_one_or_none()
        
        if existing_vacancy is None:
            new_vacancy = Vacancy(hh_id = hh_id_from_api,
                                  name = job.get('name'),
                                  url = job.get('alternate_url'))
            session.add(new_vacancy)
            saved_vacancies_counter+=1
        else:
            pass
    
    await session.commit()
    return {"found_on_hh" : len(found_jobs),
            "saved_new" : saved_vacancies_counter}



@app.post("/resume")
async def save_resume(resume: ResumeCreate,
                      email: str,
                      session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user_from_db = result.scalar_one_or_none()
    
    if user_from_db is None:
        raise HTTPException(status_code=404, detail = "Пользователь с таким email не найден")
    
    new_resume = Resume(user_id = user_from_db.id,
                        content = resume.content)
    
    session.add(new_resume)
    await session.commit()
    
    return {"status": "success", "msg": f"Резюме для {email} сохранено"}


@app.post("/vacancies/{hh_id}/fill")
async def fill_vacancy_description(hh_id: str,
                                   session: AsyncSession = Depends(get_async_session)
                                   ):
    """
    1. Ищет вакансию в БД по hh_id.
    2. Если описания нет - скачивает с HH и сохраняет.
    """
    query = select(Vacancy).where(Vacancy.hh_id == hh_id)
    result = await session.execute(query)
    vacancy = result.scalar_one_or_none()
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail='Вакансии нет в Базе Данных')
    
    if vacancy.description:
        return {"status": "cached", "description": vacancy.description}
    
    full_text = await get_vacancy_full_text(hh_id)
    
    if not full_text:
        raise HTTPException(status_code=404, deatail='Не удалось полчить данные с HH.ru')
    
    vacancy.description = full_text
    await session.commit()
    
    return {"status": "updated", "description": full_text}

@app.post("/match")
async def match_resume_vacancy(match_data: MatchRequest,
                               session: AsyncSession = Depends(get_async_session)
                               ):
    
    query_resume = select(Resume).where(Resume.id == match_data.resume_id)
    result_resume = await session.execute(query_resume)
    resume = result_resume.scalar_one_or_none()
    
    if resume is None:
        raise HTTPException(status_code=404, detail="Резюме с таким id не найдено")
    
    query_vacancy = select(Vacancy).where(Vacancy.id == match_data.vacancy_id)
    result_vacancy = await session.execute(query_vacancy)
    vacancy = result_vacancy.scalar_one_or_none()
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Вакансия с таким id не найдена")
    
    if not vacancy.description:
        raise HTTPException(status_code=400,
                            detail="у этой вакансии пустое описание. Сначала выполните запрос /fill")
        
    task = analyze_resume_task.delay(resume.content, vacancy.description)
    
    return {
        "status": "processing",
        "task_id": task.id, #Клиент получает id своего чека
        "message": "Задача отправлена в обработку. Проверьте результат позже."
    }
    
@app.get("/vacancies/{internal_id}")
async def get_vacancy_info(
    internal_id: int, 
    session: AsyncSession = Depends(get_async_session)
):
    query = select(Vacancy).where(Vacancy.id == internal_id)
    result = await session.execute(query)
    vacancy = result.scalar_one_or_none()
    
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
        
    return {
        "id": vacancy.id, 
        "hh_id": vacancy.hh_id, 
        "name": vacancy.name, 
        "has_description": bool(vacancy.description)
    }
    
@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == 'SUCCESS':
        response["result"] = task_result.result
    elif task_result.status == 'FAILURE':
        response["result"] = str(task_result.result)
        
    return response

@app.get("/all_resumes")
async def get_all_resumes(session: AsyncSession = Depends(get_async_session)):
    """
    Возвращает список всех резюме из базы, чтобы фронтенд мог их показать в списке.
    """
    query = select(Resume)
    result = await session.execute(query)
    resumes = result.scalars().all()
    return resumes