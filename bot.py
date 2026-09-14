import os
import re
import json
import time
import base64
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup
import telebot

from savvy_brain import understand

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# ============================================================
# SAVVY SENSE — single-file production MVP
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_MARKETPLACE_ID = os.getenv(
    "EBAY_MARKETPLACE_ID",
    "EBAY_US"
)

DEFAULT_CURRENCY = os.getenv(
    "DEFAULT_CURRENCY",
    "EUR"
).upper()

DEFAULT_COUNTRY = os.getenv(
    "DEFAULT_COUNTRY",
    "BY"
).upper()

DB_PATH = os.getenv(
    "DB_PATH",
    "savvysense.db"
)

HTTP_TIMEOUT = int(
    os.getenv("HTTP_TIMEOUT", "15")
)

MAX_RESULTS = int(
    os.getenv("MAX_RESULTS", "12")
)

SEARCH_TIMEOUT = int(
    os.getenv("SEARCH_TIMEOUT", "30")
)

TRACK_INTERVAL_SECONDS = int(
    os.getenv(
        "TRACK_INTERVAL_SECONDS",
        "900"
    )
)


CURRENCY_SYMBOLS = {
    "BYN": "Br",
    "RUB": "₽",
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "PLN": "zł",
    "KZT": "₸",
    "UAH": "₴",
    "CNY": "¥",
}


CURRENCY_ALIASES = {
    "€": "EUR",
    "евро": "EUR",
    "eur": "EUR",

    "$": "USD",
    "доллар": "USD",
    "доллары": "USD",
    "usd": "USD",

    "£": "GBP",
    "фунт": "GBP",
    "gbp": "GBP",

    "₽": "RUB",
    "руб": "RUB",
    "рубль": "RUB",
    "рубли": "RUB",
    "rub": "RUB",

    "br": "BYN",
    "byn": "BYN",
    "бел": "BYN",
    "белорус": "BYN",
    "белорусских": "BYN",

    "zł": "PLN",
    "pln": "PLN",
    "злот": "PLN",

    "₸": "KZT",
    "kzt": "KZT",
    "тенге": "KZT",

    "₴": "UAH",
    "uah": "UAH",
    "грив": "UAH",

    "¥": "CNY",
    "cny": "CNY",
    "юан": "CNY",
}


# Приблизительные курсы относительно EUR.
# Это НЕ live-курсы.
DEFAULT_FX_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.85,
    "GBP": 1.17,
    "PLN": 0.234,
    "RUB": 0.0093,
    "BYN": 0.29,
    "KZT": 0.00185,
    "UAH": 0.0205,
    "CNY": 0.123,
}


URL_RE = re.compile(
    r"https?://[^\s]+"
)


@dataclass
class Product:

    name: str
    shop: str
    url: str

    price: Optional[float] = None
    currency: Optional[str] = None

    old_price: Optional[float] = None

    brand: Optional[str] = None

    rating: Optional[float] = None
    reviews: Optional[int] = None

    image_url: Optional[str] = None

    delivery_price: Optional[float] = None
    delivery_currency: Optional[str] = None

    seller: Optional[str] = None

    seller_rating_percent: Optional[float] = None
    seller_feedback_count: Optional[int] = None

    product_id: Optional[str] = None

    is_exact_match: bool = False

    condition: Optional[str] = None

    source_text: Optional[str] = None


    def normalized_price_eur(
        self
    ) -> Optional[float]:

        if (
            self.price is None
            or not self.currency
        ):
            return None

        rate = DEFAULT_FX_TO_EUR.get(
            self.currency.upper()
        )

        return (
            self.price * rate
            if rate
            else None
        )


    def delivery_eur(
        self
    ) -> Optional[float]:

        if (
            self.delivery_price is None
            or not self.delivery_currency
        ):
            return None

        rate = DEFAULT_FX_TO_EUR.get(
            self.delivery_currency.upper()
        )

        return (
            self.delivery_price * rate
            if rate
            else None
        )


    def total_eur(
        self
    ) -> Optional[float]:

        price = self.normalized_price_eur()

        if price is None:
            return None

        delivery = self.delivery_eur()

        if delivery is None:
            return price

        return price + delivery


def fmt_money(
    value: Optional[float],
    currency: Optional[str]
) -> str:

    if (
        value is None
        or not currency
    ):
        return "Цена не указана"

    symbol = CURRENCY_SYMBOLS.get(
        currency.upper(),
        currency.upper()
    )

    if abs(value - round(value)) < 0.005:
        return (
            f"{symbol}{value:,.0f}"
            .replace(",", " ")
        )

    return (
        f"{symbol}{value:,.2f}"
        .replace(",", " ")
    )


def detect_currency(
    text: str
) -> str:

    if not text:
        return DEFAULT_CURRENCY

    low = text.lower()

    for token, currency in sorted(
        CURRENCY_ALIASES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        if token in low:
            return currency

    return DEFAULT_CURRENCY
def normalize_aliases(text: str) -> str:
    """
    Приводит распространённые русские названия
    товаров и брендов к форме, которую лучше
    понимают международные поисковые системы.
    """

    if not text:
        return text

    replacements = {
        "айфон": "iPhone",
        "iphone": "iPhone",

        "эпл": "Apple",
        "аппл": "Apple",
        "apple": "Apple",

        "самсунг": "Samsung",
        "самсун": "Samsung",
        "samsung": "Samsung",

        "сяоми": "Xiaomi",
        "ксяоми": "Xiaomi",
        "xiaomi": "Xiaomi",

        "хуавей": "Huawei",
        "huawei": "Huawei",

        "хонор": "Honor",
        "honor": "Honor",

        "пиксель": "Pixel",
        "google pixel": "Google Pixel",

        "плейстейшен": "PlayStation",
        "пс5": "PS5",
        "пс 5": "PS5",
        "ps5": "PS5",

        "иксбокс": "Xbox",
        "xbox": "Xbox",

        "макбук": "MacBook",
        "макбук эир": "MacBook Air",
        "макбук про": "MacBook Pro",

        "айпад": "iPad",

        "эйрподс": "AirPods",
        "аирподс": "AirPods",

        "нинтендо": "Nintendo",
        "свитч": "Switch",

        "ноут": "laptop",
        "ноутбук": "laptop",

        "смартфон": "smartphone",
        "телефон": "smartphone",

        "телевизор": "TV",
        "телевизоры": "TV",

        "наушники": "headphones",

        "кроссовки": "sneakers",

        "часы": "smartwatch",
        "смарт часы": "smartwatch",

        "планшет": "tablet",
    }

    result = text

    for old, new in sorted(
        replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):
        result = re.sub(
            rf"(?<!\w){re.escape(old)}(?!\w)",
            new,
            result,
            flags=re.IGNORECASE
        )

    return result


def parse_budget(
    text: str
):
    """
    Возвращает:
        cleaned_text,
        max_price,
        currency
    """

    if not text:
        return (
            "",
            None,
            DEFAULT_CURRENCY
        )

    currency = detect_currency(text)

    patterns = [

        # до $500
        r"(?:до|максимум|не\s+дороже|не\s+более)"
        r"\s*\$?\s*"
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(\$|usd|доллар(?:ов|а)?|долл\.?)?",

        # $500
        r"\$\s*(\d+(?:[.,]\d+)?)",

        # 500 евро
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(евро|eur|€)",

        # 500 рублей
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(руб(?:лей|ля)?|руб\.?|₽|rub)",

        # 500 BYN
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(byn|br|бел\.?\s*руб(?:лей|ля)?)",

        # 500 тенге
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(тенге|kzt|₸)",

        # 500 гривен
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(грив(?:ен|ны)?|uah|₴)",

        # 500 злотых
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(злот(?:ых|ый)?|pln|zł)",

        # 500 юаней
        r"(\d+(?:[.,]\d+)?)"
        r"\s*(юан(?:ей|я)?|cny|¥)",
    ]

    max_price = None

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if not match:
            continue

        try:
            value = float(
                match.group(1)
                .replace(",", ".")
            )
        except (
            ValueError,
            AttributeError
        ):
            continue

        max_price = value

        groups = match.groups()

        if len(groups) >= 2:
            token = groups[1]

            if token:
                token_low = token.lower()

                for alias, code in (
                    CURRENCY_ALIASES.items()
                ):
                    if alias.lower() in token_low:
                        currency = code
                        break

        break

    cleaned = text

    if max_price is not None:

        cleaned = re.sub(
            patterns[0],
            " ",
            cleaned,
            flags=re.IGNORECASE
        )

        for pattern in patterns[1:]:
            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE
            )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip()

    return (
        cleaned,
        max_price,
        currency
    )


def clean_query(text: str) -> str:

    if not text:
        return ""

    query = text.strip()

    query, _, _ = parse_budget(
        query
    )

    # Убираем типичные разговорные конструкции.
    filler_patterns = [
        r"^(найди|найти|поищи|ищи|подбери|подберите)\s+",
        r"^(хочу|мне нужен|мне нужна|мне нужны)\s+",
        r"^(нужен|нужна|нужны)\s+",
        r"^(покажи|покажите)\s+",
        r"^(можешь найти|можете найти)\s+",
        r"^(посоветуй|посоветуйте)\s+",
    ]

    for pattern in filler_patterns:
        query = re.sub(
            pattern,
            "",
            query,
            flags=re.IGNORECASE
        )

    query = normalize_aliases(
        query
    )

    query = re.sub(
        r"\s+",
        " ",
        query
    ).strip()

    return query


def extract_url(text: str) -> Optional[str]:

    if not text:
        return None

    match = URL_RE.search(text)

    if not match:
        return None

    url = match.group(0).rstrip(
        ".,!?;:)"
    )

    return url


def detect_shop(url: str) -> Optional[str]:

    if not url:
        return None

    try:
        hostname = urlparse(
            url
        ).netloc.lower()

    except Exception:
        return None

    hostname = hostname.replace(
        "www.",
        ""
    )

    shops = {
        "wildberries": [
            "wildberries.ru",
            "wildberries.by",
        ],

        "ozon": [
            "ozon.ru",
            "ozon.by",
        ],

        "amazon": [
            "amazon.com",
            "amazon.de",
            "amazon.fr",
            "amazon.co.uk",
            "amazon.it",
            "amazon.es",
        ],

        "ebay": [
            "ebay.com",
            "ebay.de",
            "ebay.fr",
            "ebay.co.uk",
            "ebay.pl",
        ],

        "aliexpress": [
            "aliexpress.com",
            "aliexpress.ru",
        ],

        "temu": [
            "temu.com",
        ],

        "walmart": [
            "walmart.com",
        ],

        "etsy": [
            "etsy.com",
        ],

        "shein": [
            "shein.com",
        ],

        "taobao": [
            "taobao.com",
        ],

        "tmall": [
            "tmall.com",
        ],

        "1688": [
            "1688.com",
        ],

        "jd": [
            "jd.com",
        ],

        "pinduoduo": [
            "pinduoduo.com",
        ],

        "alibaba": [
            "alibaba.com",
        ],

        "kaspi": [
            "kaspi.kz",
        ],

        "rozetka": [
            "rozetka.com.ua",
        ],
    }

    for shop, domains in shops.items():

        for domain in domains:

            if (
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
            ):
                return shop

    return None


def extract_wildberries_id(
    url: str
) -> Optional[str]:

    patterns = [
        r"/catalog/(\d+)/detail",
        r"/catalog/(\d+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url
        )

        if match:
            return match.group(1)

    return None


def safe_float(
    value
) -> Optional[float]:

    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return None


def safe_int(
    value
) -> Optional[int]:

    if value is None:
        return None

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return None
def format_product(
    product: Product,
    index: int
) -> str:

    lines = []

    if product.is_exact_match:
        lines.append(
            "🎯 ТОЧНОЕ СОВПАДЕНИЕ"
        )

    lines.append(
        f"{index}. {product.name}"
    )

    lines.append(
        f"🏪 {product.shop.upper()}"
    )

    if product.price is not None:

        price_text = fmt_money(
            product.price,
            product.currency
        )

        lines.append(
            f"💰 Цена: {price_text}"
        )

    else:

        lines.append(
            "💰 Цена: не указана"
        )

    total = product.total_eur()

    if (
        total is not None
        and product.delivery_price is not None
    ):

        lines.append(
            f"🚚 Доставка: "
            f"{fmt_money(product.delivery_price, product.delivery_currency)}"
        )

        lines.append(
            f"💳 Итого примерно: "
            f"{total:.2f} €"
        )

    if product.rating is not None:

        lines.append(
            f"⭐ Рейтинг: "
            f"{product.rating:.1f}"
        )

    if product.reviews is not None:

        lines.append(
            f"💬 Отзывов: "
            f"{product.reviews:,}"
            .replace(",", " ")
        )

    if product.seller:

        lines.append(
            f"👤 Продавец: "
            f"{product.seller}"
        )

    if (
        product.seller_rating_percent
        is not None
    ):

        lines.append(
            f"🏆 Рейтинг продавца: "
            f"{product.seller_rating_percent:.1f}%"
        )

    if (
        product.seller_feedback_count
        is not None
    ):

        lines.append(
            f"📊 Отзывов продавца: "
            f"{product.seller_feedback_count:,}"
            .replace(",", " ")
        )

    score = calculate_deal_score(
        product
    )

    lines.append(
        f"🧠 SAVVY SCORE: {score}/100"
    )

    if product.url:

        lines.append(
            f"🔗 {product.url}"
        )

    return "\n".join(lines)


def calculate_deal_score(
    product: Product
) -> int:

    score = 45

    if product.price is not None:
        score += 15

    if product.rating is not None:

        if product.rating >= 4.8:
            score += 15

        elif product.rating >= 4.5:
            score += 10

        elif product.rating >= 4.0:
            score += 5

    if product.reviews is not None:

        if product.reviews >= 1000:
            score += 10

        elif product.reviews >= 100:
            score += 5

    if (
        product.seller_rating_percent
        is not None
    ):

        if product.seller_rating_percent >= 99:
            score += 5

        elif product.seller_rating_percent >= 97:
            score += 3

    if product.is_exact_match:
        score += 10

    return max(
        0,
        min(score, 100)
    )


def deal_label(
    score: int
) -> str:

    if score >= 90:
        return "🔥 ОЧЕНЬ ВЫГОДНО"

    if score >= 75:
        return "🟢 ВЫГОДНО"

    if score >= 60:
        return "🟡 НОРМАЛЬНО"

    return "🔴 СОМНИТЕЛЬНО"


def product_matches_budget(
    product: Product,
    max_price: Optional[float],
    currency: Optional[str]
) -> bool:

    if max_price is None:
        return True

    if product.price is None:
        return False

    if not product.currency:
        return False

    source_rate = DEFAULT_FX_TO_EUR.get(
        product.currency.upper()
    )

    budget_rate = DEFAULT_FX_TO_EUR.get(
        currency.upper()
    )

    if (
        source_rate is None
        or budget_rate is None
    ):
        return False

    product_eur = (
        product.price
        * source_rate
    )

    budget_eur = (
        max_price
        * budget_rate
    )

    return product_eur <= budget_eur


def product_matches_text(
    product: Product,
    query: str
) -> bool:

    if not query:
        return True

    haystack = " ".join(
        [
            product.name or "",
            product.brand or "",
            product.source_text or "",
        ]
    ).lower()

    tokens = re.findall(
        r"[a-zа-яё0-9]+",
        query.lower()
    )

    important_tokens = [
        token
        for token in tokens
        if len(token) >= 2
    ]

    if not important_tokens:
        return True

    matches = 0

    for token in important_tokens:

        if token in haystack:
            matches += 1

    # Для коротких запросов требуем
    # наличие всех важных слов.
    if len(important_tokens) <= 2:
        return matches == len(
            important_tokens
        )

    # Для длинного естественного запроса
    # допускаем небольшие расхождения.
    required = max(
        2,
        int(
            len(important_tokens)
            * 0.5
        )
    )

    return matches >= required


def remove_duplicates(
    products: List[Product]
) -> List[Product]:

    result = []

    seen = set()

    for product in products:

        key = (
            product.shop.lower(),
            product.url.lower()
            if product.url
            else product.name.lower()
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(product)

    return result


def rank_products(
    products: List[Product]
) -> List[Product]:

    def sort_key(
        product: Product
    ):

        score = calculate_deal_score(
            product
        )

        price = (
            product.normalized_price_eur()
        )

        if price is None:
            price_sort = 999999999
        else:
            price_sort = price

        exact = (
            1
            if product.is_exact_match
            else 0
        )

        return (
            -exact,
            -score,
            price_sort
        )

    return sorted(
        products,
        key=sort_key
    )


def make_search_header(
    query: str,
    max_price: Optional[float],
    currency: str
) -> str:

    header = (
        "🌎 <b>SAVVY SENSE</b>\n\n"
        f"🔎 Ищу: <b>{query}</b>\n"
    )

    if max_price is not None:

        header += (
            f"💰 Бюджет: "
            f"<b>{fmt_money(max_price, currency)}</b>\n"
        )

    header += (
        "\n⏳ Проверяю доступные источники..."
    )

    return header


def make_no_results_message(
    query: str,
    max_price: Optional[float],
    currency: str
) -> str:

    text = (
        "😔 <b>Подходящих предложений "
        "не найдено.</b>\n\n"
        f"🔎 Запрос: <b>{query}</b>\n"
    )

    if max_price is not None:

        text += (
            f"💰 Бюджет: "
            f"<b>{fmt_money(max_price, currency)}</b>\n"
        )

    text += (
        "\nПопробуй:\n"
        "• убрать ограничение по цене;\n"
        "• написать модель точнее;\n"
        "• использовать английское название;\n"
        "• отправить ссылку на товар."
    )

    return text


def make_results_message(
    query: str,
    products: List[Product],
    max_price: Optional[float],
    currency: str
) -> str:

    lines = [
        "🌎 <b>SAVVY SENSE</b>",
        "",
        f"🔎 <b>{query}</b>",
        ""
    ]

    if max_price is not None:

        lines.append(
            f"💰 До "
            f"<b>{fmt_money(max_price, currency)}</b>"
        )

        lines.append("")

    lines.append(
        f"✅ Найдено предложений: "
        f"<b>{len(products)}</b>"
    )

    lines.append("")

    for index, product in enumerate(
        products[:MAX_RESULTS],
        start=1
    ):

        lines.append(
            format_product(
                product,
                index
            )
        )

        lines.append(
            "\n──────────────\n"
        )

    return "\n".join(lines)
def extract_product_from_html(
    url: str
) -> Optional[Product]:

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(iPhone; CPU iPhone OS 18_0 "
                    "like Mac OS X) "
                    "AppleWebKit/605.1.15 "
                    "Version/18.0 Mobile/15E148 "
                    "Safari/604.1"
                )
            },
            timeout=HTTP_TIMEOUT
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "Product page error:",
            e
        )

        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    shop = detect_shop(url)

    if not shop:
        shop = (
            urlparse(url)
            .netloc
            .replace("www.", "")
        )

    title = None

    meta = soup.find(
        "meta",
        attrs={
            "property": "og:title"
        }
    )

    if meta:
        title = meta.get(
            "content"
        )

    if not title:

        meta = soup.find(
            "meta",
            attrs={
                "name": "twitter:title"
            }
        )

        if meta:
            title = meta.get(
                "content"
            )

    if not title and soup.title:
        title = soup.title.get_text(
            " ",
            strip=True
        )

    if not title:
        title = "Товар по ссылке"

    image_url = None

    meta_image = soup.find(
        "meta",
        attrs={
            "property": "og:image"
        }
    )

    if meta_image:
        image_url = meta_image.get(
            "content"
        )

    price = None
    currency = None

    # JSON-LD Product
    scripts = soup.find_all(
        "script",
        attrs={
            "type": "application/ld+json"
        }
    )

    for script in scripts:

        raw = script.string

        if not raw:
            continue

        try:
            data = json.loads(raw)

        except Exception:
            continue

        objects = []

        if isinstance(data, dict):
            objects.append(data)

            graph = data.get(
                "@graph"
            )

            if isinstance(graph, list):
                objects.extend(graph)

        elif isinstance(data, list):
            objects.extend(data)

        for obj in objects:

            if not isinstance(obj, dict):
                continue

            obj_type = obj.get(
                "@type"
            )

            if (
                obj_type != "Product"
                and not (
                    isinstance(
                        obj_type,
                        list
                    )
                    and "Product"
                    in obj_type
                )
            ):
                continue

            image = obj.get(
                "image"
            )

            if (
                not image_url
                and image
            ):

                if isinstance(
                    image,
                    list
                ):
                    image_url = image[0]

                elif isinstance(
                    image,
                    str
                ):
                    image_url = image

            offers = obj.get(
                "offers"
            )

            if isinstance(
                offers,
                list
            ):

                offers = (
                    offers[0]
                    if offers
                    else None
                )

            if isinstance(
                offers,
                dict
            ):

                price = safe_float(
                    offers.get(
                        "price"
                    )
                )

                currency = (
                    offers.get(
                        "priceCurrency"
                    )
                )

            brand = obj.get(
                "brand"
            )

            if isinstance(
                brand,
                dict
            ):
                brand = brand.get(
                    "name"
                )

            return Product(
                name=obj.get(
                    "name",
                    title
                ),
                shop=shop,
                url=url,
                price=price,
                currency=(
                    currency.upper()
                    if currency
                    else None
                ),
                brand=brand,
                image_url=image_url,
                product_id=(
                    str(
                        obj.get(
                            "sku"
                        )
                    )
                    if obj.get("sku")
                    else None
                ),
                is_exact_match=True,
                source_text=(
                    soup.get_text(
                        " ",
                        strip=True
                    )[:5000]
                )
            )

    # Fallback: ищем цену в meta
    price_selectors = [
        {
            "property": "product:price:amount"
        },
        {
            "itemprop": "price"
        },
        {
            "name": "price"
        },
    ]

    for attrs in price_selectors:

        node = soup.find(
            "meta",
            attrs=attrs
        )

        if node:

            value = node.get(
                "content"
            )

            if value:

                price = safe_float(
                    value
                )

                if price is not None:
                    break

    currency_node = soup.find(
        "meta",
        attrs={
            "property":
                "product:price:currency"
        }
    )

    if currency_node:

        currency = currency_node.get(
            "content"
        )

    return Product(
        name=title,
        shop=shop,
        url=url,
        price=price,
        currency=(
            currency.upper()
            if currency
            else None
        ),
        image_url=image_url,
        is_exact_match=True,
        source_text=soup.get_text(
            " ",
            strip=True
        )[:5000]
    )


def resolve_ddg_url(
    url: str
) -> str:

    if not url:
        return url

    if url.startswith("//"):
        url = "https:" + url

    try:

        parsed = urlparse(url)

        query = parse_qs(
            parsed.query
        )

        uddg = query.get(
            "uddg"
        )

        if uddg:
            return unquote(
                uddg[0]
            )

    except Exception:
        pass

    return url


def web_search(
    query: str
) -> List[Product]:

    results = []

    search_url = (
        "https://html.duckduckgo.com/html/"
    )

    try:

        response = requests.get(
            search_url,
            params={
                "q": query
            },
            headers={
                "User-Agent":
                    "Mozilla/5.0"
            },
            timeout=SEARCH_TIMEOUT
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "Web search error:",
            e
        )

        return results

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    result_nodes = soup.select(
        ".result"
    )

    for node in result_nodes:

        link = node.select_one(
            ".result__a"
        )

        if not link:
            continue

        href = link.get(
            "href"
        )

        if not href:
            continue

        href = resolve_ddg_url(
            href
        )

        title = link.get_text(
            " ",
            strip=True
        )

        snippet_node = node.select_one(
            ".result__snippet"
        )

        snippet = (
            snippet_node.get_text(
                " ",
                strip=True
            )
            if snippet_node
            else ""
        )

        shop = detect_shop(
            href
        )

        if not shop:
            shop = (
                urlparse(href)
                .netloc
                .replace(
                    "www.",
                    ""
                )
            )

        price = None
        currency = None

        price_match = re.search(
            r"(?:(USD|EUR|GBP|RUB|BYN|KZT|UAH|CNY)\s*)?"
            r"([0-9][0-9\s.,]*)"
            r"\s*(\$|€|£|₽|₸|₴|¥)?",
            snippet,
            flags=re.IGNORECASE
        )

        if price_match:

            raw_value = (
                price_match.group(2)
                .replace(" ", "")
            )

            # Если есть и точка, и запятая,
            # считаем последний разделитель
            # десятичным.
            if (
                "," in raw_value
                and "." in raw_value
            ):

                if (
                    raw_value.rfind(",")
                    >
                    raw_value.rfind(".")
                ):
                    raw_value = (
                        raw_value
                        .replace(".", "")
                        .replace(",", ".")
                    )
                else:
                    raw_value = (
                        raw_value
                        .replace(",", "")
                    )

            elif "," in raw_value:

                parts = raw_value.split(",")

                if (
                    len(parts) == 2
                    and len(parts[1]) <= 2
                ):
                    raw_value = (
                        parts[0]
                        + "."
                        + parts[1]
                    )
                else:
                    raw_value = (
                        raw_value
                        .replace(",", "")
                    )

            elif "." in raw_value:

                parts = raw_value.split(".")

                if (
                    len(parts) > 2
                ):
                    raw_value = (
                        raw_value
                        .replace(".", "")
                    )

            price = safe_float(
                raw_value
            )

            currency_token = (
                price_match.group(1)
                or price_match.group(3)
            )

            if currency_token:

                currency = (
                    CURRENCY_ALIASES.get(
                        currency_token.lower()
                    )
                    or currency_token.upper()
                )

        results.append(
            Product(
                name=title,
                shop=shop,
                url=href,
                price=price,
                currency=currency,
                source_text=(
                    title
                    + " "
                    + snippet
                )
            )
        )

        if len(results) >= MAX_RESULTS:
            break

    return results
class EbayClient:

    TOKEN_URL = (
        "https://api.ebay.com/"
        "identity/v1/oauth2/token"
    )

    SEARCH_URL = (
        "https://api.ebay.com/"
        "buy/browse/v1/item_summary/search"
    )

    def __init__(self):

        self.client_id = (
            EBAY_CLIENT_ID
        )

        self.client_secret = (
            EBAY_CLIENT_SECRET
        )

        self.marketplace = (
            EBAY_MARKETPLACE_ID
        )

        self.access_token = None
        self.expires_at = 0

    def get_token(self):

        if (
            self.access_token
            and time.time()
            < self.expires_at - 60
        ):
            return self.access_token

        if (
            not self.client_id
            or not self.client_secret
        ):

            print(
                "eBay credentials are missing"
            )

            return None

        credentials = (
            f"{self.client_id}:"
            f"{self.client_secret}"
        )

        encoded = base64.b64encode(
            credentials.encode()
        ).decode()

        headers = {
            "Content-Type":
                "application/x-www-form-urlencoded",
            "Authorization":
                f"Basic {encoded}",
        }

        data = {
            "grant_type":
                "client_credentials",
            "scope":
                "https://api.ebay.com/"
                "oauth/api_scope",
        }

        try:

            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=HTTP_TIMEOUT
            )

            response.raise_for_status()

            result = response.json()

            self.access_token = (
                result.get(
                    "access_token"
                )
            )

            expires_in = int(
                result.get(
                    "expires_in",
                    7200
                )
            )

            self.expires_at = (
                time.time()
                + expires_in
            )

            print(
                "eBay OAuth token received"
            )

            return self.access_token

        except Exception as e:

            print(
                "eBay OAuth error:",
                e
            )

            return None

    def search(
        self,
        query: str
    ) -> List[Product]:

        token = self.get_token()

        if not token:
            return []

        headers = {
            "Authorization":
                f"Bearer {token}",

            "X-EBAY-C-MARKETPLACE-ID":
                self.marketplace,

            "Accept":
                "application/json",
        }

        params = {
            "q": query,
            "limit": 10,
        }

        try:

            response = requests.get(
                self.SEARCH_URL,
                headers=headers,
                params=params,
                timeout=HTTP_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            items = data.get(
                "itemSummaries",
                []
            )

            products = []

            for item in items:

                title = item.get(
                    "title",
                    "Без названия"
                )

                url = item.get(
                    "itemWebUrl",
                    ""
                )

                price_data = item.get(
                    "price"
                )

                price = None
                currency = None

                if price_data:

                    price = safe_float(
                        price_data.get(
                            "value"
                        )
                    )

                    currency = (
                        price_data.get(
                            "currency"
                        )
                    )

                image_url = None

                image = item.get(
                    "image"
                )

                if image:

                    image_url = image.get(
                        "imageUrl"
                    )

                seller = None
                seller_rating = None
                seller_feedback = None

                seller_data = item.get(
                    "seller"
                )

                if seller_data:

                    seller = (
                        seller_data.get(
                            "username"
                        )
                    )

                    seller_rating = (
                        safe_float(
                            seller_data.get(
                                "feedbackPercentage"
                            )
                        )
                    )

                    seller_feedback = (
                        safe_int(
                            seller_data.get(
                                "feedbackScore"
                            )
                        )
                    )

                products.append(
                    Product(
                        name=title,
                        shop="ebay",
                        url=url,
                        price=price,
                        currency=currency,
                        image_url=image_url,
                        seller=seller,
                        seller_rating_percent=(
                            seller_rating
                        ),
                        seller_feedback_count=(
                            seller_feedback
                        ),
                        product_id=(
                            item.get(
                                "itemId"
                            )
                        ),
                        source_text=title,
                    )
                )

            print(
                "eBay results:",
                len(products)
            )

            return products

        except Exception as e:

            print(
                "eBay search error:",
                e
            )

            return []


ebay_client = EbayClient()


def search_everywhere(
    original_query: str
) -> List[Product]:

    brain = understand(
        original_query,
        country=DEFAULT_COUNTRY,
        currency=DEFAULT_CURRENCY,
    )

    query = brain["query"]
    max_price = brain["max_price"]
    currency = brain["currency"]

    print(
        "SAVVY QUERY:",
        query,
        "MAX PRICE:",
        max_price,
        "CURRENCY:",
        currency
    )

    products = []

    # eBay
    try:
        for product in ebay_client.search(query):

            if not brain["accessory"]:
                title = (
                    product.name + " " +
                    (product.source_text or "")
                ).lower()

                bad = (
                    "case", "cover", "charger",
                    "cable", "battery", "screen",
                    "display", "чехол", "зарядка",
                    "кабель", "аккумулятор", "дисплей"
                )

                if any(word in title for word in bad):
                    continue

            if product_matches_budget(
                product,
                max_price,
                currency
            ):
                products.append(product)

    except Exception as e:
        print("eBay error:", e)

    # Web
    try:
        for product in web_search(query):

            if not brain["accessory"]:
                title = (
                    product.name + " " +
                    (product.source_text or "")
                ).lower()

                bad = (
                    "case", "cover", "charger",
                    "cable", "battery", "screen",
                    "display", "чехол", "зарядка",
                    "кабель", "аккумулятор", "дисплей"
                )

                if any(word in title for word in bad):
                    continue

            if product_matches_budget(
                product,
                max_price,
                currency
            ):
                products.append(product)

    except Exception as e:
        print("WEB error:", e)

    products = remove_duplicates(products)
    products = rank_products(products)

    print(
        "SAVVY RESULTS:",
        len(products)
    )

    return products[:MAX_RESULTS]


def init_database():

    connection = sqlite3.connect(
        DB_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            max_price REAL,
            currency TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def add_track(
    chat_id: int,
    query: str,
    max_price: Optional[float],
    currency: str
):

    connection = sqlite3.connect(
        DB_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tracks
        (chat_id, query, max_price, currency, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            query,
            max_price,
            currency,
            datetime.utcnow().isoformat()
        )
    )

    connection.commit()
    connection.close()


def get_tracks():

    connection = sqlite3.connect(
        DB_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            chat_id,
            query,
            max_price,
            currency
        FROM tracks
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def analyze_photo(
    image_bytes: bytes
) -> Optional[str]:

    if (
        not OPENAI_API_KEY
        or OpenAI is None
    ):
        return None

    try:

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        encoded = base64.b64encode(
            image_bytes
        ).decode()

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Определи товар на фотографии. "
                                "Верни только JSON с полями: "
                                "query, brand, model, category, "
                                "color, gender, description, confidence."
                            )
                        },
                        {
                            "type": "input_image",
                            "image_url":
                                "data:image/jpeg;base64,"
                                + encoded
                        }
                    ]
                }
            ]
        )

        text = response.output_text

        try:

            data = json.loads(
                text
            )

            query = data.get(
                "query"
            )

            if query:
                return query

        except Exception:
            pass

        return text.strip()

    except Exception as e:

        print(
            "OpenAI image error:",
            e
        )

        return None


def ai_check_product(
    product_text: str
) -> str:

    if (
        not OPENAI_API_KEY
        or OpenAI is None
    ):

        return (
            "🧠 <b>SAVVY CHECK</b>\n\n"
            "Для полноценного AI-анализа "
            "добавь OPENAI_API_KEY в Railway.\n\n"
            "Пока могу оценивать товар "
            "по цене, рейтингу, отзывам "
            "и данным продавца."
        )

    try:

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=(
                "Ты AI-консультант SAVVY SENSE. "
                "Оцени товар для покупки.\n\n"
                "Товар:\n"
                + product_text
                + "\n\n"
                "Дай кратко:\n"
                "1. стоит ли покупать;\n"
                "2. главные плюсы;\n"
                "3. главные риски;\n"
                "4. кому подходит;\n"
                "5. итоговая рекомендация."
            )
        )

        return (
            "🧠 <b>SAVVY CHECK</b>\n\n"
            + response.output_text
        )

    except Exception as e:

        print(
            "OpenAI check error:",
            e
        )

        return (
            "Не удалось выполнить AI-анализ "
            "сейчас. Попробуй ещё раз."
        )


def split_message(
    text: str,
    limit: int = 3500
) -> List[str]:

    if len(text) <= limit:
        return [text]

    parts = []

    while len(text) > limit:

        cut = text.rfind(
            "\n",
            0,
            limit
        )

        if cut <= 0:
            cut = limit

        parts.append(
            text[:cut]
        )

        text = text[cut:].lstrip()

    if text:
        parts.append(text)

    return parts


bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


def send_long_message(
    chat_id: int,
    text: str
):

    for part in split_message(
        text
    ):

        bot.send_message(
            chat_id,
            part,
            disable_web_page_preview=True
        )


@bot.message_handler(
    commands=[
        "start"
    ]
)
def start_command(message):

    text = (
        "🧠 <b>SAVVY SENSE</b>\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь мне:\n"
        "• название товара;\n"
        "• ссылку;\n"
        "• фотографию.\n\n"
        "Например:\n"
        "<b>Айфон 15 до $500</b>\n\n"
        "Я сам определю запрос "
        "и начну поиск."
    )

    bot.send_message(
        message.chat.id,
        text
    )


@bot.message_handler(
    commands=[
        "help"
    ]
)
def help_command(message):

    text = (
        "🧠 <b>SAVVY SENSE — помощь</b>\n\n"
        "/find — найти товар\n"
        "/compare — сравнить товары\n"
        "/cheaper — найти дешевле\n"
        "/check — стоит ли покупать\n"
        "/track — отслеживать цену\n\n"
        "Но команды не обязательны.\n\n"
        "Просто напиши, что хочешь купить."
    )

    bot.send_message(
        message.chat.id,
        text
    )


@bot.message_handler(
    commands=[
        "find",
        "compare",
        "cheaper"
    ]
)
def search_command(message):

    query = message.text or ""

    parts = query.split(
        maxsplit=1
    )

    if len(parts) < 2:

        bot.send_message(
            message.chat.id,
            "Напиши товар после команды.\n\n"
            "Например:\n"
            "/find iPhone 15 до $500"
        )

        return

    user_query = parts[1]

    bot.send_message(
        message.chat.id,
        "⏳ Ищу лучшие предложения..."
    )

    try:

        products = search_everywhere(
            user_query
        )

        if not products:

            cleaned, max_price, currency = (
                parse_budget(
                    clean_query(
                        user_query
                    )
                )
            )

            send_long_message(
                message.chat.id,
                make_no_results_message(
                    cleaned,
                    max_price,
                    currency
                )
            )

            return

        cleaned, max_price, currency = (
            parse_budget(
                clean_query(
                    user_query
                )
            )
        )

        send_long_message(
            message.chat.id,
            make_results_message(
                cleaned,
                products,
                max_price,
                currency
            )
        )

    except Exception as e:

        print(
            "Search command error:",
            e
        )

        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка поиска. "
            "Попробуй ещё раз."
        )


@bot.message_handler(
    commands=[
        "track"
    ]
)
def track_command(message):

    parts = (
        (message.text or "")
        .split(
            maxsplit=1
        )
    )

    if len(parts) < 2:

        bot.send_message(
            message.chat.id,
            "Например:\n"
            "/track iPhone 15 до $500"
        )

        return

    query = parts[1]

    cleaned, max_price, currency = (
        parse_budget(
            clean_query(query)
        )
    )

    add_track(
        message.chat.id,
        cleaned,
        max_price,
        currency
    )

    bot.send_message(
        message.chat.id,
        "🔔 <b>Отслеживание включено.</b>\n\n"
        f"Товар: <b>{cleaned}</b>\n"
        + (
            f"Лимит: "
            f"<b>{fmt_money(max_price, currency)}</b>\n"
            if max_price is not None
            else ""
        )
        + "\nЯ буду проверять цену автоматически."
    )


@bot.message_handler(
    commands=[
        "check"
    ]
)
def check_command(message):

    parts = (
        (message.text or "")
        .split(
            maxsplit=1
        )
    )

    if len(parts) < 2:

        bot.send_message(
            message.chat.id,
            "Например:\n"
            "/check iPhone 15"
        )

        return

    query = parts[1]

    bot.send_message(
        message.chat.id,
        "🧠 Анализирую..."
    )

    products = search_everywhere(
        query
    )

    if products:

        product = products[0]

        text = format_product(
            product,
            1
        )

        send_long_message(
            message.chat.id,
            ai_check_product(
                text
            )
        )

    else:

        bot.send_message(
            message.chat.id,
            ai_check_product(
                query
            )
        )


@bot.message_handler(
    content_types=[
        "photo"
    ]
)
def photo_handler(message):

    if not OPENAI_API_KEY:

        bot.send_message(
            message.chat.id,
            "📷 Фото получено.\n\n"
            "Для AI-распознавания товара "
            "нужно добавить OPENAI_API_KEY "
            "в Railway Variables."
        )

        return

    bot.send_message(
        message.chat.id,
        "📷 Анализирую товар на фото..."
    )

    try:

        file_info = bot.get_file(
            message.photo[-1].file_id
        )

        downloaded = bot.download_file(
            file_info.file_path
        )

        query = analyze_photo(
            downloaded
        )

        if not query:

            bot.send_message(
                message.chat.id,
                "Не удалось определить товар "
                "на фотографии."
            )

            return

        bot.send_message(
            message.chat.id,
            f"🔎 Определил товар:\n"
            f"<b>{query}</b>\n\n"
            f"🌎 Ищу предложения..."
        )

        products = search_everywhere(
            query
        )

        if not products:

            bot.send_message(
                message.chat.id,
                "Подходящих предложений "
                "не найдено."
            )

            return

        send_long_message(
            message.chat.id,
            make_results_message(
                query,
                products,
                None,
                DEFAULT_CURRENCY
            )
        )

    except Exception as e:

        print(
            "Photo handler error:",
            e
        )

        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось обработать фотографию."
        )


@bot.message_handler(
    content_types=[
        "text"
    ]
)
def text_handler(message):

    text = (
        message.text or ""
    ).strip()

    if not text:
        return

    # Приветствия
    greetings = {
        "привет",
        "здравствуйте",
        "здравствуй",
        "добрый день",
        "добрый вечер",
        "доброе утро",
        "хай",
        "hello",
        "hi",
    }

    if text.lower() in greetings:

        bot.send_message(
            message.chat.id,
            "🧠 Привет!\n\n"
            "Напиши, какой товар хочешь найти, "
            "и я начну поиск."
        )

        return

    url = extract_url(
        text
    )

    bot.send_message(
        message.chat.id,
        "⏳ Ищу лучшие предложения..."
    )

    try:

        # ----------------------------------------------------
        # Пользователь отправил ссылку
        # ----------------------------------------------------

        if url:

            source_product = (
                extract_product_from_html(
                    url
                )
            )

            if source_product:

                source_product.is_exact_match = True

                source_query = (
                    source_product.name
                )

                search_query = clean_query(
                    source_query
                )

                alternatives = (
                    search_everywhere(
                        search_query
                    )
                )

                all_products = [
                    source_product
                ]

                all_products.extend(
                    alternatives
                )

                all_products = (
                    remove_duplicates(
                        all_products
                    )
                )

                all_products = (
                    rank_products(
                        all_products
                    )
                )

                send_long_message(
                    message.chat.id,
                    make_results_message(
                        search_query,
                        all_products,
                        None,
                        DEFAULT_CURRENCY
                    )
                )

                return

            # Если страницу не удалось прочитать,
            # всё равно попробуем искать по URL.
            products = search_everywhere(
                text
            )

        else:

            products = search_everywhere(
                text
            )

        cleaned, max_price, currency = (
            parse_budget(
                clean_query(
                    text
                )
            )
        )

        if not products:

            send_long_message(
                message.chat.id,
                make_no_results_message(
                    cleaned,
                    max_price,
                    currency
                )
            )

            return

        send_long_message(
            message.chat.id,
            make_results_message(
                cleaned,
                products,
                max_price,
                currency
            )
        )

    except Exception as e:

        print(
            "Text handler error:",
            e
        )

        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка.\n"
            "Попробуй повторить запрос."
        )


def tracking_worker():

    while True:

        try:

            tracks = get_tracks()

            for (
                track_id,
                chat_id,
                query,
                max_price,
                currency
            ) in tracks:

                products = search_everywhere(
                    query
                )

                if not products:
                    continue

                best = products[0]

                if (
                    max_price is not None
                    and best.price is not None
                    and best.currency
                ):

                    if product_matches_budget(
                        best,
                        max_price,
                        currency
                    ):

                        message = (
                            "🔔 <b>SAVVY SENSE PRICE ALERT</b>\n\n"
                            f"Нашёл предложение по запросу:\n"
                            f"<b>{query}</b>\n\n"
                            f"💰 {fmt_money(best.price, best.currency)}\n"
                            f"🏪 {best.shop.upper()}\n\n"
                            f"{best.url}"
                        )

                        try:

                            bot.send_message(
                                chat_id,
                                message,
                                disable_web_page_preview=True
                            )

                        except Exception as send_error:

                            print(
                                "Tracking send error:",
                                send_error
                            )

        except Exception as e:

            print(
                "Tracking worker error:",
                e
            )

        time.sleep(
            TRACK_INTERVAL_SECONDS
        )


def main():

    init_database()

    tracking_thread = threading.Thread(
        target=tracking_worker,
        daemon=True
    )

    tracking_thread.start()

    print(
        "SAVVY SENSE started"
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )


if __name__ == "__main__":
    main()