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


# ============================================================
# SEARCH QUERY
# ============================================================

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
        self.currency = normalize_currency(currency)

        self.category = category
        self.brand = brand
        self.model = model
        self.color = color
        self.gender = gender
        self.intent = intent


# ============================================================
# GLOBAL SEARCH
# ============================================================

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

    # ========================================================
    # GENERIC PARSED VALUE
    # ========================================================

    def _get_parsed_value(
        self,
        parsed,
        key,
        default=None,
    ):

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

    # ========================================================
    # TEXT NORMALIZATION
    # ========================================================

    def normalize_text(
        self,
        text: Optional[str],
    ) -> str:

        if not text:
            return ""

        text = str(text).lower().strip()

        # Единообразные разделители
        text = text.replace(
            "ё",
            "е",
        )

        text = re.sub(
            r"[_\-]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ========================================================
    # WORD ALIASES
    # ========================================================

    def normalize_aliases(
        self,
        text: Optional[str],
    ) -> str:

        text = self.normalize_text(
            text
        )

        if not text:
            return ""

        aliases = {
            # Apple
            "айфон": "iphone",
            "айфон 15": "iphone 15",
            "айфон 15 про": "iphone 15 pro",
            "айфон 15 про макс": "iphone 15 pro max",

            "айфон 15 pro": "iphone 15 pro",
            "айфон 15 pro max": "iphone 15 pro max",

            "эпл": "apple",

            "айпад": "ipad",
            "макбук": "macbook",
            "эйрподс": "airpods",
            "аирподс": "airpods",

            # Samsung
            "самсунг": "samsung",
            "галакси": "galaxy",
            "самсунг галакси": "samsung galaxy",

            # Xiaomi
            "сяоми": "xiaomi",
            "ксиаоми": "xiaomi",
            "редми": "redmi",

            # Sony
            "сони": "sony",

            # Gaming
            "пс5": "ps5",
            "пс 5": "ps5",
            "плейстейшен": "playstation",

            "пс4": "ps4",
            "пс 4": "ps4",

            "иксбокс": "xbox",

            # Common categories
            "смартфон": "smartphone",
            "телефон": "smartphone",
            "ноут": "laptop",
            "ноутбук": "laptop",
            "наушники": "headphones",
            "телевизор": "tv",
        }

        # Сначала пробуем полное совпадение
        if text in aliases:
            return aliases[text]

        # Затем заменяем отдельные слова
        replacements = {
            "айфон": "iphone",
            "самсунг": "samsung",
            "галакси": "galaxy",
            "сяоми": "xiaomi",
            "ксиаоми": "xiaomi",
            "сони": "sony",
            "макбук": "macbook",
            "айпад": "ipad",
            "эйрподс": "airpods",
            "аирподс": "airpods",
            "пс5": "ps5",
            "пс 5": "ps5",
            "плейстейшен": "playstation",
            "пс4": "ps4",
            "пс 4": "ps4",
            "иксбокс": "xbox",
        }

        words = text.split()

        normalized_words = []

        for word in words:
            normalized_words.append(
                replacements.get(
                    word,
                    word,
                )
            )

        return " ".join(
            normalized_words
        )

    # ========================================================
    # MODEL MATCHING
    # ========================================================

    def model_matches(
        self,
        product_name: str,
        requested_model: str,
    ) -> bool:

        name = self.normalize_aliases(
            product_name
        )

        model = self.normalize_aliases(
            requested_model
        )

        if not model:
            return True

        # ----------------------------------------------------
        # Полное совпадение модели
        # ----------------------------------------------------

        model_parts = model.split()

        if all(
            part in name
            for part in model_parts
        ):
            return True

        # ----------------------------------------------------
        # Специальная логика Apple
        # ----------------------------------------------------

        if model.startswith("iphone"):

            iphone_match = re.search(
                r"\biphone\s+(\d+)",
                model,
            )

            if iphone_match:

                generation = (
                    iphone_match.group(1)
                )

                if (
                    f"iphone {generation}"
                    not in name
                ):
                    return False

                # Если пользователь просит Pro,
                # обычный iPhone не является
                # точным совпадением.
                if "pro max" in model:
                    return (
                        "pro max" in name
                    )

                if "pro" in model:
                    return (
                        "pro" in name
                        and "pro max" not in name
                    )

                # Если запрос обычный iPhone 15,
                # допускаем варианты памяти,
                # цвета и т.п.
                return True

        return False

    # ========================================================
    # CATEGORY MATCHING
    # ========================================================

    def category_matches(
        self,
        product_name: str,
        category: Optional[str],
    ) -> bool:

        if not category:
            return True

        name = self.normalize_aliases(
            product_name
        )

        category_words = {

            "smartphone": [
                "iphone",
                "smartphone",
                "cell phone",
                "mobile phone",
                "android phone",
                "samsung galaxy",
                "xiaomi",
                "redmi",
                "pixel",
                "смартфон",
                "телефон",
            ],

            "laptop": [
                "laptop",
                "notebook",
                "macbook",
                "chromebook",
                "ноутбук",
            ],

            "headphones": [
                "headphones",
                "headset",
                "earbuds",
                "earphones",
                "airpods",
                "наушники",
            ],

            "camera": [
                "camera",
                "digital camera",
                "mirrorless",
                "dslr",
                "фотоаппарат",
                "камера",
            ],

            "tv": [
                "tv",
                "television",
                "smart tv",
                "телевизор",
            ],

            "gaming": [
                "playstation",
                "ps5",
                "ps4",
                "xbox",
                "console",
                "gaming console",
                "игровая приставка",
            ],

            "clothing": [
                "shirt",
                "t-shirt",
                "jacket",
                "coat",
                "dress",
                "hoodie",
                "sweater",
                "pants",
                "jeans",
                "куртка",
                "футболка",
                "рубашка",
                "платье",
                "брюки",
                "джинсы",
                "одежда",
            ],

            "shoes": [
                "shoes",
                "sneakers",
                "boots",
                "trainers",
                "кроссовки",
                "ботинки",
                "обувь",
            ],

            "watch": [
                "watch",
                "smartwatch",
                "часы",
            ],
        }

        words = category_words.get(
            category
        )

        if not words:
            return True

        return any(
            word in name
            for word in words
        )

    # ========================================================
    # ACCESSORY DETECTION
    # ========================================================

    def is_accessory(
        self,
        product_name: str,
    ) -> bool:

        name = self.normalize_text(
            product_name
        )

        # ВАЖНО:
        # "screen" больше НЕ считается
        # автоматически аксессуаром для любого товара.
        #
        # Мы смотрим на смысловые фразы.

        accessory_phrases = [

            "screen replacement",
            "replacement screen",
            "display replacement",
            "replacement display",
            "lcd replacement",
            "oled replacement",

            "screen protector",
            "glass protector",
            "tempered glass",

            "phone case",
            "iphone case",
            "samsung case",

            "charging cable",
            "usb cable",
            "power cable",

            "repair kit",
            "repair tool",

            "replacement battery",
            "replacement part",

            "back glass",
            "rear glass",
            "rear cover",

            "phone housing",
            "replacement housing",

            "digitizer",

            "чехол",
            "защитное стекло",
            "защитная пленка",
            "замена экрана",
            "замена дисплея",
            "дисплей для замены",
            "экран для замены",
            "запчасть",
            "запчасти",
            "ремонтный комплект",
            "заднее стекло",
            "задняя крышка",
            "корпус для",
            "кабель для зарядки",
        ]

        return any(
            phrase in name
            for phrase in accessory_phrases
        )

    # ========================================================
    # BRAND MATCHING
    # ========================================================

    def brand_matches(
        self,
        product_name: str,
        brand: Optional[str],
    ) -> bool:

        if not brand:
            return True

        name = self.normalize_text(
            product_name
        )

        brand = self.normalize_aliases(
            brand
        )

        aliases = {

            "apple": [
                "apple",
                "iphone",
                "ipad",
                "macbook",
                "airpods",
            ],

            "samsung": [
                "samsung",
                "galaxy",
            ],

            "xiaomi": [
                "xiaomi",
                "redmi",
                "poco",
            ],

            "sony": [
                "sony",
            ],

            "google": [
                "google",
                "pixel",
            ],

            "huawei": [
                "huawei",
            ],

            "nike": [
                "nike",
            ],

            "adidas": [
                "adidas",
            ],
        }

        accepted = aliases.get(
            brand,
            [brand],
        )

        return any(
            alias in name
            for alias in accepted
        )

    # ========================================================
    # COLOR MATCHING
    # ========================================================

    def color_matches(
        self,
        product_name: str,
        requested_color: Optional[str],
    ) -> bool:

        if not requested_color:
            return True

        name = self.normalize_text(
            product_name
        )

        color = self.normalize_text(
            requested_color
        )

        aliases = {

            "black": [
                "black",
                "черный",
                "черн",
            ],

            "white": [
                "white",
                "белый",
                "бел",
            ],

            "blue": [
                "blue",
                "синий",
                "син",
            ],

            "red": [
                "red",
                "красный",
                "красн",
            ],

            "green": [
                "green",
                "зеленый",
                "зелен",
            ],

            "pink": [
                "pink",
                "розовый",
                "розов",
            ],

            "gray": [
                "gray",
                "grey",
                "серый",
                "сер",
            ],

            "silver": [
                "silver",
                "серебристый",
            ],

            "gold": [
                "gold",
                "золотой",
            ],
        }

        requested_aliases = aliases.get(
            color,
            [color],
        )

        all_colors = []

        for values in aliases.values():
            all_colors.extend(
                values
            )

        # Если магазин вообще НЕ указал цвет,
        # не отбрасываем товар.
        has_color = any(
            value in name
            for value in all_colors
        )

        if not has_color:
            return True

        return any(
            value in name
            for value in requested_aliases
        )

    # ========================================================
    # PARSE QUERY
    # ========================================================

    def parse_query(
        self,
        text: str,
    ) -> SearchQuery:

        original = text.strip()

        max_price = None
        currency = None

        price_patterns = [

            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
                r"\s*\$?\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
                r"\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
                r"\s*([\d\s.,]+)\s*(?:USD|доллар(?:а|ов)?)\b",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
                r"\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
                r"\s*([\d\s.,]+)\s*(?:EUR|евро)\b",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*RUB\b",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:руб(?:лей|ля)?)\b",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*BYN\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*белорусских\s+руб(?:лей|ля)?",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*р\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:PLN|злотых|злот)\b",
                "PLN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:GBP|фунтов?|£)",
                "GBP",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:KZT|тенге|₸)",
                "KZT",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:UAH|гривен?|₴)",
                "UAH",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:CNY|юаней?|¥)",
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

        if currency is None:

            currency = detect_currency_from_text(
                original
            )

        # ----------------------------------------------------
        # ОЧИСТКА ЗАПРОСА
        # ----------------------------------------------------

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
        ]

        for pattern in cleanup_patterns:

            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        # ----------------------------------------------------
        # УДАЛЯЕМ БЮДЖЕТ
        # ----------------------------------------------------

        budget_patterns = [

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
            r"\s*\$?\s*[\d\s.,]+\s*\$",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
            r"\s*\$\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
            r"\s*€\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более|under|below)"
            r"\s*[\d\s.,]+\s*"
            r"(?:USD|EUR|GBP|RUB|BYN|PLN|KZT|UAH|CNY|"
            r"доллар(?:а|ов)?|евро|руб(?:лей|ля)?|"
            r"белорусских\s+рублей|российских\s+рублей|"
            r"злотых|фунтов?|тенге|гривен?|юаней?)",

            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\d\s.,]+\s*(?:\$|€|£|₽|₸|₴|¥|р\b)",
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

    # ========================================================
    # PRODUCT FROM LINK
    # ========================================================

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

    # ========================================================
    # GLOBAL SEARCH
    # ========================================================

    def search_everywhere(
        self,
        query: str,
    ) -> List[Product]:

        parsed = self.parse_query(
            query
        )

        # ----------------------------------------------------
        # AI PARSER
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # NORMALIZE AI DATA
        # ----------------------------------------------------

        parsed.brand = (
            self.normalize_aliases(
                parsed.brand
            )
            if parsed.brand
            else None
        )

        parsed.model = (
            self.normalize_aliases(
                parsed.model
            )
            if parsed.model
            else None
        )

        # ----------------------------------------------------
        # ЛОГ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        results = []

        for adapter in self.adapters:

            try:

                products = adapter.search(
                    parsed.query
                )

                print(
                    f"{adapter.shop_name}:",
                    len(products),
                    "raw results",
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

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        filtered = self.remove_bad_results(
            results,
            parsed,
        )

        print(
            "RESULTS AFTER FILTER:",
            len(filtered),
        )

        # ----------------------------------------------------
        # DEDUP
        # ----------------------------------------------------

        filtered = self.remove_duplicates(
            filtered
        )

        print(
            "RESULTS AFTER DEDUP:",
            len(filtered),
        )

        # ----------------------------------------------------
        # RANK
        # ----------------------------------------------------

        return self.rank_results(
            filtered,
            parsed,
        )

    # ========================================================
    # FILTER
    # ========================================================

    def remove_bad_results(
        self,
        products,
        parsed,
    ):

        clean_results = []

        rejected = {
            "empty_name": 0,
            "bad_page": 0,
            "accessory": 0,
            "category": 0,
            "brand": 0,
            "model": 0,
            "color": 0,
            "budget": 0,
            "price": 0,
        }

        bad_words = [

            "категория",
            "catalog",
            "каталог",
            "статья",
            "обзор",
            "сравнение",
            "новости",
            "wikipedia",
        ]

        for product in products:

            if not product.name:

                rejected[
                    "empty_name"
                ] += 1

                continue

            name = self.normalize_text(
                product.name
            )

            # ------------------------------------------------
            # BAD PAGES
            # ------------------------------------------------

            if any(
                word in name
                for word in bad_words
            ):

                rejected[
                    "bad_page"
                ] += 1

                continue

            # ------------------------------------------------
            # ACCESSORIES
            # ------------------------------------------------

            if (
                parsed.category
                in {
                    "smartphone",
                    "laptop",
                    "camera",
                    "tv",
                    "gaming",
                }
            ):

                if self.is_accessory(
                    name
                ):

                    rejected[
                        "accessory"
                    ] += 1

                    continue

            # ------------------------------------------------
            # CATEGORY
            # ------------------------------------------------

            if not self.category_matches(
                name,
                parsed.category,
            ):

                rejected[
                    "category"
                ] += 1

                continue

            # ------------------------------------------------
            # BRAND
            # ------------------------------------------------

            if not self.brand_matches(
                name,
                parsed.brand,
            ):

                rejected[
                    "brand"
                ] += 1

                continue

            # ------------------------------------------------
            # MODEL
            # ------------------------------------------------

            if not self.model_matches(
                name,
                parsed.model,
            ):

                rejected[
                    "model"
                ] += 1

                continue

            # ------------------------------------------------
            # COLOR
            # ------------------------------------------------

            if not self.color_matches(
                name,
                parsed.color,
            ):

                rejected[
                    "color"
                ] += 1

                continue

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            if product.price is not None:

                try:

                    product.price = float(
                        product.price
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    product.price = None

            if (
                product.price is not None
                and product.price <= 0
            ):

                rejected[
                    "price"
                ] += 1

                continue

            if (
                product.price is not None
                and product.price > 50000000
            ):

                rejected[
                    "price"
                ] += 1

                continue

            # ------------------------------------------------
            # SUSPICIOUSLY CHEAP
            # ------------------------------------------------

            if (
                product.price is not None
                and product.price < 10
            ):

                suspicious_product_words = [

                    "iphone",
                    "apple",
                    "samsung",
                    "galaxy",
                    "pixel",
                    "macbook",
                    "playstation",
                    "xbox",
                    "sony",
                    "smartphone",
                    "смартфон",
                    "телефон",
                    "laptop",
                    "ноутбук",
                    "television",
                    "телевизор",
                ]

                if any(
                    word in name
                    for word
                    in suspicious_product_words
                ):

                    rejected[
                        "price"
                    ] += 1

                    continue

            # ------------------------------------------------
            # BUDGET
            # ------------------------------------------------

            if (
                parsed.max_price is not None
                and parsed.currency
            ):

                if (
                    product.price is None
                    or not product.currency
                ):

                    rejected[
                        "budget"
                    ] += 1

                    continue

                product_currency = (
                    normalize_currency(
                        product.currency
                    )
                )

                budget_currency = (
                    normalize_currency(
                        parsed.currency
                    )
                )

                if (
                    not product_currency
                    or not budget_currency
                ):

                    rejected[
                        "budget"
                    ] += 1

                    continue

                # ------------------------------------------------
                # SAME CURRENCY
                # ------------------------------------------------

                if (
                    product_currency
                    == budget_currency
                ):

                    converted_price = (
                        product.price
                    )

                else:

                    converted_price = (
                        convert_to_budget_currency(
                            product.price,
                            product_currency,
                            budget_currency,
                        )
                    )

                if converted_price is None:

                    rejected[
                        "budget"
                    ] += 1

                    continue

                print(
                    "BUDGET CHECK:",
                    product.name,
                    "|",
                    product.price,
                    product_currency,
                    "=>",
                    round(
                        converted_price,
                        2,
                    ),
                    budget_currency,
                    "| LIMIT:",
                    parsed.max_price,
                )

                if (
                    converted_price
                    > parsed.max_price
                ):

                    rejected[
                        "budget"
                    ] += 1

                    continue

            # ------------------------------------------------
            # ACCEPT
            # ------------------------------------------------

            clean_results.append(
                product
            )

        print(
            "FILTER REJECTED:",
            rejected,
        )

        return clean_results

    # ========================================================
    # DUPLICATES
    # ========================================================

    def remove_duplicates(
        self,
        products,
    ):

        unique = []
        seen = set()

        for product in products:

            key = (
                product.shop.lower(),
                self.normalize_text(
                    product.name
                ),
                round(
                    float(product.price),
                    2,
                )
                if product.price is not None
                else None,
                normalize_currency(
                    product.currency
                ),
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                product
            )

        return unique

    # ========================================================
    # RANKING
    # ========================================================

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

            # ------------------------------------------------
            # PRICE EXISTS
            # ------------------------------------------------

            if product.price is not None:
                score += 5

            # ------------------------------------------------
            # EXACT MATCH
            # ------------------------------------------------

            if product.is_exact_match:
                score += 10

            # ------------------------------------------------
            # BUDGET VALUE
            # ------------------------------------------------

            if (
                parsed
                and parsed.max_price is not None
                and parsed.currency
                and product.price is not None
                and product.currency
            ):

                product_currency = (
                    normalize_currency(
                        product.currency
                    )
                )

                budget_currency = (
                    normalize_currency(
                        parsed.currency
                    )
                )

                if (
                    product_currency
                    == budget_currency
                ):

                    converted_price = (
                        product.price
                    )

                else:

                    converted_price = (
                        convert_to_budget_currency(
                            product.price,
                            product_currency,
                            budget_currency,
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
                int(score),
                100,
            )

            scored_products.append(
                (
                    score,
                    product,
                )
            )

        # ----------------------------------------------------
        # BEST SCORE FIRST
        # ----------------------------------------------------

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