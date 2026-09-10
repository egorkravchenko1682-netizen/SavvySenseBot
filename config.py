import os


# =========================
# TELEGRAM
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================
# USER REGION
# =========================

DEFAULT_COUNTRY = os.getenv(
    "DEFAULT_COUNTRY",
    "BY"
)

DEFAULT_CURRENCY = os.getenv(
    "DEFAULT_CURRENCY",
    "BYN"
)


# =========================
# SEARCH
# =========================

MAX_SEARCH_RESULTS = 20

REQUEST_TIMEOUT = 15


# =========================
# SUPPORTED REGIONS
# =========================

SUPPORTED_COUNTRIES = {
    "BY": "Беларусь",
    "RU": "Россия",
    "KZ": "Казахстан",
    "UA": "Украина",

    "PL": "Польша",
    "DE": "Германия",
    "FR": "Франция",
    "IT": "Италия",
    "ES": "Испания",

    "US": "США",
    "GB": "Великобритания",

    "CN": "Китай",
}


# =========================
# MARKETPLACES
# =========================

MARKETPLACES = [
    "wildberries",
    "ozon",
    "yandex_market",
    "megamarket",
    "kaspi",
    "rozetka",

    "aliexpress",
    "1688",
    "taobao",
    "tmall",
    "jd",
    "pinduoduo",

    "amazon",
    "ebay",
    "temu",
    "shein",
    "walmart",
    "etsy",
    "zalando",
]


# =========================
# CURRENCY
# =========================

CURRENCY_SYMBOLS = {
    "BYN": "Br",
    "RUB": "₽",
    "KZT": "₸",
    "UAH": "₴",
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "CNY": "¥",
}


# =========================
# API KEYS
# =========================

EBAY_CLIENT_ID = os.getenv(
    "EBAY_CLIENT_ID"
)

EBAY_CLIENT_SECRET = os.getenv(
    "EBAY_CLIENT_SECRET"
)

AMAZON_ACCESS_KEY = os.getenv(
    "AMAZON_ACCESS_KEY"
)

AMAZON_SECRET_KEY = os.getenv(
    "AMAZON_SECRET_KEY"
)

AMAZON_PARTNER_TAG = os.getenv(
    "AMAZON_PARTNER_TAG"
)