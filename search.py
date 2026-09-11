import re
from typing import List, Optional

from products import Product
from deal_score import calculate_deal_score

from adapters.base import ShopAdapter

from adapters.wildberries import WildberriesAdapter
from adapters.ozon import OzonAdapter
from adapters.amazon import AmazonAdapter
from adapters.aliexpress import AliExpressAdapter
from adapters.ebay_api import EbayApiAdapter
from adapters.temu import TemuAdapter
from adapters.taobao import TaobaoAdapter
from adapters.jd import JdAdapter
from adapters.walmart import WalmartAdapter
from adapters.web_search import WebSearchAdapter

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
    ):
        self.query = query
        self.max_price = max_price
        self.currency = normalize_currency(currency)


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

    def parse_query(self, text: str) -> SearchQuery:

        original = text.strip()

        max_price = None
        currency = None

        price_patterns = [

            # BYN
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*р\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:руб(?:лей|ля)?|белорусских\s+рублей)",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*BYN\b",
                "BYN",
            ),

            # USD
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:USD|доллар(?:а|ов)?)\b",
                "USD",
            ),

            # EUR
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*€",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:EUR|евро)\b",
                "EUR",
            ),

            # RUB
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:российских\s+рублей)\b",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*RUB\b",
                "RUB",
            ),

            # PLN
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:PLN|злотых|злот)\b",
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

            raw_price = match.group(1)

            raw_price = (
                raw_price
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

            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\$€]\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\d\s.,]+\s*"
            r"(?:\$|€|₽|р\b)",

            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\d\s.,]+\s*"
            r"(?:BYN|USD|EUR|RUB|PLN|"
            r"доллар(?:а|ов)?|евро|"
            r"руб(?:лей|ля)?|"
            r"российских\s+рублей|"
            r"белорусских\s+рублей|"
            r"злотых|злот)",
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

    def get_product_from_link(
        self,
        url: str
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

    def search_everywhere(
        self,
        query: str
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

        results = self.remove_bad_results(
            results,
            parsed,
        )

        results = self.remove_duplicates(
            results,
        )

        return self.rank_results(
            results,
            parsed,
        )

    def remove_bad_results(
        self,
        products: List[Product],
        parsed: SearchQuery,
    ) -> List[Product]:

        clean_results = []

        for product in products:

            if not product.name:
                continue

            name = product.name.lower()

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

            # Если есть бюджет —
            # проверяем его независимо от валюты товара.
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

                    print(
                        "Currency conversion failed:",
                        product.price,
                        product.currency,
                        "->",
                        parsed.currency,
                    )

                    # Не утверждаем, что товар
                    # находится в бюджете.
                    continue

                print(
                    "PRICE:",
                    product.price,
                    product.currency,
                    "=>",
                    round(converted_price, 2),
                    parsed.currency,
                )

                if converted_price > parsed.max_price:
                    continue

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

    def remove_duplicates(
        self,
        products: List[Product]
    ) -> List[Product]:

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

    def rank_results(
        self,
        products: List[Product],
        parsed: SearchQuery | None = None,
    ) -> List[Product]:

        scored_products = []

        for product in products:

            score = calculate_deal_score(
                product
            )

            if product.price is not None:
                score += 5

            if product.is_exact_match:
                score += 10

            # Оцениваем близость к бюджету
            # уже после конвертации валюты.
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