import httpx
import asyncio
import re

async def get_vacancies(keyword):
    params = {
        "text": keyword,
        "area": [1002, 1003], # Минск и Гродно
        "per_page": 10 
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.hh.ru/vacancies', params=params)
        
        if response.status_code !=200:
            print("Ошибка получения данных:", response.status_code)
            return []
        
        return response.json()['items']
    
    
def clean_html(raw_html):
    """Удаляет теги типа <p>, <br> из текста"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


async def get_vacancy_full_text(vacancy_id: str):
    """
    Получает полное описание вакансии по её ID.
    """
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        description_html = data.get("description", "")
        return clean_html(description_html)
    
    
if __name__ == "__main__":
    found_jobs = asyncio.run(get_vacancies("Python Junior"))
    
    for job in found_jobs:
        salary = job.get('salary')
        print(f"Вакансия: {job['name']} | ЗП: {salary}")
        
        
