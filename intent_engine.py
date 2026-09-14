import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# ============================================================
# SAVVY SENSE — INTENT ENGINE
# ============================================================
#
# Задача:
# Превратить естественный запрос пользователя в структурированное
# намерение, которое затем передаётся Global Search Engine.
#
# Пример:
#
# "Мне нужна черная майка поло размер L, цена до 80р"
#
# =>
# product = "polo shirt"
# color = "black"
# size = "L"
# max_price = 80
# currency = "BYN"
# product_type = "main_product"
#
# ============================================================


@dataclass
class ShoppingIntent:
    original_query: str

    # Что ищем
    product: str = ""
    category: str = ""
    brand: Optional[str] = None
    model: Optional[str] = None

    # Атрибуты
    color: Optional[str] = None
    size: Optional[str] = None
    gender: Optional[str] = None
    condition: Optional[str] = None
    material: Optional[str] = None

    # Технические характеристики
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Количество
    quantity: int = 1

    # Цена
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: Optional[str] = None

    # Доставка
    destination_country: Optional[str] = None
    shipping_required: bool = True

    # Что именно ищем
    product_type: str = "main_product"
    accessory_requested: bool = False

    # Дополнительные требования
    requirements: List[str] = field(default_factory=list)

    # Что важно пользователю
    priorities: List[str] = field(
        default_factory=lambda: [
            "match",
            "total_cost",
            "quality",
            "delivery",
        ]
    )

    # Уровень уверенности
    confidence: float = 0.0

    # Очищенный запрос для поисковиков
    search_query: str = ""

    # Возможные варианты поискового запроса
    search_queries: List[str] = field(default_factory=list)

    # Системная информация
    parser: str = "fallback"


# ============================================================
# СЛОВАРИ
# ============================================================

COLOR_MAP = {
    "черн": "black",
    "чёрн": "black",
    "black": "black",

    "бел": "white",
    "белый": "white",
    "белая": "white",
    "white": "white",

    "красн": "red",
    "red": "red",

    "син": "blue",
    "голуб": "blue",
    "blue": "blue",

    "зел": "green",
    "green": "green",

    "сер": "gray",
    "grey": "gray",
    "gray": "gray",

    "желт": "yellow",
    "жёлт": "yellow",
    "yellow": "yellow",

    "роз": "pink",
    "pink": "pink",

    "фиолет": "purple",
    "purple": "purple",

    "корич": "brown",
    "brown": "brown",

    "оранж": "orange",
    "orange": "orange",

    "беж": "beige",
    "beige": "beige",

    "хаки": "khaki",
    "khaki": "khaki",

    "золот": "gold",
    "gold": "gold",

    "серебр": "silver",
    "silver": "silver",
}


ACCESSORY_TERMS = {
    "чехол",
    "case",
    "cover",
    "стекло",
    "защитное стекло",
    "плёнка",
    "пленка",
    "screen protector",
    "кабель",
    "cable",
    "зарядка",
    "charger",
    "зарядное устройство",
    "адаптер",
    "adapter",
    "ремешок",
    "strap",
    "клавиатура",
    "keyboard",
    "мышь",
    "mouse",
    "наушники",
    "headphones",
    "гарнитура",
    "чехол-книжка",
    "корпус",
    "housing",
    "back glass",
    "дисплей",
    "display",
    "экран",
    "screen",
    "digitizer",
    "replacement",
    "замена",
    "запчасть",
    "запчасти",
    "part",
    "parts",
    "аксессуар",
    "accessory",
}


MAIN_PRODUCT_HINTS = {
    "телефон",
    "смартфон",
    "iphone",
    "айфон",
    "samsung",
    "pixel",
    "ноутбук",
    "laptop",
    "компьютер",
    "computer",
    "телевизор",
    "tv",
    "монитор",
    "monitor",
    "пылесос",
    "vacuum",
    "холодильник",
    "refrigerator",
    "стиральная машина",
    "washing machine",
    "куртка",
    "пальто",
    "рубашка",
    "футболка",
    "майка",
    "поло",
    "кроссовки",
    "ботинки",
    "туфли",
    "джинсы",
    "брюки",
    "платье",
    "велосипед",
    "велосипед",
    "автомобиль",
    "машина",
    "камера",
    "фотоаппарат",
    "часы",
    "watch",
}


# ============================================================
# НОРМАЛИЗАЦИЯ
# ============================================================

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip().lower()

    text = text.replace("ё", "е")

    # Разные варианты тире
    text = re.sub(r"[–—−]", "-", text)

    # Убираем повторяющиеся пробелы
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_color(text: str) -> Optional[str]:
    text = normalize_text(text)

    for key, value in COLOR_MAP.items():
        if re.search(rf"\b{re.escape(key)}\w*", text):
            return value

    return None


def detect_size(text: str) -> Optional[str]:
    text = normalize_text(text)

    # Международные размеры
    match = re.search(
        r"(?:размер|size|разм\.?)\s*[:\-]?\s*"
        r"(xxxs|xxs|xs|s|m|l|xl|xxl|xxxl|xxxxl)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).upper()

    # Размер без слова "размер":
    match = re.search(
        r"\b(XXXL|XXL|XL|L|M|S|XS|XXS|XXXS)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).upper()

    # EU обувь / одежда и т.п.
    match = re.search(
        r"(?:размер|size|eu)\s*[:\-]?\s*(\d{2,3}(?:[.,]\d)?)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).replace(",", ".")

    return None


# ============================================================
# ВАЛЮТА
# ============================================================

def detect_currency(text: str) -> Optional[str]:
    text = normalize_text(text)

    # Белорусский рубль
    byn_patterns = [
        r"\bbyn\b",
        r"\bбел\.?\s*руб",
        r"\bбелорусск\w*\s+руб",
        r"\bбелорусск\w*\s+рубл",
        r"\bбел\s+руб",
        r"бел\.?\s*р\b",
    ]

    for pattern in byn_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "BYN"

    # Доллар
    usd_patterns = [
        r"\busd\b",
        r"\bдоллар\w*\b",
        r"\bdollar\w*\b",
        r"\$",
    ]

    for pattern in usd_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "USD"

    # Евро
    eur_patterns = [
        r"\beur\b",
        r"\bевро\b",
        r"\beuro\b",
        r"€",
    ]

    for pattern in eur_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "EUR"

    # Китайский юань
    cny_patterns = [
        r"\bcny\b",
        r"\byuan\b",
        r"\bюан\w*\b",
        r"¥",
    ]

    for pattern in cny_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "CNY"

    # Казахстанский тенге
    kzt_patterns = [
        r"\bkzt\b",
        r"\bтенге\b",
        r"\b₸",
    ]

    for pattern in kzt_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "KZT"

    # Украинская гривна
    uah_patterns = [
        r"\buah\b",
        r"\bгривн\w*\b",
        r"\b₴",
    ]

    for pattern in uah_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "UAH"

    # Польский злотый
    pln_patterns = [
        r"\bpln\b",
        r"\bзлот\w*\b",
        r"\bzl\b",
    ]

    for pattern in pln_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "PLN"

    # Фунт
    gbp_patterns = [
        r"\bgbp\b",
        r"\bфунт\w*\b",
        r"\bpound\w*\b",
        r"£",
    ]

    for pattern in gbp_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "GBP"

    # Российский рубль — ТОЛЬКО если явно указан.
    #
    # ВАЖНО:
    # "80р" сам по себе неоднозначен.
    # В контексте белорусского пользователя и BYN-профиля
    # можно позже использовать память пользователя.
    #
    # Здесь намеренно не превращаем любой "р" автоматически
    # в RUB.
    rub_patterns = [
        r"\brub\b",
        r"\bроссийск\w*\s+руб",
        r"\bрос\s+руб",
        r"\bроссийск\w*\s+рубл",
        r"₽",
    ]

    for pattern in rub_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return "RUB"

    return None


# ============================================================
# ЦЕНА
# ============================================================

def _number(value: str) -> float:
    value = value.replace(" ", "")
    value = value.replace(",", ".")

    return float(value)


def parse_price_constraint(
    text: str,
) -> tuple[Optional[float], Optional[float]]:

    text = normalize_text(text)

    # Диапазон:
    # 100-200
    # 100 — 200
    match = re.search(
        r"\b(\d+(?:[.,]\d+)?)\s*(?:-|до|—)\s*"
        r"(\d+(?:[.,]\d+)?)\b",
        text,
    )

    if match:
        first = _number(match.group(1))
        second = _number(match.group(2))

        return min(first, second), max(first, second)

    # До X
    patterns_max = [
        r"(?:до|не\s+дороже|максимум|макс\.?|не\s+более|в\s+пределах\s+до)"
        r"\s*(\d+(?:[.,]\d+)?)",

        r"(\d+(?:[.,]\d+)?)\s*(?:максимум|макс\.?)",
    ]

    for pattern in patterns_max:
        match = re.search(pattern, text)

        if match:
            return None, _number(match.group(1))

    # От X
    patterns_min = [
        r"(?:от|не\s+дешевле|минимум|мин\.?)"
        r"\s*(\d+(?:[.,]\d+)?)",
    ]

    for pattern in patterns_min:
        match = re.search(pattern, text)

        if match:
            return _number(match.group(1)), None

    # Явная цена:
    # за 500
    # цена 500
    # стоит 500
    match = re.search(
        r"(?:цена|стоит|стоимость|за)\s*"
        r"(\d+(?:[.,]\d+)?)",
        text,
    )

    if match:
        value = _number(match.group(1))
        return value, value

    return None, None


def parse_price_and_currency(
    text: str,
) -> tuple[Optional[float], Optional[float], Optional[str]]:

    currency = detect_currency(text)

    min_price, max_price = parse_price_constraint(text)

    return min_price, max_price, currency


# ============================================================
# ТИП ТОВАРА
# ============================================================

def detect_product_type(text: str) -> tuple[str, bool]:
    text = normalize_text(text)

    for term in ACCESSORY_TERMS:
        if term in text:
            return "accessory", True

    return "main_product", False


# ============================================================
# БРЕНДЫ
# ============================================================

KNOWN_BRANDS = [
    "apple",
    "iphone",
    "samsung",
    "google",
    "pixel",
    "xiaomi",
    "huawei",
    "honor",
    "oneplus",
    "sony",
    "lg",
    "asus",
    "acer",
    "lenovo",
    "hp",
    "dell",
    "msi",
    "nike",
    "adidas",
    "puma",
    "reebok",
    "new balance",
    "zara",
    "uniqlo",
    "lacoste",
    "polo ralph lauren",
    "ralph lauren",
]


def detect_brand(text: str) -> Optional[str]:
    text = normalize_text(text)

    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if brand in text:
            return brand

    return None


# ============================================================
# СОСТОЯНИЕ
# ============================================================

def detect_condition(text: str) -> Optional[str]:
    text = normalize_text(text)

    if any(
        phrase in text
        for phrase in [
            "новый",
            "новая",
            "новое",
            "новые",
            "new",
        ]
    ):
        return "new"

    if any(
        phrase in text
        for phrase in [
            "б/у",
            "бу",
            "бывший в употреблении",
            "used",
            "pre-owned",
        ]
    ):
        return "used"

    if any(
        phrase in text
        for phrase in [
            "восстановленный",
            "восстановлен",
            "refurbished",
        ]
    ):
        return "refurbished"

    return None


# ============================================================
# КОЛИЧЕСТВО
# ============================================================

def detect_quantity(text: str) -> int:
    text = normalize_text(text)

    patterns = [
        r"\b(\d+)\s*(?:шт|штук|штуки|pcs|pieces)\b",
        r"\b(\d+)\s*(?:товара|товаров)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            try:
                quantity = int(match.group(1))

                if 1 <= quantity <= 1000:
                    return quantity

            except Exception:
                pass

    return 1


# ============================================================
# МОДЕЛЬ
# ============================================================

def detect_model(text: str) -> Optional[str]:
    text = normalize_text(text)

    # iPhone 15 / iPhone 15 Pro Max
    match = re.search(
        r"\biphone\s+"
        r"(\d+(?:\s+(?:pro|max|plus|mini|promax))*)",
        text,
        re.IGNORECASE,
    )

    if match:
        return "iPhone " + match.group(1).strip()

    # Samsung Galaxy S24 Ultra
    match = re.search(
        r"\b("
        r"galaxy\s+[a-z]?\d+\w*"
        r"|pixel\s+\d+\w*"
        r"|xbox\s+\w+"
        r"|playstation\s+\d+\w*"
        r")\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# УДАЛЕНИЕ ЦЕНЫ И СЛУЖЕБНЫХ СЛОВ
# ============================================================

def clean_for_search(text: str) -> str:
    text = normalize_text(text)

    # Убираем ценовые конструкции.
    patterns = [
        r"(?:до|не\s+дороже|максимум|макс\.?|не\s+более)\s*"
        r"\d+(?:[.,]\d+)?\s*"
        r"(?:byn|usd|eur|cny|kzt|uah|pln|gbp|rub|"
        r"доллар\w*|евро|юан\w*|тенге|гривн\w*|"
        r"руб\w*|р\b|\$|€|¥|₽|₸|₴|£)?",

        r"(?:цена|стоимость|стоит)\s*"
        r"(?:до\s*)?\d+(?:[.,]\d+)?\s*"
        r"(?:byn|usd|eur|cny|kzt|uah|pln|gbp|rub|"
        r"доллар\w*|евро|юан\w*|руб\w*|р\b|\$|€|¥|₽)?",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Служебные слова
    stop_words = [
        "мне нужна",
        "мне нужен",
        "мне нужно",
        "я хочу",
        "хочу",
        "нужен",
        "нужна",
        "нужно",
        "найди мне",
        "найди",
        "подбери мне",
        "подбери",
        "пожалуйста",
        "поищи",
        "ищу",
    ]

    for phrase in stop_words:
        text = text.replace(phrase, " ")

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# FALLBACK PARSER
# ============================================================

def parse_fallback(query: str) -> ShoppingIntent:

    original = query
    text = normalize_text(query)

    min_price, max_price, currency = parse_price_and_currency(text)

    # Специальная обработка короткого "р".
    #
    # Если пользователь пишет:
    # "80р"
    #
    # мы НЕ объявляем его RUB автоматически.
    #
    # Здесь оставляем валюту неизвестной.
    # Позже User Memory сможет подсказать предпочтительную валюту.
    #
    if re.search(r"\d+(?:[.,]\d+)?\s*р\b", text):
        if currency is None:
            currency = None

    color = detect_color(text)
    size = detect_size(text)

    brand = detect_brand(text)
    model = detect_model(text)

    condition = detect_condition(text)

    quantity = detect_quantity(text)

    product_type, accessory_requested = detect_product_type(text)

    search_query = clean_for_search(text)

    # Категория
    category = ""

    if "поло" in text or "polo" in text:
        category = "polo shirt"

    elif "майка" in text:
        category = "tank top / sleeveless shirt"

    elif "футболка" in text:
        category = "t-shirt"

    elif "кроссов" in text or "sneaker" in text:
        category = "sneakers"

    elif "куртк" in text or "jacket" in text:
        category = "jacket"

    elif "ноутбук" in text or "laptop" in text:
        category = "laptop"

    elif "телефон" in text or "смартфон" in text:
        category = "smartphone"

    elif "айфон" in text or "iphone" in text:
        category = "smartphone"

    elif "телевизор" in text or "tv" in text:
        category = "television"

    # Если нашли модель iPhone
    if model and "iphone" in model.lower():
        category = "smartphone"

    product = search_query

    # Убираем атрибуты из поисковой фразы не полностью —
    # часть слов оставляем для естественного поиска.
    #
    # Например:
    # "черная майка поло размер L"
    #
    # => "черная майка поло размер l"
    #
    # Поисковые коннекторы сами смогут использовать этот запрос.

    requirements = []

    if color:
        requirements.append(f"color:{color}")

    if size:
        requirements.append(f"size:{size}")

    if condition:
        requirements.append(f"condition:{condition}")

    if accessory_requested:
        requirements.append("accessory_requested")

    # Приоритеты
    priorities = [
        "match",
        "total_cost",
        "quality",
        "delivery",
    ]

    # Если пользователь явно говорит "дешевый"
    if any(
        phrase in text
        for phrase in [
            "самый дешевый",
            "самая дешевая",
            "подешевле",
            "дешевле",
            "cheap",
            "cheapest",
        ]
    ):
        priorities = [
            "total_cost",
            "match",
            "delivery",
            "quality",
        ]

    # Если пользователь говорит "лучший"
    if any(
        phrase in text
        for phrase in [
            "лучший",
            "лучшее",
            "лучше",
            "best",
            "качественный",
            "качественное",
        ]
    ):
        priorities = [
            "quality",
            "match",
            "total_cost",
            "delivery",
        ]

    confidence_parts = 0

    if search_query:
        confidence_parts += 0.25

    if color:
        confidence_parts += 0.10

    if size:
        confidence_parts += 0.10

    if currency:
        confidence_parts += 0.10

    if max_price is not None:
        confidence_parts += 0.15

    if brand or model:
        confidence_parts += 0.10

    if category:
        confidence_parts += 0.10

    confidence = min(confidence_parts, 0.90)

    return ShoppingIntent(
        original_query=original,
        product=product,
        category=category,
        brand=brand,
        model=model,
        color=color,
        size=size,
        condition=condition,
        attributes={},
        quantity=quantity,
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        destination_country=None,
        shipping_required=True,
        product_type=product_type,
        accessory_requested=accessory_requested,
        requirements=requirements,
        priorities=priorities,
        confidence=confidence,
        search_query=search_query,
        search_queries=build_search_queries(
            search_query,
            category,
            brand,
            model,
            color,
            size,
        ),
        parser="fallback",
    )


# ============================================================
# ПОИСКОВЫЕ ЗАПРОСЫ
# ============================================================

def build_search_queries(
    search_query: str,
    category: str,
    brand: Optional[str],
    model: Optional[str],
    color: Optional[str],
    size: Optional[str],
) -> List[str]:

    queries = []

    if search_query:
        queries.append(search_query)

    parts = []

    if brand:
        parts.append(brand)

    if model and model.lower() not in " ".join(parts).lower():
        parts.append(model)

    if category:
        parts.append(category)

    if color:
        parts.append(color)

    if size:
        parts.append(size)

    structured = " ".join(parts).strip()

    if structured and structured not in queries:
        queries.append(structured)

    # Английский вариант полезен для Amazon/eBay/etc.
    if category:
        english_parts = []

        if brand:
            english_parts.append(brand)

        if model:
            english_parts.append(model)

        english_parts.append(category)

        if color:
            english_parts.append(color)

        if size:
            english_parts.append(size)

        english_query = " ".join(english_parts)

        if english_query and english_query not in queries:
            queries.append(english_query)

    return queries[:5]


# ============================================================
# OPENAI PARSER
# ============================================================

class AIIntentParser:

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.client = None

        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as exc:
                print("SAVVY AI INIT ERROR:", exc)

    def available(self) -> bool:
        return self.client is not None

    def parse(self, query: str) -> Optional[ShoppingIntent]:

        if not self.client:
            return None

        system_prompt = """
You are the intent engine of SAVVY SENSE,
a global AI shopping assistant.

Your job is NOT to search for products.
Your job is to understand exactly what the user wants
and convert the request into structured JSON.

Rules:

1. Understand natural language.
2. Extract product/category.
3. Extract brand and model.
4. Extract color.
5. Extract size.
6. Extract gender when explicitly stated.
7. Extract condition: new, used, refurbished.
8. Extract quantity.
9. Extract minimum and maximum price.
10. Identify currency carefully.
11. Do not confuse BYN with RUB.
12. Do not assume that every "р" means RUB.
13. If "80р" is ambiguous, return currency=null.
14. Identify whether the user wants the main product or an accessory.
15. "iPhone 15" means the smartphone itself unless an accessory
    is explicitly requested.
16. "iPhone 15 case" means an accessory.
17. Preserve important product characteristics.
18. Do not invent information.
19. Do not invent a brand, size, model, currency or specification.
20. Search queries should be useful for international marketplaces.
21. Return valid JSON only.

JSON schema:

{
  "product": "",
  "category": "",
  "brand": null,
  "model": null,
  "color": null,
  "size": null,
  "gender": null,
  "condition": null,
  "attributes": {},
  "quantity": 1,
  "min_price": null,
  "max_price": null,
  "currency": null,
  "product_type": "main_product",
  "accessory_requested": false,
  "requirements": [],
  "priorities": [],
  "search_query": "",
  "confidence": 0.0
}

Currency codes allowed:
USD, EUR, BYN, RUB, CNY, KZT, UAH, PLN, GBP

Important:
If the user says "80р" and there is no reliable context
identifying the currency, do NOT guess RUB.
Return null.

If the surrounding user profile later provides a preferred
currency, another component may resolve the ambiguity.
"""

        try:
            response = self.client.responses.create(
                model=os.getenv(
                    "SAVVY_INTENT_MODEL",
                    "gpt-4o-mini",
                ),
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
            )

            text = getattr(response, "output_text", None)

            if not text:
                return None

            text = text.strip()

            # Иногда модель может вернуть ```json ... ```
            text = re.sub(
                r"^```json\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )

            text = re.sub(
                r"\s*```$",
                "",
                text,
            )

            data = json.loads(text)

            if not isinstance(data, dict):
                return None

            return self._to_intent(query, data)

        except Exception as exc:
            print("SAVVY AI INTENT ERROR:", exc)
            return None

    def _to_intent(
        self,
        original_query: str,
        data: Dict[str, Any],
    ) -> ShoppingIntent:

        product = str(
            data.get("product") or ""
        ).strip()

        category = str(
            data.get("category") or ""
        ).strip()

        brand = data.get("brand")
        model = data.get("model")
        color = data.get("color")
        size = data.get("size")
        gender = data.get("gender")
        condition = data.get("condition")

        attributes = data.get("attributes")

        if not isinstance(attributes, dict):
            attributes = {}

        quantity = data.get("quantity", 1)

        try:
            quantity = int(quantity)
        except Exception:
            quantity = 1

        quantity = max(1, min(quantity, 1000))

        min_price = data.get("min_price")
        max_price = data.get("max_price")

        try:
            if min_price is not None:
                min_price = float(min_price)
        except Exception:
            min_price = None

        try:
            if max_price is not None:
                max_price = float(max_price)
        except Exception:
            max_price = None

        currency = data.get("currency")

        if currency:
            currency = str(currency).upper().strip()

        allowed_currencies = {
            "USD",
            "EUR",
            "BYN",
            "RUB",
            "CNY",
            "KZT",
            "UAH",
            "PLN",
            "GBP",
        }

        if currency not in allowed_currencies:
            currency = None

        product_type = str(
            data.get("product_type") or "main_product"
        )

        if product_type not in {
            "main_product",
            "accessory",
        }:
            product_type = "main_product"

        accessory_requested = bool(
            data.get(
                "accessory_requested",
                product_type == "accessory",
            )
        )

        requirements = data.get("requirements", [])

        if not isinstance(requirements, list):
            requirements = []

        requirements = [
            str(item).strip()
            for item in requirements
            if str(item).strip()
        ]

        priorities = data.get("priorities", [])

        if not isinstance(priorities, list):
            priorities = []

        priorities = [
            str(item).strip()
            for item in priorities
            if str(item).strip()
        ]

        if not priorities:
            priorities = [
                "match",
                "total_cost",
                "quality",
                "delivery",
            ]

        search_query = str(
            data.get("search_query") or product
        ).strip()

        intent = ShoppingIntent(
            original_query=original_query,
            product=product,
            category=category,
            brand=brand,
            model=model,
            color=color,
            size=size,
            gender=gender,
            condition=condition,
            attributes=attributes,
            quantity=quantity,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            product_type=product_type,
            accessory_requested=accessory_requested,
            requirements=requirements,
            priorities=priorities,
            confidence=float(
                data.get("confidence") or 0.0
            ),
            search_query=search_query,
            parser="openai",
        )

        intent.search_queries = build_search_queries(
            search_query,
            category,
            brand,
            model,
            color,
            size,
        )

        return intent


# ============================================================
# ГЛАВНЫЙ ENGINE
# ============================================================

class SavvyIntentEngine:

    def __init__(self):
        self.ai = AIIntentParser()

    def parse(
        self,
        query: str,
        preferred_currency: Optional[str] = None,
        destination_country: Optional[str] = None,
    ) -> ShoppingIntent:

        query = query.strip()

        if not query:
            return ShoppingIntent(
                original_query="",
                parser="empty",
            )

        # Сначала AI.
        intent = self.ai.parse(query)

        # Если AI не смог — fallback.
        if intent is None:
            intent = parse_fallback(query)

        # ----------------------------------------------------
        # Безопасное разрешение валюты
        # ----------------------------------------------------

        if not intent.currency and preferred_currency:
            preferred_currency = preferred_currency.upper()

            if preferred_currency in {
                "USD",
                "EUR",
                "BYN",
                "RUB",
                "CNY",
                "KZT",
                "UAH",
                "PLN",
                "GBP",
            }:
                # Используем предпочтительную валюту только тогда,
                # когда в запросе валюта действительно не определена.
                intent.currency = preferred_currency

        # ----------------------------------------------------
        # Страна доставки
        # ----------------------------------------------------

        if destination_country:
            intent.destination_country = destination_country

        # ----------------------------------------------------
        # Дополнительная защита от ошибок AI
        # ----------------------------------------------------

        normalized = normalize_text(query)

        # Если пользователь явно указал аксессуар,
        # основной товар не должен быть выбран AI ошибочно.
        explicit_accessory = any(
            term in normalized
            for term in ACCESSORY_TERMS
        )

        if explicit_accessory:
            intent.accessory_requested = True
            intent.product_type = "accessory"

        # Если запрос содержит основной товар без аксессуара,
        # сохраняем main_product.
        if (
            not explicit_accessory
            and any(
                term in normalized
                for term in MAIN_PRODUCT_HINTS
            )
        ):
            intent.product_type = "main_product"
            intent.accessory_requested = False

        # ----------------------------------------------------
        # Цена должна быть числом
        # ----------------------------------------------------

        if intent.max_price is not None:
            try:
                intent.max_price = float(intent.max_price)

                if intent.max_price <= 0:
                    intent.max_price = None

            except Exception:
                intent.max_price = None

        if intent.min_price is not None:
            try:
                intent.min_price = float(intent.min_price)

                if intent.min_price < 0:
                    intent.min_price = None

            except Exception:
                intent.min_price = None

        # Если min > max — исправляем порядок.
        if (
            intent.min_price is not None
            and intent.max_price is not None
            and intent.min_price > intent.max_price
        ):
            intent.min_price, intent.max_price = (
                intent.max_price,
                intent.min_price,
            )

        # ----------------------------------------------------
        # Размер
        # ----------------------------------------------------

        if not intent.size:
            intent.size = detect_size(normalized)

        # ----------------------------------------------------
        # Цвет
        # ----------------------------------------------------

        if not intent.color:
            intent.color = detect_color(normalized)

        # ----------------------------------------------------
        # Состояние
        # ----------------------------------------------------

        if not intent.condition:
            intent.condition = detect_condition(normalized)

        # ----------------------------------------------------
        # Количество
        # ----------------------------------------------------

        if not intent.quantity:
            intent.quantity = detect_quantity(normalized)

        # ----------------------------------------------------
        # Поисковые запросы
        # ----------------------------------------------------

        intent.search_queries = build_search_queries(
            intent.search_query,
            intent.category,
            intent.brand,
            intent.model,
            intent.color,
            intent.size,
        )

        # ----------------------------------------------------
        # Логирование
        # ----------------------------------------------------

        print("========================================")
        print("SAVVY INTENT")
        print("Original:", intent.original_query)
        print("Product:", intent.product)
        print("Category:", intent.category)
        print("Brand:", intent.brand)
        print("Model:", intent.model)
        print("Color:", intent.color)
        print("Size:", intent.size)
        print("Gender:", intent.gender)
        print("Condition:", intent.condition)
        print("Quantity:", intent.quantity)
        print("Min price:", intent.min_price)
        print("Max price:", intent.max_price)
        print("Currency:", intent.currency)
        print("Product type:", intent.product_type)
        print("Accessory:", intent.accessory_requested)
        print("Attributes:", intent.attributes)
        print("Priorities:", intent.priorities)
        print("Search:", intent.search_query)
        print("Search queries:", intent.search_queries)
        print("Confidence:", intent.confidence)
        print("Parser:", intent.parser)
        print("========================================")

        return intent

    def to_dict(
        self,
        intent: ShoppingIntent,
    ) -> Dict[str, Any]:

        return asdict(intent)


# ============================================================
# УДОБНАЯ ФУНКЦИЯ
# ============================================================

_default_engine: Optional[SavvyIntentEngine] = None


def get_intent_engine() -> SavvyIntentEngine:
    global _default_engine

    if _default_engine is None:
        _default_engine = SavvyIntentEngine()

    return _default_engine


def understand_query(
    query: str,
    preferred_currency: Optional[str] = None,
    destination_country: Optional[str] = None,
) -> ShoppingIntent:

    engine = get_intent_engine()

    return engine.parse(
        query=query,
        preferred_currency=preferred_currency,
        destination_country=destination_country,
    )


# ============================================================
# ЛОКАЛЬНЫЙ ТЕСТ
# ============================================================

if __name__ == "__main__":

    tests = [
        "Мне нужна черная майка поло размер L, цена до 80р",
        "Нужен айфон 15 до 800$",
        "Найди iPhone 15 Pro Max 256GB до 1000 евро",
        "Хочу черные кроссовки Nike 42 размера до 200 BYN",
        "Нужен Samsung Galaxy S24 Ultra новый до 3000 рублей",
        "Найди чехол на iPhone 15 до $30",
        "Нужен ноутбук Lenovo 16 GB RAM до 1000 евро",
        "Хочу телевизор 55 дюймов OLED до 2000 BYN",
    ]

    for query in tests:

        print()
        print()
        print("TEST:", query)

        result = understand_query(query)

        print(
            json.dumps(
                asdict(result),
                ensure_ascii=False,
                indent=2,
            )
        )