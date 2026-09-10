from products import Product
from adapters.base import ShopAdapter


class TaobaoAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "taobao"

    def can_handle(self, url: str) -> bool:
        return "taobao.com" in url.lower()

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:
        return []