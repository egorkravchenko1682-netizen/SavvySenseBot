import re
from urllib.parse import urlparse


def detect_shop(url):
    """
    Определяет магазин по ссылке.
    Возвращает внутреннее имя магазина.
    """

    try:
        hostname = urlparse(url).netloc.lower()
    except Exception:
        return None

    hostname = hostname.replace("www.", "")

    shops = {
        "wildberries": [
            "wildberries.ru",
            "wildberries.by",
        ],
        "ozon": [
            "ozon.ru",
            "ozon.by",
        ],
        "yandex_market": [
            "market.yandex.ru",
            "market.yandex.by",
        ],
        "megamarket": [
            "megamarket.ru",
        ],
        "kaspi": [
            "kaspi.kz",
        ],
        "aliexpress": [
            "aliexpress.com",
            "aliexpress.ru",
        ],
        "amazon": [
            "amazon.com",
            "amazon.de",
            "amazon.fr",
            "amazon.co.uk",
        ],
        "ebay": [
            "ebay.com",
            "ebay.de",
            "ebay.fr",
        ],
        "temu": [
            "temu.com",
        ],
        "shein": [
            "shein.com",
        ],
        "walmart": [
            "walmart.com",
        ],
        "etsy": [
            "etsy.com",
        ],
        "alibaba": [
            "alibaba.com",
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
    }

    for shop_name, domains in shops.items():
        for domain in domains:
            if hostname == domain or hostname.endswith("." + domain):
                return shop_name

    return None


def extract_wildberries_id(url):
    """
    Извлекает артикул Wildberries из ссылки.
    """

    patterns = [
        r"/catalog/(\d+)/detail",
        r"/catalog/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None