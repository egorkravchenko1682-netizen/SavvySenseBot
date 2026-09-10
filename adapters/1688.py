from products import Product
from adapters.base import ShopAdapter


class Adapter1688(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "1688"

    def can_handle(self, url: str) -> bool:
        return "1688.com" in url.lower()

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:
        return []