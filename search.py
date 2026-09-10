import re
from typing import List, Tuple, Optional

from products import Product
from deal_score import calculate_deal_score

from adapters.base import ShopAdapter

from adapters.wildberries import WildberriesAdapter
from adapters.ozon import OzonAdapter
from adapters.amazon import AmazonAdapter
from adapters.aliexpress import AliExpressAdapter
from adapters.ebay import EbayAdapter
from adapters.temu import TemuAdapter
from adapters.taobao import TaobaoAdapter
from adapters.jd import JdAdapter
from adapters.walmart import WalmartAdapter
from adapters.web_search import WebSearchAdapter


class SearchQuery:
    """
    Разобранный пользовательский запрос.

    Например:

    "Нужен айфон 15 до 800$"

    превращается в:

    query = "айфон 15"
    max_price = 800
    currency = "USD"
    """

    def __init__(
        self,
        query: str,
        max_price: Optional[float] = None,
        currency: Optional[str] = None,
    ):
        self.query = query
        self.max_price = max_price
        self.currency = currency


class GlobalSearch:

    def __init__(self):

        self.adapters: List[ShopAdapter] = [
            WildberriesAdapter(),
            OzonAdapter(),
            AmazonAdapter(),
            AliExpressAdapter(),
            EbayAdapter(),
            TemuAdapter(),
            TaobaoAdapter(),
            JdAdapter(),
            WalmartAdapter(),
            WebSearchAdapter(),
        ]

    # ---------------------------------------------------------
    # РАЗБОР ЗАПРОСА
    # ---------------------------------------------------------

    def parse_query(self, text: str) -> SearchQuery:

        original = text.strip()

        max_price = None
        currency = None

        # -----------------------------------------------------
        # Ищем ограничения по цене
        # -----------------------------------------------------

        price_patterns = [

            # 800$
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            # $800
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            # 800 USD
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:usd|доллар(?:а|ов)?)",
                "USD",
            ),

            # 800€
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*€",
                "EUR",
            ),

            # €800
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            # 800 EUR
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:eur|евро)",
                "EUR",
            ),

            # 800 BYN
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:byn|бел(?:\.|орусских)?\s*руб)",
                "BYN",
            ),

            # 800 руб / 800 рублей
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:₽|руб(?:\.|лей)?|рублей)",
                "RUB",
            ),

            # 800 ₽
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            # 800 PLN / злотых
            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:pln|злотых|злот)",
                "PLN",
            ),
        ]

        for pattern, detected_currency in price_patterns:

            match = re.search(
                pattern,
                original,
                flags=re.IGNORECASE,
            )

            if match:

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

        # -----------------------------------------------------
        # Очищаем запрос
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
        ]

        for pattern in cleanup_patterns:

            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        # Удаляем конструкцию бюджета
        budget_patterns = [
            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\$€₽]\s*[\d\s.,]+",

            r"(?:до|не\s+дороже|максимум|не\s+более)"
            r"\s*[\d\s.,]+\s*"
            r"(?:\$|€|₽|usd|eur|byn|rub|pln|"
            r"доллар(?:а|ов)?|евро|руб(?:\.|лей)?|"
            r"рублей|злотых|злот)",
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
                    e
                )

        return None

    # ---------------------------------------------------------
    # ГЛОБАЛЬНЫЙ ПОИСК
    # ---------------------------------------------------------

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

        # -----------------------------------------------------
        # Ищем уже очищенный запрос
        # -----------------------------------------------------

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
                    e
                )

        # -----------------------------------------------------
        # Удаляем мусор
        # -----------------------------------------------------

        results = self.remove_bad_results(
            results,
            parsed,
        )

        # -----------------------------------------------------
        # Удаляем дубликаты
        # -----------------------------------------------------

        results = self.remove_duplicates(
            results
        )

        # -----------------------------------------------------
        # Сортируем по SAVVY SCORE
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
        products: List[Product],
        parsed: SearchQuery,
    ) -> List[Product]:

        clean_results = []

        for product in products:

            # -------------------------------------------------
            # Нет названия
            # -------------------------------------------------

            if not product.name:

                continue

            name = product.name.lower()

            # -------------------------------------------------
            # Категории / статьи / мусор
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Цена выше бюджета
            #
            # ВАЖНО:
            #
            # Мы сравниваем только если валюта товара
            # совпадает с валютой ограничения.
            #
            # Конвертацию сделаем отдельным модулем.
            # -------------------------------------------------

            if (
                parsed.max_price is not None
                and product.price is not None
                and product.currency
                and parsed.currency
                and product.currency.upper()
                == parsed.currency.upper()
            ):

                if product.price > parsed.max_price:

                    continue

            # -------------------------------------------------
            # Нереалистичная цена
            # -------------------------------------------------

            if product.price is not None:

                if product.price <= 0:

                    continue

                # Для дорогих товаров не принимаем
                # подозрительно маленькие значения.

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

            clean_results.append(
                product
            )

        return clean_results

    # ---------------------------------------------------------
    # ДУБЛИКАТЫ
    # ---------------------------------------------------------

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
            )

            if key in seen:

                continue

            seen.add(key)

            unique.append(
                product
            )

        return unique

    # ---------------------------------------------------------
    # РАНЖИРОВАНИЕ
    # ---------------------------------------------------------

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

            # -------------------------------------------------
            # Бонус за наличие цены
            # -------------------------------------------------

            if product.price is not None:

                score += 5

            # -------------------------------------------------
            # Бонус за точное совпадение
            # -------------------------------------------------

            if product.is_exact_match:

                score += 10

            # -------------------------------------------------
            # Бонус за цену ниже бюджета
            # -------------------------------------------------

            if (
                parsed
                and parsed.max_price
                and product.price
                and product.currency
                and parsed.currency
                and product.currency.upper()
                == parsed.currency.upper()
            ):

                percentage = (
                    product.price
                    / parsed.max_price
                )

                # Очень хорошая цена
                if percentage <= 0.50:
                    score += 15

                elif percentage <= 0.70:
                    score += 10

                elif percentage <= 0.85:
                    score += 5

            score = min(
                score,
                100
            )

            scored_products.append(
                (
                    score,
                    product
                )
            )

        # -----------------------------------------------------
        # Сначала лучший SAVVY SCORE
        # -----------------------------------------------------

        scored_products.sort(
            key=lambda item: (
                item[0],
                -(item[1].price or 999999999)
            ),
            reverse=True,
        )

        return [
            product
            for score, product
            in scored_products
        ]