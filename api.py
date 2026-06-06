import httpx
from typing import List
import re
from bs4 import BeautifulSoup
MAX_SYNONYMS = 20

async def fetch_synonyms_english(word: str) -> List[str]:
    """Получает синонимы для английских слов через Datamuse API."""
    url = "https://api.datamuse.com/words"
    params = {"ml": word, "max": str(MAX_SYNONYMS)}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return [item["word"] for item in data]
    except Exception as e:
        print(f"Datamuse error: {e}")
        raise ConnectionError(f"Ошибка API: {e}")


async def fetch_synonyms_russian(word: str) -> List[str]:
    """
    Получает синонимы для русских слов через synonymonline.ru.
    """
    first_letter = word[0].upper()
    url = f"https://synonymonline.ru/{first_letter}/{word}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Проверяем на 404
            if "404: страница не найдена" in html.lower():
                raise ConnectionError(f"Слово '{word}' не найдено")
            
            synonyms = []
            soup = BeautifulSoup(html, 'html.parser')
            
            # ВАРИАНТ 1: Ищем в meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                content = meta_desc['content']
                # Извлекаем слова после "синонимов к слову"
                match = re.search(r'синонимов к слову [«"]\w+[»"]:\s*(.+?)(?:\s+и другие|$)', content)
                if match:
                    synonyms_text = match.group(1)
                    found = [s.strip().lower() for s in synonyms_text.split(',')]
                    synonyms.extend([s for s in found if s and s != word.lower()])
            
            # ВАРИАНТ 2: Ищем в основном контенте страницы
            if len(synonyms) < 3:
                # Ищем все ссылки с синонимами
                links = soup.find_all('a', href=re.compile(r'/synonym/|/\w+/'))
                for link in links:
                    text = link.get_text().strip().lower()
                    if (text and 
                        re.match(r'^[а-яё\-]+$', text) and
                        len(text) > 1 and 
                        text != word.lower() and
                        text not in synonyms):
                        synonyms.append(text)
            
            # ВАРИАНТ 3: Ищем в списках и абзацах
            if len(synonyms) < 3:
                # Ищем текст в тегах <p>, <li>, <span>
                for tag in ['p', 'li', 'span']:
                    elements = soup.find_all(tag)
                    for elem in elements:
                        text = elem.get_text().strip()
                        # Ищем слова через запятую
                        words = re.findall(r'[а-яё\-]+', text.lower())
                        for w in words:
                            if (len(w) > 2 and 
                                w != word.lower() and 
                                w not in synonyms and
                                w not in ['синонимы', 'слова', 'другие', 'примеры']):
                                synonyms.append(w)
            
            # Фильтруем и возвращаем
            synonyms = [s for s in synonyms if len(s) > 1][:MAX_SYNONYMS]
            
            print(f"✅ Найдено синонимов: {len(synonyms)}")
            if synonyms:
                print(f"   Примеры: {', '.join(synonyms[:5])}")
            
            return synonyms[:MAX_SYNONYMS]
            
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        raise ConnectionError(f"Ошибка доступа к сайту ({e.response.status_code})")
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
        raise ConnectionError(f"Не удалось подключиться: {e}")
    except Exception as e:
        print(f"Parse Error: {e}")
        raise RuntimeError(f"Ошибка обработки: {e}")


def detect_language(word: str) -> str:
    """Определяет язык слова."""
    if re.search(r'[а-яА-ЯёЁ]', word):
        return 'ru'
    elif re.search(r'[a-zA-Z]', word):
        return 'en'
    return 'unknown'


async def fetch_synonyms(word: str) -> List[str]:
    """Основная функция."""
    word = word.strip().lower()
    if not word:
        raise ValueError("Слово не может быть пустым")
    
    lang = detect_language(word)
    
    if lang == 'ru':
        print(f"🇷🇺 Русский: '{word}'")
        return await fetch_synonyms_russian(word)
    elif lang == 'en':
        print(f"🇬🇧 English: '{word}'")
        return await fetch_synonyms_english(word)
    else:
        raise ValueError("Неизвестный язык")