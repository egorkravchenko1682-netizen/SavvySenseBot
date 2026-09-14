import json, os, re, sqlite3, time
from dataclasses import dataclass, asdict
from typing import Any, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.6-luna')
DB_PATH = os.getenv('DB_PATH', 'savvysense.db')

REGIONS = {
    'BY': {'name': 'Беларусь', 'currency': 'BYN', 'lang': 'ru', 'hints': 'ozon.by, wildberries.by, 21vek.by, kufar.by, local Belarus stores'},
    'RU': {'name': 'Россия', 'currency': 'RUB', 'lang': 'ru', 'hints': 'ozon.ru, wildberries.ru, yandex market, megamarket, avito, local Russian stores'},
    'KZ': {'name': 'Казахстан', 'currency': 'KZT', 'lang': 'ru', 'hints': 'kaspi.kz, wildberries.kz, ozon.kz, technodom.kz, sulpak.kz, local Kazakhstan stores'},
    'UZ': {'name': 'Узбекистан', 'currency': 'UZS', 'lang': 'ru', 'hints': 'uzum.uz, asaxiy.uz, local Uzbekistan stores'},
    'KG': {'name': 'Кыргызстан', 'currency': 'KGS', 'lang': 'ru', 'hints': 'local Kyrgyzstan stores and marketplaces'},
    'AM': {'name': 'Армения', 'currency': 'AMD', 'lang': 'ru', 'hints': 'local Armenian stores and marketplaces'},
    'AZ': {'name': 'Азербайджан', 'currency': 'AZN', 'lang': 'ru', 'hints': 'local Azerbaijan stores and marketplaces'},
    'TJ': {'name': 'Таджикистан', 'currency': 'TJS', 'lang': 'ru', 'hints': 'local Tajikistan stores and marketplaces'},
    'MD': {'name': 'Молдова', 'currency': 'MDL', 'lang': 'ru', 'hints': '999.md, local Moldova stores and marketplaces'},
}

CURRENCY_BY_SYMBOL = {
    '$': 'USD', '€': 'EUR', '₽': 'RUB', '₸': 'KZT', '₴': 'UAH', '£': 'GBP'
}

@dataclass
class UserProfile:
    user_id: int
    region: str = 'BY'
    currency: str = 'BYN'
    preferences: dict[str, Any] | None = None


def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, region TEXT, currency TEXT, preferences TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS tracks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, query TEXT, created_at REAL)')
    con.commit()
    return con


def get_profile(user_id: int, language_code: Optional[str] = None) -> UserProfile:
    con = db()
    row = con.execute('SELECT region,currency,preferences FROM users WHERE user_id=?', (user_id,)).fetchone()
    if row:
        prefs = json.loads(row[2] or '{}')
        return UserProfile(user_id, row[0], row[1], prefs)
    region = 'BY' if (language_code or '').lower().startswith('ru') else 'BY'
    currency = REGIONS[region]['currency']
    con.execute('INSERT OR IGNORE INTO users(user_id,region,currency,preferences) VALUES(?,?,?,?)', (user_id, region, currency, '{}'))
    con.commit(); con.close()
    return UserProfile(user_id, region, currency, {})


def set_region(user_id: int, region: str):
    region = region.upper()
    if region not in REGIONS:
        raise ValueError('unknown region')
    con = db(); con.execute('INSERT OR REPLACE INTO users(user_id,region,currency,preferences) VALUES(?,?,?,COALESCE((SELECT preferences FROM users WHERE user_id=?),\'{}\'))', (user_id, region, REGIONS[region]['currency'], user_id)); con.commit(); con.close()


def save_preference(user_id: int, key: str, value: Any):
    p = get_profile(user_id).preferences or {}
    p[key] = value
    con = db(); con.execute('UPDATE users SET preferences=? WHERE user_id=?', (json.dumps(p, ensure_ascii=False), user_id)); con.commit(); con.close()


def add_track(user_id: int, query: str):
    con = db(); con.execute('INSERT INTO tracks(user_id,query,created_at) VALUES(?,?,?)', (user_id, query, time.time())); con.commit(); con.close()


def list_tracks(user_id: int):
    con = db(); rows = con.execute('SELECT query FROM tracks WHERE user_id=? ORDER BY id DESC LIMIT 20', (user_id,)).fetchall(); con.close(); return [r[0] for r in rows]


def region_from_text(text: str, current: UserProfile) -> UserProfile:
    t = text.lower()
    markers = {
        'беларус': 'BY', 'бел. руб': 'BY', 'byn': 'BY',
        'росси': 'RU', 'рубл': 'RU', 'rub': 'RU',
        'казахстан': 'KZ', 'тенге': 'KZ', 'kzt': 'KZ',
        'узбекистан': 'UZ', 'сум': 'UZ', 'uzs': 'UZ',
        'киргиз': 'KG', 'кыргыз': 'KG', 'сом': 'KG', 'kgs': 'KG',
        'армени': 'AM', 'драм': 'AM', 'amd': 'AM',
        'азербайджан': 'AZ', 'манат': 'AZ', 'azn': 'AZ',
        'таджикистан': 'TJ', 'сомони': 'TJ', 'tjs': 'TJ',
        'молдова': 'MD', 'лей': 'MD', 'mdl': 'MD',
    }
    for marker, code in markers.items():
        if marker in t and code in REGIONS:
            current.region = code; current.currency = REGIONS[code]['currency']; return current
    return current


def parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return {}
    try: return json.loads(m.group(0))
    except Exception: return {}


def ask_ai(query: str, profile: UserProfile, mode: str = 'shop') -> str:
    if OpenAI is None or not os.getenv('OPENAI_API_KEY'):
        return 'OPENAI_API_KEY не настроен. Добавь ключ в Railway Variables.'
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    r = REGIONS[profile.region]
    prefs = json.dumps(profile.preferences or {}, ensure_ascii=False)
    system = f'''Ты — SAVVY SENSE, персональный AI shopping decision engine для СНГ.
Регион пользователя: {r['name']} ({profile.region}); валюта: {profile.currency}.
Локальные источники региона: {r['hints']}.
Память пользователя: {prefs}.
Твоя задача — не просто найти товар, а помочь принять решение.
Всегда:
1) понимай естественный русский язык, бюджет, модель, цвет, размер, назначение и приоритеты;
2) используй web search для актуальных предложений, если доступен;
3) ищи сначала в регионе пользователя, затем по всему СНГ, затем глобально;
4) не выдумывай цены, наличие, рейтинг, доставку или продавца; если не проверено — помечай как неизвестно;
5) отличай оригинальный товар от аксессуаров, запчастей и похожих моделей;
6) считай полную стоимость для региона, только если цена/доставка реально известны;
7) дай 3–5 лучших вариантов, а не длинный список;
8) выбери BEST CHOICE и объясни почему;
9) добавь SAVVY SCORE 0–100 как прозрачную оценку по соответствию запросу, цене, качеству, продавцу и доставке; не выдавай её за объективный рейтинг;
10) отдельно отметь риск, когда есть сомнения;
11) учитывай память пользователя, но не придумывай личные данные.
Формат ответа:
🧠 SAVVY
Коротко: что понял.
🥇 BEST CHOICE
2–4 альтернативы.
Для каждого: цена, доставка/итого если известно, продавец, ссылка, SAVVY SCORE, риск.
💡 Почему этот вариант.
⚠️ Что проверить перед покупкой.
'''
    if mode == 'analyze':
        system += '\nСделай также честный BUY / WAIT вывод и перечисли главные плюсы и минусы.'
    prompt = f'''Запрос пользователя: {query}\nРежим: {mode}\nПроведи поиск и анализ. Не спрашивай лишних уточнений: используй наиболее разумное предположение и явно укажи его, если оно важно.'''
    try:
        resp = client.responses.create(
            model=MODEL,
            instructions=system,
            tools=[{'type': 'web_search_preview'}],
            input=prompt,
            store=False,
        )
        return resp.output_text.strip()
    except Exception as e:
        return f'Не удалось выполнить AI-поиск: {e}'


def understand(query: str, profile: UserProfile) -> dict:
    if OpenAI is None or not os.getenv('OPENAI_API_KEY'):
        return {'search_query': query, 'region': profile.region, 'currency': profile.currency}
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    r = REGIONS[profile.region]
    prompt = f'''Разбери запрос для shopping engine. Регион по умолчанию: {r["name"]}; валюта: {profile.currency}.
Верни JSON без markdown с полями: product, brand, model, category, color, size, max_price, min_price, currency, accessory_requested, search_query, priorities, confidence.
КРИТИЧНО: числа внутри названий моделей не являются ценой. Например "iPhone 15 до 800$" => model="15", min_price=null, max_price=800, currency="USD".
Не угадывай валюту для двусмысленного "р": используй валюту региона по умолчанию.
Запрос: {query}'''
    try:
        resp = client.responses.create(model=MODEL, instructions='Ты parser shopping запросов. Возвращай только JSON.', input=prompt, store=False)
        return parse_json(resp.output_text)
    except Exception:
        return {'search_query': query, 'region': profile.region, 'currency': profile.currency}


def ask_ai_image(image_url: str, user_text: str, profile: UserProfile) -> str:
    if OpenAI is None or not os.getenv('OPENAI_API_KEY'):
        return 'OPENAI_API_KEY не настроен. Добавь ключ в Railway Variables.'
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    r = REGIONS[profile.region]
    prefs = json.dumps(profile.preferences or {}, ensure_ascii=False)
    instructions = f"""Ты — SAVVY SENSE, AI shopping assistant.
Регион: {r['name']} ({profile.region}); валюта: {profile.currency}.
Память: {prefs}.
Посмотри изображение, определи товар, бренд/модель если возможно, ключевые характеристики и затем найди актуальные предложения через web search.
Ищи сначала в регионе пользователя, потом по СНГ, потом глобально.
Не выдумывай. Чётко отделяй распознанное от предположений.
Дай 3–5 вариантов, BEST CHOICE, цену/доставку если проверены, ссылку, SAVVY SCORE 0–100 и риск.
Если на фото аксессуар — прямо скажи, что это аксессуар, а не основной товар."""
    text = user_text or 'Найди такой товар и лучшие варианты покупки.'
    try:
        resp = client.responses.create(
            model=MODEL,
            instructions=instructions,
            tools=[{'type': 'web_search_preview'}],
            input=[{'role': 'user', 'content': [
                {'type': 'input_text', 'text': text},
                {'type': 'input_image', 'image_url': image_url},
            ]}],
            store=False,
        )
        return resp.output_text.strip()
    except Exception as e:
        return f'Не удалось обработать фото: {e}'