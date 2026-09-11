from products import Product
from adapters.base import ShopAdapter


class EbayAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "ebay"

    def can_handle(self, url: str) -> bool:
        domains = [
            "ebay.com",
            "ebay.de",
            "ebay.fr",
            "ebay.co.uk",
        ]
        url = url.lower()
        return any(domain in url for domain in domains)

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:
        return []