import json
import os
import re
import sqlite3
import time

from dataclasses import dataclass
from typing import Any, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna",
)

DB_PATH = os.getenv(
    "DB_PATH",
    "savvysense.db",
)


REGIONS = {
    "BY": {
        "name": "Беларусь",
        "currency": "BYN",
        "lang": "ru",
        "hints": "Беларусь, Ozon BY, Wildberries BY, 21vek, Kufar",
    },
    "RU": {
        "name": "Россия",
        "currency": "RUB",
        "lang": "ru",
        "hints": "Ozon, Wildberries, Яндекс Маркет, Мегамаркет, Avito",
    },
    "KZ": {
        "name": "Казахстан",
        "currency": "KZT",
        "lang": "ru",
        "hints": "Kaspi, Wildberries Kazakhstan, Ozon Kazakhstan, Technodom, Sulpak",
    },
    "UZ": {
        "name": "Узбекистан",
        "currency": "UZS",
        "lang": "ru",
        "hints": "Uzum, Asaxiy и местные магазины",
    },
    "KG": {
        "name": "Кыргызстан",
        "currency": "KGS",
        "lang": "ru",
        "hints": "местные магазины и маркетплейсы Кыргызстана",
    },
    "AM": {
        "name": "Армения",
        "currency": "AMD",
        "lang": "ru",
        "hints": "местные магазины и маркетплейсы Армении",
    },
    "AZ": {
        "name": "Азербайджан",
        "currency": "AZN",
        "lang": "ru",
        "hints": "местные магазины и маркетплейсы Азербайджана",
    },
    "TJ": {
        "name": "Таджикистан",
        "currency": "TJS",
        "lang": "ru",
        "hints": "местные магазины и маркетплейсы Таджикистана",
    },
    "MD": {
        "name": "Молдова",
        "currency": "MDL",
        "lang": "ru",
        "hints": "999.md и местные магазины Молдовы",
    },
}


@dataclass
class UserProfile:
    user_id: int
    region: str = "BY"
    currency: str = "BYN"
    preferences: dict[str, Any] | None = None


def db():
    con = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            region TEXT,
            currency TEXT,
            preferences TEXT
        )
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query TEXT,
            created_at REAL
        )
        """
    )

    con.commit()

    return con


def get_profile(
    user_id: int,
    language_code: Optional[str] = None,
):
    con = db()

    row = con.execute(
        """
        SELECT region, currency, preferences
        FROM users
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()

    if row:
        try:
            preferences = json.loads(
                row[2] or "{}"
            )
        except Exception:
            preferences = {}

        con.close()

        return UserProfile(
            user_id,
            row[0],
            row[1],
            preferences,
        )

    region = "BY"
    currency = REGIONS[region]["currency"]

    con.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, region, currency, preferences)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            region,
            currency,
            "{}",
        ),
    )

    con.commit()
    con.close()

    return UserProfile(
        user_id,
        region,
        currency,
        {},
    )


def set_region(
    user_id: int,
    region: str,
):
    region = region.upper()

    if region not in REGIONS:
        raise ValueError("unknown region")

    profile = get_profile(user_id)

    con = db()

    con.execute(
        """
        UPDATE users
        SET region=?, currency=?, preferences=?
        WHERE user_id=?
        """,
        (
            region,
            REGIONS[region]["currency"],
            json.dumps(
                profile.preferences or {},
                ensure_ascii=False,
            ),
            user_id,
        ),
    )

    con.commit()
    con.close()


def save_preference(
    user_id: int,
    key: str,
    value: Any,
):
    profile = get_profile(user_id)

    preferences = (
        profile.preferences or {}
    )

    preferences[key] = value

    con = db()

    con.execute(
        """
        UPDATE users
        SET preferences=?
        WHERE user_id=?
        """,
        (
            json.dumps(
                preferences,
                ensure_ascii=False,
            ),
            user_id,
        ),
    )

    con.commit()
    con.close()


def add_track(
    user_id: int,
    query: str,
):
    con = db()

    con.execute(
        """
        INSERT INTO tracks
        (user_id, query, created_at)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            query,
            time.time(),
        ),
    )

    con.commit()
    con.close()


def list_tracks(user_id: int):
    con = db()

    rows = con.execute(
        """
        SELECT query
        FROM tracks
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,),
    ).fetchall()

    con.close()

    return [
        row[0]
        for row in rows
    ]


def region_from_text(
    text: str,
    current: UserProfile,
):
    text = text.lower()

    markers = {
        "беларус": "BY",
        "бел. руб": "BY",
        "byn": "BY",

        "росси": "RU",
        "рубл": "RU",
        "rub": "RU",

        "казахстан": "KZ",
        "тенге": "KZ",
        "kzt": "KZ",

        "узбекистан": "UZ",
        "сум": "UZ",
        "uzs": "UZ",

        "киргиз": "KG",
        "кыргыз": "KG",
        "сом": "KG",
        "kgs": "KG",

        "армени": "AM",
        "драм": "AM",
        "amd": "AM",

        "азербайджан": "AZ",
        "манат": "AZ",
        "azn": "AZ",

        "таджикистан": "TJ",
        "сомони": "TJ",
        "tjs": "TJ",

        "молдова": "MD",
        "mdl": "MD",
    }

    for marker, code in markers.items():
        if marker in text:
            current.region = code
            current.currency = REGIONS[
                code
            ]["currency"]

            return current

    return current


def parse_json(text: str):
    text = text.strip()

    match = re.search(
        r"\{.*\}",
        text,
        re.S,
    )

    if not match:
        return {}

    try:
        return json.loads(
            match.group(0)
        )
    except Exception:
        return {}


def openai_client():
    if OpenAI is None:
        return None

    key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not key:
        return None

    return OpenAI(api_key=key)


def ask_ai(
    query: str,
    profile: UserProfile,
    mode: str = "shop",
):
    client = openai_client()

    if client is None:
        return (
            "❌ OPENAI_API_KEY не настроен.\n"
            "Добавь его в Railway Variables."
        )

    region = REGIONS[
        profile.region
    ]

    preferences = json.dumps(
        profile.preferences or {},
        ensure_ascii=False,
    )

    instructions = f"""
Ты — SAVVY SENSE.

Ты не обычный поисковик.
Ты AI Shopping Decision Engine.

Регион:
{region["name"]} ({profile.region})

Валюта:
{profile.currency}

Локальные источники:
{region["hints"]}

Память пользователя:
{preferences}

Главная задача:
помочь человеку принять лучшее решение о покупке.

ПРАВИЛА:

1. Понимай обычный человеческий язык.

2. Определи товар, модель, бренд,
бюджет, валюту, цвет, размер,
назначение и требования.

3. Учитывай регион пользователя.

4. Сначала ищи подходящие варианты
в его регионе.

5. Затем рассматривай другие страны СНГ.

6. Затем рассматривай мировой рынок,
если это выгодно или необходимо.

7. Не выдумывай:
цену, наличие, рейтинг,
продавца или доставку.

8. Отличай основной товар от:
чехлов, кабелей, зарядок,
запчастей и аксессуаров.

9. Не выбирай товар только потому,
что он дешевле.

10. Учитывай:
цену,
доставку,
качество,
продавца,
рейтинг,
соответствие запросу,
риск.

11. Если полная стоимость неизвестна,
честно напиши об этом.

12. Не выдавай предположение
за проверенный факт.

13. Покажи максимум 5 хороших вариантов.

14. Выбери один BEST CHOICE.

15. Рассчитай SAVVY SCORE от 0 до 100.
Это аналитическая оценка SAVVY,
а не официальный рейтинг товара.

16. Объясни пользователю,
почему выбран именно этот вариант.

17. Если есть риск —
обязательно предупреди.

18. Используй память пользователя,
но никогда не придумывай личные данные.

ФОРМАТ:

🧠 SAVVY

Коротко:
что понял.

🥇 BEST CHOICE

Название
Цена:
Доставка:
Итого:
Продавец:
SAVVY SCORE:
Риск:
Ссылка:

Другие хорошие варианты:

🥈 ...
🥉 ...

💡 Почему я выбрал BEST CHOICE

⚠️ Что проверить перед покупкой
"""

    if mode == "analyze":
        instructions += """
Дополнительно:
сделай BUY / WAIT вывод,
плюсы и минусы товара.
"""

    if mode == "cheaper":
        instructions += """
Главная цель:
найди более выгодные альтернативы
с сохранением ключевых характеристик.
"""

    if mode == "compare":
        instructions += """
Главная цель:
сравни варианты между собой
и выбери победителя.
"""

    prompt = f"""
Запрос пользователя:

{query}

Режим:
{mode}

Самостоятельно проведи поиск,
анализируй результаты и дай
практическую рекомендацию.
"""

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=instructions,
            tools=[
                {
                    "type": "web_search_preview"
                }
            ],
            input=prompt,
            store=False,
        )

        return (
            response.output_text
            or "Не удалось получить результат."
        ).strip()

    except Exception as e:
        print("AI ERROR:", e)

        return (
            "❌ SAVVY временно не смог "
            "выполнить поиск.\n\n"
            f"Техническая ошибка: {e}"
        )


def understand(
    query: str,
    profile: UserProfile,
):
    client = openai_client()

    if client is None:
        return {
            "search_query": query,
            "region": profile.region,
            "currency": profile.currency,
            "max_price": None,
        }

    region = REGIONS[
        profile.region
    ]

    prompt = f"""
Разбери shopping-запрос.

Регион:
{region["name"]}

Валюта региона:
{profile.currency}

Верни только JSON:

{{
"product": null,
"brand": null,
"model": null,
"category": null,
"color": null,
"size": null,
"max_price": null,
"min_price": null,
"currency": null,
"accessory_requested": false,
"search_query": "",
"priorities": [],
"confidence": 0.0
}}

КРИТИЧНО:

Число в названии модели
не является ценой.

Например:

"iPhone 15 до 800$"

означает:

model = "15"
max_price = 800
currency = "USD"

Не придумывай валюту.

Запрос:

{query}
"""

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=(
                "Ты parser shopping запросов. "
                "Возвращай только JSON."
            ),
            input=prompt,
            store=False,
        )

        return parse_json(
            response.output_text
        )

    except Exception as e:
        print(
            "INTENT ERROR:",
            e,
        )

        return {
            "search_query": query,
            "region": profile.region,
            "currency": profile.currency,
            "max_price": None,
        }


def ask_ai_image(
    image_url: str,
    user_text: str,
    profile: UserProfile,
):
    client = openai_client()

    if client is None:
        return (
            "❌ OPENAI_API_KEY не настроен."
        )

    region = REGIONS[
        profile.region
    ]

    preferences = json.dumps(
        profile.preferences or {},
        ensure_ascii=False,
    )

    instructions = f"""
Ты — SAVVY SENSE,
AI Shopping Assistant.

Регион:
{region["name"]}

Валюта:
{profile.currency}

Память:
{preferences}

Посмотри изображение.

Определи:
• что за товар
• бренд
• модель
• категорию
• цвет
• основные характеристики

Отделяй факты от предположений.

После этого используй web search,
чтобы найти актуальные варианты покупки.

Ищи:
1. регион пользователя
2. СНГ
3. мировой рынок

Дай:

🥇 BEST CHOICE

3–5 вариантов.

Для каждого:
цена,
доставка если известна,
продавец,
ссылка,
SAVVY SCORE,
риск.

Если на фото аксессуар,
не называй его основным товаром.
"""

    user_text = (
        user_text
        or
        "Найди такой товар и лучшие "
        "варианты покупки."
    )

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=instructions,
            tools=[
                {
                    "type": "web_search_preview"
                }
            ],
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_text,
                        },
                        {
                            "type": "input_image",
                            "image_url": image_url,
                        },
                    ],
                }
            ],
            store=False,
        )

        return (
            response.output_text
            or "Не удалось обработать изображение."
        ).strip()

    except Exception as e:
        print(
            "PHOTO AI ERROR:",
            e,
        )

        return (
            "❌ Не удалось обработать фото."
        )