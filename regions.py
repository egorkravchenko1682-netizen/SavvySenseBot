from config import SUPPORTED_COUNTRIES


REGION_MARKETPLACES = {
    "BY": [
        "wildberries",
        "ozon",
        "yandex_market",
        "aliexpress",
        "1688",
        "taobao",
        "amazon",
        "ebay",
        "temu",
    ],

    "RU": [
        "wildberries",
        "ozon",
        "yandex_market",
        "megamarket",
        "aliexpress",
        "1688",
        "taobao",
        "amazon",
        "ebay",
    ],

    "KZ": [
        "kaspi",
        "wildberries",
        "ozon",
        "aliexpress",
        "1688",
        "taobao",
        "amazon",
        "ebay",
    ],

    "UA": [
        "rozetka",
        "aliexpress",
        "ebay",
        "amazon",
        "temu",
    ],

    "PL": [
        "amazon",
        "ebay",
        "aliexpress",
        "temu",
        "zalando",
    ],

    "DE": [
        "amazon",
        "ebay",
        "aliexpress",
        "temu",
        "zalando",
    ],

    "FR": [
        "amazon",
        "ebay",
        "aliexpress",
        "temu",
        "shein",
        "zalando",
    ],

    "US": [
        "amazon",
        "ebay",
        "walmart",
        "etsy",
        "temu",
        "aliexpress",
    ],

    "GB": [
        "amazon",
        "ebay",
        "temu",
        "aliexpress",
        "etsy",
    ],

    "CN": [
        "1688",
        "taobao",
        "tmall",
        "jd",
        "pinduoduo",
        "aliexpress",
    ],
}


def get_marketplaces(country_code: str):
    country_code = country_code.upper()

    if country_code in REGION_MARKETPLACES:
        return REGION_MARKETPLACES[country_code]

    return [
        "amazon",
        "ebay",
        "aliexpress",
        "temu",
    ]


def get_country_name(country_code: str):
    return SUPPORTED_COUNTRIES.get(
        country_code.upper(),
        country_code
    )