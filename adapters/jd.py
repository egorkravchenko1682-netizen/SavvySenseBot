from products import Product
from adapters.base import ShopAdapter


class JdAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "jd"

    def can_handle(self, url: str) -> bool:
        return "jd.com" in url.lower()

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:
        return []