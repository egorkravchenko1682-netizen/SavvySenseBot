import re
from typing import List, Optional

from products import Product
from deal_score import calculate_deal_score

from adapters.base import ShopAdapter

from adapters.wildberries import WildberriesAdapter
from adapters.ozon import OzonAdapter
from adapters.amazon import AmazonAdapter
from adapters.aliexpress import AliExpressAdapter
from adapters.temu import TemuAdapter
from adapters.taobao import TaobaoAdapter
from adapters.jd import JdAdapter
from adapters.walmart import WalmartAdapter
from adapters.web_search import WebSearchAdapter
from adapters.ebay_api import EbayApiAdapter

from ai_parser import parse_user_request

from currency import (
    normalize_currency,
    detect_currency_from_text,
    convert_to_budget_currency,
)


class SearchQuery:

    def __init__(
        self,
        query: str,
        max_price: Optional[float] = None,
        currency: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        color: Optional[str] = None,
        gender: Optional[str] = None,
        intent: Optional[str] = None,
    ):
        self.query = query
        self.max_price = max_price
        self.currency = normalize_currency(
            currency
        )

        self.category = category
        self.brand = brand
        self.model = model
        self.color = color
        self.gender = gender
        self.intent = intent


class GlobalSearch:

    def __init__(self):

        self.adapters: List[ShopAdapter] = [
            WildberriesAdapter(),
            OzonAdapter(),
            AmazonAdapter(),
            AliExpressAdapter(),
            EbayApiAdapter(),
            TemuAdapter(),
            TaobaoAdapter(),
            JdAdapter(),
            WalmartAdapter(),
            WebSearchAdapter(),
        ]

    # ---------------------------------------------------------
    # ВСПОМОГАТЕЛЬНОЕ ПОЛУЧЕНИЕ ДАННЫХ AI PARSER
    # ---------------------------------------------------------

    def _get_parsed_value(
        self,
        parsed,
        key,
        default=None,
    ):
        """
        Работает и с dict, и с объектом,
        если структура ai_parser позже изменится.
        """

        if parsed is None:
            return default

        if isinstance(parsed, dict):
            return parsed.get(
                key,
                default,
            )

        return getattr(
            parsed,
            key,
            default,
        )

    # ---------------------------------------------------------
    # ПАРСИНГ ЗАПРОСА
    # ---------------------------------------------------------

    def parse_query(
        self,
        text: str,
    ) -> SearchQuery:

        original = text.strip()

        max_price = None
        currency = None

        price_patterns = [

            # ДО 500$
            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*\$?\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            # ДО $500
            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            # ДО 500 USD
            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*([\d\s.,]+)\s*(?:USD|доллар(?:а|ов)?)\b",
                "USD",
            ),

            # ДО 500€
            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            # ДО 500 EUR
            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*([\d\s.,]+)\s*(?:EUR|евро)\b",
                "EUR",
            ),

            # ДО 500₽
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            # ДО 500 RUB
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*RUB\b",
                "RUB",
            ),

            # ДО 500 рублей
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:российских\s+рублей|руб(?:лей|ля))\b",
                "RUB",
            ),

            # ДО 500 BYN
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*BYN\b",
                "BYN",
            ),

            # ДО 500 белорусских рублей
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*белорусских\s+руб(?:лей|ля)?",
                "BYN",
            ),

            # ДО 500 р
            #
            # ВАЖНО:
            # одиночная "р" трактуется как BYN,
            # поскольку бот ориентирован на Беларусь.
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*р\b",
                "BYN",
            ),

            # ДО 500 PLN
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:PLN|злотых|злот)\b",
                "PLN",
            ),

            # ДО 500 GBP
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:GBP|фунтов?|£)",
                "GBP",
            ),

            # ДО 500 KZT
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:KZT|тенге|₸)",
                "KZT",
            ),

            # ДО 500 UAH
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:UAH|гривен?|₴)",
                "UAH",
            ),

            # ДО 500 CNY
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:CNY|юаней?|¥)",
                "CNY",
            ),
        ]

        for pattern, detected_currency in price_patterns:

            match = re.search(
                pattern,
                original,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            raw_price = (
                match.group(1)
                .replace(" ", "")
                .replace(",", ".")
            )

            try:
                max_price = float(
                    raw_price
                )

                currency = detected_currency

                break

            except ValueError:
                pass

        # -----------------------------------------------------
        # ЕСЛИ ЯВНЫЙ ПАТТЕРН НЕ НАШЁЛ ВАЛЮТУ
        # ПЫТАЕМСЯ ОПРЕДЕЛИТЬ ЕЁ ПО ТЕКСТУ
        # -----------------------------------------------------

        if currency is None:
            currency = detect_currency_from_text(
                original
            )

        # -----------------------------------------------------
        # ОЧИЩАЕМ ПОИСКОВЫЙ ЗАПРОС
        # -----------------------------------------------------

        cleaned = original

        cleanup_patterns = [
            r"\bмне\s+нужен\b",
            r"\bмне\s+нужна\b",
            r"\bмне\s+нужно\b",
            r"\bнужен\b",
            r"\bнужна\b",
            r"\bнужно\b",
            r"\bхочу\b",
            r"\bхотел\s+бы\b",
            r"\bхотела\s+бы\b",
            r"\bкупить\b",
            r"\bнайди\b",
            r"\bпоищи\b",
            r"\bищу\b",
            r"\bподбери\b",
            r"\bпосоветуй\b",
            r"\bпокажи\b",
            r"\bнайти\b",
            r"\bнужен\s+мне\b",
        ]

        for pattern in cleanup_patterns:

            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        # -----------------------------------------------------
        # УДАЛЯЕМ БЮДЖЕТ ИЗ QUERY
        # -----------------------------------------------------

        budget_patterns = [

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*\$?\s*[\d\s.,]+\s*\$",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*\$\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*€\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)\s*[\d\s.,]+\s*(?:USD|EUR|GBP|RUB|BYN|PLN|KZT|UAH|CNY|доллар(?:а|ов)?|евро|руб(?:лей|ля)?|белорусских\s+рублей|российских\s+рублей|злотых|фунтов?|тенге|гривен?|юаней?)",

            r"(?:до|не\s+дороже|максимум|не\s+более)\s*[\d\s.,]+\s*(?:\$|€|£|₽|₸|₴|¥|р\b)",
        ]

        for pattern in budget_patterns:

            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        return SearchQuery(
            query=cleaned,
            max_price=max_price,
            currency=currency,
        )

    # ---------------------------------------------------------
    # ПОЛУЧЕНИЕ ТОВАРА ПО ССЫЛКЕ
    # ---------------------------------------------------------

    def get_product_from_link(
        self,
        url: str,
    ) -> Optional[Product]:

        for adapter in self.adapters:

            try:

                if adapter.can_handle(url):

                    product = adapter.get_product(
                        url
                    )

                    if product:
                        product.is_exact_match = True

                    return product

            except Exception as e:

                print(
                    f"{adapter.shop_name} link error:",
                    e,
                )

        return None

    # ---------------------------------------------------------
    # ГЛОБАЛЬНЫЙ ПОИСК
    # ---------------------------------------------------------

    def search_everywhere(
        self,
        query: str,
    ) -> List[Product]:

        parsed = self.parse_query(
            query
        )

        # -----------------------------------------------------
        # AI АНАЛИЗ ЗАПРОСА
        # -----------------------------------------------------

        try:

            ai_parsed = parse_user_request(
                query
            )

            parsed.category = self._get_parsed_value(
                ai_parsed,
                "category",
            )

            parsed.brand = self._get_parsed_value(
                ai_parsed,
                "brand",
            )

            parsed.model = self._get_parsed_value(
                ai_parsed,
                "model",
            )

            parsed.color = self._get_parsed_value(
                ai_parsed,
                "color",
            )

            parsed.gender = self._get_parsed_value(
                ai_parsed,
                "gender",
            )

            parsed.intent = self._get_parsed_value(
                ai_parsed,
                "intent",
            )

            ai_budget = self._get_parsed_value(
                ai_parsed,
                "budget",
            )

            ai_currency = self._get_parsed_value(
                ai_parsed,
                "currency",
            )

            # Если AI определил бюджет,
            # используем его.
            if (
                parsed.max_price is None
                and ai_budget is not None
            ):
                try:
                    parsed.max_price = float(
                        ai_budget
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            # Если AI определил валюту,
            # используем её.
            normalized_ai_currency = normalize_currency(
                ai_currency
            )

            if normalized_ai_currency:
                parsed.currency = (
                    normalized_ai_currency
                )

        except Exception as e:

            print(
                "AI parser error:",
                e,
            )

        print(
            "================================="
        )

        print(
            "SAVVY QUERY:",
            parsed.query,
        )

        print(
            "MAX PRICE:",
            parsed.max_price,
        )

        print(
            "CURRENCY:",
            parsed.currency,
        )

        print(
            "CATEGORY:",
            parsed.category,
        )

        print(
            "BRAND:",
            parsed.brand,
        )

        print(
            "MODEL:",
            parsed.model,
        )

        print(
            "COLOR:",
            parsed.color,
        )

        print(
            "GENDER:",
            parsed.gender,
        )

        print(
            "INTENT:",
            parsed.intent,
        )

        print(
            "================================="
        )

        # -----------------------------------------------------
        # ПОИСК ПО МАГАЗИНАМ
        # -----------------------------------------------------

        results = []

        for adapter in self.adapters:

            try:

                products = adapter.search(
                    parsed.query
                )

                if products:

                    results.extend(
                        products
                    )

            except Exception as e:

                print(
                    f"{adapter.shop_name} search error:",
                    e,
                )

        print(
            "TOTAL RAW RESULTS:",
            len(results),
        )

        # -----------------------------------------------------
        # ФИЛЬТРАЦИЯ
        # -----------------------------------------------------

        results = self.remove_bad_results(
            results,
            parsed,
        )

        print(
            "RESULTS AFTER FILTER:",
            len(results),
        )

        # -----------------------------------------------------
        # ДУБЛИКАТЫ
        # -----------------------------------------------------

        results = self.remove_duplicates(
            results
        )

        print(
            "RESULTS AFTER DEDUP:",
            len(results),
        )

        # -----------------------------------------------------
        # РАНЖИРОВАНИЕ
        # -----------------------------------------------------

        return self.rank_results(
            results,
            parsed,
        )

    # ---------------------------------------------------------
    # ФИЛЬТРАЦИЯ
    # ---------------------------------------------------------

    def remove_bad_results(
        self,
        products,
        parsed,
    ):

        clean_results = []

        # -----------------------------------------------------
        # СЛОВА, КОТОРЫЕ ОЗНАЧАЮТ АКСЕССУАРЫ / ЗАПЧАСТИ
        # -----------------------------------------------------

        accessory_words = [

            "case",
            "cover",
            "screen",
            "display",
            "digitizer",
            "replacement",
            "repair",
            "repair kit",
            "battery",
            "charger",
            "charging cable",
            "cable",
            "adapter",
            "glass",
            "back glass",
            "rear cover",
            "housing",
            "frame",
            "protector",
            "screen protector",
            "earpods",
            "airpods",
            "headphones",
            "earbuds",

            "чехол",
            "стекло",
            "экран",
            "дисплей",
            "тачскрин",
            "запчасть",
            "запчасти",
            "замена",
            "ремонт",
            "ремонтный комплект",
            "зарядка",
            "кабель",
            "адаптер",
            "защитное стекло",
            "наушники",
            "крышка",
            "корпус",
            "рамка",
        ]

        bad_words = [

            "категория",
            "catalog",
            "каталог",
            "статья",
            "обзор",
            "сравнение",
            "новости",
            "wiki",
            "wikipedia",
        ]

        # -----------------------------------------------------
        # КАТЕГОРИИ
        # -----------------------------------------------------

        smartphone_words = [
            "iphone",
            "smartphone",
            "cell phone",
            "mobile phone",
            "смартфон",
            "телефон",
        ]

        laptop_words = [
            "laptop",
            "notebook",
            "macbook",
            "chromebook",
            "ноутбук",
        ]

        headphone_words = [
            "headphones",
            "headset",
            "earbuds",
            "earphones",
            "наушники",
        ]

        camera_words = [
            "camera",
            "digital camera",
            "mirrorless",
            "dslr",
            "фотоаппарат",
            "камера",
        ]

        tv_words = [
            "tv",
            "television",
            "телевизор",
        ]

        gaming_words = [
            "playstation",
            "ps5",
            "ps4",
            "xbox",
            "console",
            "игровая приставка",
        ]

        for product in products:

            if not product.name:
                continue

            name = product.name.lower().strip()

            # -------------------------------------------------
            # ОБЩАЯ ПРОВЕРКА
            # -------------------------------------------------

            if any(
                word in name
                for word in bad_words
            ):
                continue

            # -------------------------------------------------
            # ЕСЛИ МЫ ИЩЕМ СМАРТФОН
            # -------------------------------------------------

            if parsed.category == "smartphone":

                # Запрещаем аксессуары
                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

                # Сам товар должен быть смартфоном
                if not any(
                    word in name
                    for word in smartphone_words
                ):
                    continue

            # -------------------------------------------------
            # НОУТБУК
            # -------------------------------------------------

            if parsed.category == "laptop":

                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

                if not any(
                    word in name
                    for word in laptop_words
                ):
                    continue

            # -------------------------------------------------
            # НАУШНИКИ
            # -------------------------------------------------

            if parsed.category == "headphones":

                if not any(
                    word in name
                    for word in headphone_words
                ):
                    continue

            # -------------------------------------------------
            # КАМЕРА
            # -------------------------------------------------

            if parsed.category == "camera":

                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

                if not any(
                    word in name
                    for word in camera_words
                ):
                    continue

            # -------------------------------------------------
            # TV
            # -------------------------------------------------

            if parsed.category == "tv":

                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

                if not any(
                    word in name
                    for word in tv_words
                ):
                    continue

            # -------------------------------------------------
            # GAMING
            # -------------------------------------------------

            if parsed.category == "gaming":

                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

                if not any(
                    word in name
                    for word in gaming_words
                ):
                    continue

            # -------------------------------------------------
            # БРЕНД
            # -------------------------------------------------

            if parsed.brand:

                brand = str(
                    parsed.brand
                ).lower()

                if brand not in name:

                    # Небольшие исключения
                    brand_aliases = {

                        "apple": [
                            "apple",
                            "iphone",
                            "macbook",
                            "airpods",
                        ],

                        "samsung": [
                            "samsung",
                            "galaxy",
                        ],

                        "sony": [
                            "sony",
                        ],

                        "xiaomi": [
                            "xiaomi",
                            "redmi",
                            "poco",
                        ],
                    }

                    aliases = (
                        brand_aliases.get(
                            brand,
                            [brand],
                        )
                    )

                    if not any(
                        alias in name
                        for alias in aliases
                    ):
                        continue

            # -------------------------------------------------
            # МОДЕЛЬ
            # -------------------------------------------------

            if parsed.model:

                model = str(
                    parsed.model
                ).lower()

                # Для моделей типа iPhone 15
                # проверяем составляющие,
                # чтобы "iPhone 15 Pro" тоже проходил.
                model_parts = model.split()

                if not all(
                    part in name
                    for part in model_parts
                ):
                    continue

            # -------------------------------------------------
            # ЦВЕТ
            # -------------------------------------------------

            if parsed.color:

                color = str(
                    parsed.color
                ).lower()

                color_aliases = {
                    "black": [
                        "black",
                        "черн",
                    ],
                    "white": [
                        "white",
                        "бел",
                    ],
                    "blue": [
                        "blue",
                        "син",
                    ],
                    "red": [
                        "red",
                        "крас",
                    ],
                    "green": [
                        "green",
                        "зелен",
                    ],
                    "pink": [
                        "pink",
                        "розов",
                    ],
                }

                aliases = color_aliases.get(
                    color,
                    [color],
                )

                # Цвет не всегда указан в названии.
                # Поэтому НЕ отбрасываем товар,
                # если магазин не указал цвет.
                #
                # Но если цвет явно указан,
                # проверяем его.
                has_known_color = any(
                    color_word in name
                    for values in color_aliases.values()
                    for color_word in values
                )

                if has_known_color:

                    if not any(
                        alias in name
                        for alias in aliases
                    ):
                        continue

            # -------------------------------------------------
            # БЮДЖЕТ
            # -------------------------------------------------

            if (
                parsed.max_price is not None
                and parsed.currency
            ):

                if (
                    product.price is None
                    or not product.currency
                ):
                    # Без цены невозможно проверить бюджет.
                    continue

                converted_price = (
                    convert_to_budget_currency(
                        product.price,
                        product.currency,
                        parsed.currency,
                    )
                )

                if converted_price is None:
                    continue

                print(
                    "PRICE:",
                    product.price,
                    product.currency,
                    "=>",
                    round(
                        converted_price,
                        2,
                    ),
                    parsed.currency,
                )

                if (
                    converted_price
                    > parsed.max_price
                ):
                    continue

            # -------------------------------------------------
            # ПРОВЕРКА ЦЕНЫ
            # -------------------------------------------------

            if product.price is not None:

                if product.price <= 0:
                    continue

                # Подозрительно маленькая цена
                suspicious_words = [
                    "iphone",
                    "apple",
                    "samsung",
                    "galaxy",
                    "pixel",
                    "macbook",
                    "playstation",
                    "xbox",
                    "sony",
                    "смартфон",
                    "телефон",
                    "ноутбук",
                    "телевизор",
                    "tv",
                ]

                if (
                    product.price < 10
                    and any(
                        word in name
                        for word in suspicious_words
                    )
                ):
                    continue

                if product.price > 50000000:
                    continue

            clean_results.append(
                product
            )

        return clean_results

    # ---------------------------------------------------------
    # ДУБЛИКАТЫ
    # ---------------------------------------------------------

    def remove_duplicates(
        self,
        products,
    ):

        unique = []
        seen = set()

        for product in products:

            key = (
                product.shop.lower(),
                product.name.lower().strip(),
                product.price,
                product.currency,
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(
                product
            )

        return unique

    # ---------------------------------------------------------
    # РЕЙТИНГ
    # ---------------------------------------------------------

    def rank_results(
        self,
        products,
        parsed=None,
    ):

        scored_products = []

        for product in products:

            score = calculate_deal_score(
                product
            )

            # Есть цена
            if product.price is not None:
                score += 5

            # Это точное совпадение
            if product.is_exact_match:
                score += 10

            # -------------------------------------------------
            # ЦЕНА ОТНОСИТЕЛЬНО БЮДЖЕТА
            # -------------------------------------------------

            if (
                parsed
                and parsed.max_price is not None
                and parsed.currency
                and product.price is not None
                and product.currency
            ):

                converted_price = (
                    convert_to_budget_currency(
                        product.price,
                        product.currency,
                        parsed.currency,
                    )
                )

                if converted_price is not None:

                    percentage = (
                        converted_price
                        / parsed.max_price
                    )

                    if percentage <= 0.50:
                        score += 15

                    elif percentage <= 0.70:
                        score += 10

                    elif percentage <= 0.85:
                        score += 5

            score = min(
                score,
                100,
            )

            scored_products.append(
                (
                    score,
                    product,
                )
            )

        # Сначала лучший score,
        # при одинаковом score — более дешёвый товар.
        scored_products.sort(
            key=lambda item: (
                item[0],
                -(
                    item[1].price
                    if item[1].price is not None
                    else 999999999
                ),
            ),
            reverse=True,
        )

        return [
            product
            for score, product
            in scored_products
        ]