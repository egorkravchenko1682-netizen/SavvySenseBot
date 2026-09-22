import re
import sqlite3
from typing import Optional


DB_NAME = "savvy.db"


REGIONS = {
    "BY": "Беларусь",
    "RU": "Россия",
    "KZ": "Казахстан",
    "UZ": "Узбекистан",
    "KG": "Кыргызстан",
    "AM": "Армения",
    "AZ": "Азербайджан",
    "TJ": "Таджикистан",
    "MD": "Молдова",
}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            region TEXT DEFAULT 'BY',
            currency TEXT DEFAULT 'USD'
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INTEGER,
            key TEXT,
            value TEXT,
            UNIQUE(user_id, key)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            target_price REAL,
            currency TEXT,
            active INTEGER DEFAULT 1
        )
        """
    )

    conn.commit()
    conn.close()


def ensure_user(user_id: int):
    conn = get_db()

    conn.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, region, currency)
        VALUES (?, 'BY', 'USD')
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


def get_user(user_id: int):
    ensure_user(user_id)

    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    return row


def set_region(user_id: int, region: str):
    region = region.upper()

    if region not in REGIONS:
        raise ValueError("Unsupported region")

    ensure_user(user_id)

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET region = ?
        WHERE user_id = ?
        """,
        (region, user_id),
    )

    conn.commit()
    conn.close()


def get_region(user_id: int) -> str:
    row = get_user(user_id)
    return row["region"]


def remember(user_id: int, key: str, value: str):
    ensure_user(user_id)

    conn = get_db()

    conn.execute(
        """
        INSERT INTO preferences
        (user_id, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, key)
        DO UPDATE SET value = excluded.value
        """,
        (user_id, key, value),
    )

    conn.commit()
    conn.close()


def get_preferences(user_id: int):
    ensure_user(user_id)

    conn = get_db()

    rows = conn.execute(
        """
        SELECT key, value
        FROM preferences
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()

    conn.close()

    return {row["key"]: row["value"] for row in rows}


def add_tracking(
    user_id: int,
    product: str,
    target_price: Optional[float] = None,
    currency: str = "USD",
):
    ensure_user(user_id)

    conn = get_db()

    conn.execute(
        """
        INSERT INTO tracking
        (user_id, product, target_price, currency)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            product,
            target_price,
            currency,
        ),
    )

    conn.commit()
    conn.close()


def get_tracking(user_id: int):
    ensure_user(user_id)

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM tracking
        WHERE user_id = ?
        AND active = 1
        ORDER BY id DESC
        """,
        (user_id,),
    ).fetchall()

    conn.close()

    return rows


def region_from_text(text: str) -> Optional[str]:
    if not text:
        return None

    text = text.lower()

    aliases = {
        "беларусь": "BY",
        "белоруссия": "BY",
        "belarus": "BY",

        "россия": "RU",
        "российская федерация": "RU",
        "russia": "RU",

        "казахстан": "KZ",
        "kazakhstan": "KZ",

        "узбекистан": "UZ",
        "uzbekistan": "UZ",

        "кыргызстан": "KG",
        "киргизия": "KG",
        "kyrgyzstan": "KG",

        "армения": "AM",
        "armenia": "AM",

        "азербайджан": "AZ",
        "azerbaijan": "AZ",

        "таджикистан": "TJ",
        "tajikistan": "TJ",

        "молдова": "MD",
        "moldova": "MD",
    }

    for name, code in aliases.items():
        if name in text:
            return code

    return None


def understand(text: str):
    """
    Базовое понимание запроса SAVVY.

    Пока без OpenAI.
    Позже сюда можно подключить отдельный AI-слой,
    не ломая ядро.
    """

    if not text:
        return {
            "intent": "unknown",
            "query": "",
        }

    original = text.strip()
    lowered = original.lower()

    if lowered.startswith("/find"):
        intent = "product_search"

    elif lowered.startswith("/compare"):
        intent = "compare"

    elif lowered.startswith("/check"):
        intent = "check"

    elif lowered.startswith("/cheaper"):
        intent = "cheaper"

    elif lowered.startswith("/track"):
        intent = "track"

    elif lowered.startswith("/help"):
        intent = "help"

    else:
        if any(
            word in lowered
            for word in [
                "сравни",
                "сравнить",
                "compare",
            ]
        ):
            intent = "compare"

        elif any(
            word in lowered
            for word in [
                "дешевле",
                "дешевый",
                "найди дешевле",
                "cheaper",
            ]
        ):
            intent = "cheaper"

        elif any(
            word in lowered
            for word in [
                "стоит ли",
                "выгодно ли",
                "покупать",
                "worth",
            ]
        ):
            intent = "check"

        elif any(
            word in lowered
            for word in [
                "следи",
                "отслеживай",
                "отследи",
                "track",
            ]
        ):
            intent = "track"

        else:
            intent = "product_search"

    query = original

    commands = [
        "/find",
        "/compare",
        "/check",
        "/cheaper",
        "/track",
    ]

    for command in commands:
        if lowered.startswith(command):
            query = original[len(command):].strip()
            break

    budget = extract_budget(original)

    region = region_from_text(original)

    return {
        "intent": intent,
        "query": query,
        "budget": budget,
        "region": region,
    }


def extract_budget(text: str):
    if not text:
        return None

    patterns = [
        r"до\s*\$?\s*(\d+(?:[.,]\d+)?)",
        r"до\s*(\d+(?:[.,]\d+)?)\s*\$",
        r"\$\s*(\d+(?:[.,]\d+)?)",
        r"(\d+(?:[.,]\d+)?)\s*\$",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text.lower(),
        )

        if match:
            try:
                return float(
                    match.group(1).replace(",", ".")
                )
            except ValueError:
                pass

    return None


def build_context(user_id: int):
    user = get_user(user_id)

    return {
        "user_id": user_id,
        "region": user["region"],
        "currency": user["currency"],
        "preferences": get_preferences(user_id),
        "tracking": [
            dict(row)
            for row in get_tracking(user_id)
        ],
    }


init_db()