import streamlit as st
import requests
import time
import os

# Настройка адреса (Локально или Докер)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Smart Hunter")

# Инициализация состояния
if 'page' not in st.session_state:
    st.session_state['page'] = "Регистрация"
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

# Навигация
def navigate():
    st.session_state['page'] = st.session_state.menu_selection

# БОКОВОЕ МЕНЮ
with st.sidebar:
    st.title("Меню")
    if st.session_state['user_email']:
        st.success(f"Вы вошли как: {st.session_state['user_email']}")
        if st.button("Выйти"):
            st.session_state['user_email'] = None
            st.session_state['page'] = "Авторизация"
            st.rerun()
    
    options = ["Регистрация", "Авторизация", "Моё Резюме", "Поиск Вакансий", "Анализ (Match)"]
    
    try:
        index = options.index(st.session_state['page'])
    except ValueError:
        index = 0
        
    st.radio("Перейти к:", options, index=index, key="menu_selection", on_change=navigate)

# --- СТРАНИЦА РЕГИСТРАЦИИ ---
if st.session_state['page'] == "Регистрация":
    st.header("Регистрация")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    
    if st.button("Зарегистрироваться"):
        try:
            response = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
            if response.status_code == 200:
                st.success("Успешно! Перенаправляем на вход...")
                time.sleep(1)
                st.session_state['page'] = "Авторизация"
                st.rerun()
            elif response.status_code == 422:
                st.error("Пароль слишком короткий или email некорректный!")
            else:
                st.error(f"Ошибка: {response.text}")
        except Exception as e:
            st.error(f"Ошибка соединения: {e}")

# --- СТРАНИЦА АВТОРИЗАЦИИ ---
elif st.session_state['page'] == "Авторизация":
    st.header("Вход")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    
    if st.button("Войти"):
        try:
            response = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
            if response.status_code == 200:
                st.success("Вход выполнен!")
                st.session_state['user_email'] = email
                time.sleep(1)
                st.session_state['page'] = "Моё Резюме" # Сразу перекинем на создание резюме
                st.rerun()
            else:
                st.error("Неверные данные")
        except Exception as e:
            st.error(f"Ошибка соединения: {e}")

# --- НОВАЯ СТРАНИЦА: МОЁ РЕЗЮМЕ ---
elif st.session_state['page'] == "Моё Резюме":
    st.header("Добавить / Обновить Резюме")
    
    if not st.session_state['user_email']:
        st.warning("Сначала войдите в систему!")
    else:
        st.info("Вставьте текст вашего резюме сюда. Мы сохраним его в базу.")
        resume_text = st.text_area("Текст резюме", height=200, placeholder="Я Python разработчик, знаю FastAPI, Docker...")
        
        if st.button("Сохранить резюме"):
            if len(resume_text) < 10:
                st.error("Напишите хоть что-нибудь (минимум 10 символов)!")
            else:
                try:
                    # запрос на Бэкенд
                    # Email передаем в (params), текст в теле (json)
                    response = requests.post(
                        f"{API_URL}/resume", 
                        params={"email": st.session_state['user_email']},
                        json={"content": resume_text}
                    )
                    
                    if response.status_code == 200:
                        st.success("Резюме успешно сохранено!")
                        st.caption("Теперь вы можете переходить к поиску вакансий и анализу.")
                    else:
                        st.error(f"Ошибка сервера: {response.text}")
                        
                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")

# --- СТРАНИЦА ПОИСКА ---
elif st.session_state['page'] == "Поиск Вакансий":
    st.header("Поиск работы")
    
    if not st.session_state['user_email']:
        st.warning("Пожалуйста, сначала авторизуйтесь!")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            keyword = st.text_input("Ключевое слово", "Python Junior")
        with col2:
            st.write("") 
            st.write("") 
            search_btn = st.button("Найти")
            
        if search_btn:
            with st.spinner("Сканируем HH.ru..."):
                try:
                    response = requests.get(f"{API_URL}/vacancies", params={"text": keyword})
                    if response.status_code == 200:
                        data = response.json()
                        st.metric("Найдено на HH", data.get("found_on_hh", 0))
                        st.metric("Сохранено новых", data.get("saved_new", 0))
                        st.success("Вакансии сохранены в базу данных!")
                    else:
                        st.error(f"Ошибка сервера: {response.text}")
                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")

# --- СТРАНИЦА АНАЛИЗА (MATCH) ---
elif st.session_state['page'] == "Анализ (Match)":
    st.header("AI Анализ совместимости")
    
    if not st.session_state['user_email']:
        st.warning("Нужен вход в систему")
    else:
        st.info("Выберите резюме из списка и введите ID вакансии")
        
        resume_options = []
        res_id = None
        
        try:
            # Запрашиваем список всех резюме
            res_response = requests.get(f"{API_URL}/all_resumes")
            if res_response.status_code == 200:
                resumes_list = res_response.json()
                if not resumes_list:
                    st.warning("В базе нет резюме. Сначала создайте его.")
                else:
                    # Формируем список для Selectbox
                    # словарь, Ключ = "Красивое название", Значение = ID
                    resume_map = {f"ID: {r['id']} | {r['content'][:40]}...": r['id'] for r in resumes_list}
                    
                    selected_label = st.selectbox("Выберите резюме", options=list(resume_map.keys()))
                    
                    # реальный ID из выбора
                    res_id = resume_map[selected_label]
            else:
                st.error("Не удалось загрузить список резюме")
        except Exception as e:
            st.error(f"Ошибка соединения (список резюме): {e}")

        c1, c2 = st.columns(2)
        with c1:
            # Показываем выбранный ID (просто для информации, заблокированный)
            if res_id:
                st.text_input("Выбран ID Резюме", value=res_id, disabled=True)
            else:
                st.text_input("ID Резюме", value="Не выбрано", disabled=True)
                
        with c2:
            vac_id = st.number_input("ID Вакансии", min_value=1, value=1)

        vacancy_ready = False
        
        # Проверка вакансии
        if vac_id:
            try:
                info_response = requests.get(f"{API_URL}/vacancies/{vac_id}")
                
                if info_response.status_code == 200:
                    vac_info = info_response.json()
                    st.write(f"Вакансия: **{vac_info['name']}**")
                    
                    if vac_info['has_description']:
                        vacancy_ready = True
                        st.success("Описание готово")
                    else:
                        st.warning("Нет описания")
                        if st.button("Скачать с HH"):
                            with st.spinner("Скачиваем..."):
                                requests.post(f"{API_URL}/vacancies/{vac_info['hh_id']}/fill")
                                st.rerun()
                elif info_response.status_code == 404:
                    st.error("Вакансия не найдена")
            except Exception as e:
                st.error(f"Ошибка: {e}")

        st.divider()

        # Кнопка запуска (с проверкой, что резюме выбрано)
        if vacancy_ready and res_id:
            if st.button("Запустить AI Анализ", type="primary"):
                status_box = st.status("Запуск анализа...", expanded=True)
                
                try:
                    payload = {"resume_id": res_id, "vacancy_id": vac_id}
                    response = requests.post(f"{API_URL}/match", json=payload)
                    
                    if response.status_code == 200:
                        task_id = response.json().get("task_id")
                        status_box.write(f"Задача ID: {task_id}")
                        status_box.write("⏳ Ожидание воркера...")
                        
                        #Polling (опрос сервера, готов ли результат)
                        while True:
                            time.sleep(2)
                            status_resp = requests.get(f"{API_URL}/tasks/{task_id}")
                            status_data = status_resp.json()
                            status = status_data["status"]
                            
                            if status == "SUCCESS":
                                status_box.update(label="Готово!", state="complete", expanded=False)
                                
                                # КРАСИВЫЙ ВЫВОД РЕЗУЛЬТАТА
                                st.divider()
                                st.subheader("Результат анализа:")
                                st.code(status_data["result"], language="text")
                                break
                            
                            elif status == "FAILURE":
                                status_box.update(label="Ошибка", state="error")
                                st.error(status_data['result'])
                                break
                    else:
                        st.error(f"Ошибка: {response.text}")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        elif not res_id:
            st.warning("Сначала выберите резюме из списка сверху!")