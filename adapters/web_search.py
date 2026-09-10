from products import Product
from adapters.base import ShopAdapter


class WebSearchAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "web_search"

    def can_handle(self, url: str) -> bool:
        return False

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:
        return []