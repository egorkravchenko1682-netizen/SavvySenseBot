from typing import List

from products import Product
from adapters.base import ShopAdapter

from adapters.wildberries import WildberriesAdapter
from adapters.ozon import OzonAdapter
from adapters.amazon import AmazonAdapter
from adapters.aliexpress import AliExpressAdapter
from adapters.ebay import EbayAdapter
from adapters.temu import TemuAdapter
from adapters.taobao import TaobaoAdapter
from adapters.jd import JdAdapter
from adapters.1688 import Adapter1688


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
            Adapter1688(),
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

        return self.sort_by_price(results)

    def sort_by_price(
        self,
        products: List[Product]
    ) -> List[Product]:

        return sorted(
            products,
            key=lambda product: (
                product.price
                if product.price is not None
                else float("inf")
            )
        )