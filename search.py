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

from currency import (
    normalize_currency,
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
    ):
        self.query = query
        self.max_price = max_price
        self.currency = normalize_currency(currency)
        self.category = category
        self.brand = brand
        self.model = model


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
    # PARSE QUERY
    # ---------------------------------------------------------

    def parse_query(self, text: str) -> SearchQuery:

        original = text.strip()

        max_price = None
        currency = None

        price_patterns = [

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*р\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:руб(?:лей|ля)?|белорусских\s+рублей)",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*BYN\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:USD|доллар(?:а|ов)?)\b",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*€",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:EUR|евро)\b",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:российских\s+рублей)",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*RUB\b",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)\s*([\d\s.,]+)\s*(?:PLN|злотых|злот)\b",
                "PLN",
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

                max_price = float(raw_price)
                currency = detected_currency

                break

            except ValueError:
                pass

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
        ]

        for pattern in cleanup_patterns:

            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        budget_patterns = [

            r"(?:до|не\s+дороже|максимум|не\s+более)\s*[\$€]\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более)\s*[\d\s.,]+\s*(?:\$|€|₽|р\b)",

            r"(?:до|не\s+дороже|максимум|не\s+более)\s*[\d\s.,]+\s*(?:BYN|USD|EUR|RUB|PLN|доллар(?:а|ов)?|евро|руб(?:лей|ля)?|российских\s+рублей|белорусских\s+рублей|злотых|злот)",
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
    # PRODUCT FROM LINK
    # ---------------------------------------------------------

    def get_product_from_link(
        self,
        url: str,
    ) -> Product | None:

        for adapter in self.adapters:

            try:

                if adapter.can_handle(url):

                    product = adapter.get_product(url)

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
    # GLOBAL SEARCH
    # ---------------------------------------------------------

    def search_everywhere(
        self,
        query: str,
    ) -> List[Product]:

        parsed = self.parse_query(query)

        print(
            "SAVVY QUERY:",
            parsed.query,
            "MAX PRICE:",
            parsed.max_price,
            "CURRENCY:",
            parsed.currency,
        )

        results = []

        for adapter in self.adapters:

            try:

                products = adapter.search(
                    parsed.query
                )

                if products:

                    results.extend(products)

            except Exception as e:

                print(
                    f"{adapter.shop_name} search error:",
                    e,
                )

        print(
            "TOTAL RAW RESULTS:",
            len(results),
        )

        results = self.remove_bad_results(
            results,
            parsed,
        )

        print(
            "RESULTS AFTER FILTER:",
            len(results),
        )

        results = self.remove_duplicates(
            results
        )

        print(
            "RESULTS AFTER DEDUP:",
            len(results),
        )

        return self.rank_results(
            results,
            parsed,
        )

    # ---------------------------------------------------------
    # FILTER RESULTS
    # ---------------------------------------------------------

    def remove_bad_results(
        self,
        products,
        parsed,
    ):

        clean_results = []

        accessory_words = [

            # English
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

            # Russian
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

        main_product_categories = [

            "smartphone",
            "laptop",
            "headphones",
            "tv",
            "camera",
            "gaming",
        ]

        for product in products:

            if not product.name:
                continue

            name = product.name.lower().strip()

            # ---------------------------------------------
            # Убираем информационный мусор
            # ---------------------------------------------

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

            if any(
                word in name
                for word in bad_words
            ):
                continue

            # ---------------------------------------------
            # Убираем аксессуары и запчасти
            # ---------------------------------------------

            if parsed.category in main_product_categories:

                if any(
                    word in name
                    for word in accessory_words
                ):
                    continue

            # ---------------------------------------------
            # SMARTPHONE
            # ---------------------------------------------

            if parsed.category == "smartphone":

                smartphone_words = [

                    "iphone",
                    "smartphone",
                    "cell phone",
                    "mobile phone",
                    "смартфон",
                    "телефон",
                ]

                if not any(
                    word in name
                    for word in smartphone_words
                ):
                    continue

            # ---------------------------------------------
            # LAPTOP
            # ---------------------------------------------

            if parsed.category == "laptop":

                laptop_words = [

                    "laptop",
                    "notebook",
                    "macbook",
                    "chromebook",
                    "ноутбук",
                ]

                if not any(
                    word in name
                    for word in laptop_words
                ):
                    continue

            # ---------------------------------------------
            # HEADPHONES
            # ---------------------------------------------

            if parsed.category == "headphones":

                headphone_words = [

                    "headphones",
                    "headset",
                    "earbuds",
                    "earphones",
                    "наушники",
                ]

                if not any(
                    word in name
                    for word in headphone_words
                ):
                    continue

            # ---------------------------------------------
            # CAMERA
            # ---------------------------------------------

            if parsed.category == "camera":

                camera_words = [

                    "camera",
                    "digital camera",
                    "mirrorless",
                    "dslr",
                    "фотоаппарат",
                    "камера",
                ]

                if not any(
                    word in name
                    for word in camera_words
                ):
                    continue

            # ---------------------------------------------
            # MODEL
            # ---------------------------------------------

            if parsed.model:

                model = parsed.model.lower()

                if model not in name:
                    continue

            # ---------------------------------------------
            # BRAND
            # ---------------------------------------------

            if parsed.brand:

                brand = parsed.brand.lower()

                if brand not in name:
                    continue

            # ---------------------------------------------
            # BUDGET
            # ---------------------------------------------

            if (
                parsed.max_price is not None
                and parsed.currency
                and product.price is not None
                and product.currency
            ):

                converted_price = convert_to_budget_currency(

                    product.price,
                    product.currency,
                    parsed.currency,
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

                if converted_price > parsed.max_price:
                    continue

            # ---------------------------------------------
            # PRICE SANITY CHECK
            # ---------------------------------------------

            if product.price is not None:

                if product.price <= 0:
                    continue

                expensive_keywords = [

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
                        for word in expensive_keywords
                    )
                ):
                    continue

                if product.price > 50000000:
                    continue

            clean_results.append(product)

        return clean_results

    # ---------------------------------------------------------
    # REMOVE DUPLICATES
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

            unique.append(product)

        return unique

    # ---------------------------------------------------------
    # RANK RESULTS
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

            # Точное совпадение
            if product.is_exact_match:
                score += 10

            # Выгодность относительно бюджета
            if (
                parsed
                and parsed.max_price
                and product.price
                and product.currency
                and parsed.currency
            ):

                converted_price = convert_to_budget_currency(

                    product.price,
                    product.currency,
                    parsed.currency,
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

        scored_products.sort(

            key=lambda item: (
                item[0],
                -(item[1].price or 999999999),
            ),

            reverse=True,
        )

        return [
            product
            for score, product
            in scored_products
        ]