from typing import List

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
        ]

    def get_product_from_link(
        self,
        url: str
    ) -> Product | None:

        for adapter in self.adapters:

            if adapter.can_handle(url):
                return adapter.get_product(url)

        return None

    def search_everywhere(
        self,
        query: str
    ) -> List[Product]:

        results = []

        for adapter in self.adapters:

            try:

                products = adapter.search(query)

                if products:
                    results.extend(products)

            except Exception as e:

                print(
                    f"{adapter.shop_name} search error:",
                    e
                )

        return self.rank_results(results)

    def rank_results(
        self,
        products: List[Product]
    ) -> List[Product]:

        scored_products = []

        for product in products:

            score = calculate_deal_score(product)

            scored_products.append(
                (score, product)
            )

        scored_products.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return [
            product
            for score, product
            in scored_products
        ]