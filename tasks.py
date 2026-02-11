import time
import random
from celery_app import celery_app

@celery_app.task(name="analyze_resume_task")
def analyze_resume_task(resume_text: str, vacancy_text: str):
    """
    Эта функция будет выполняться ОТДЕЛЬНО, на другом процессе (Worker).
    """
    #AI imitaion
    time.sleep(10)
    
    score = random.randint(50, 99)
    result_text = f"""
    [AI ANALYZED ASYNC]
    Совместимость: {score}%
    
    Анализ резюме (выполнено в фоне):
    Кандидат подходит. Мы проверили это через Celery!
    Текст вакансии: {vacancy_text[:30]}...
    """
    
    return result_text