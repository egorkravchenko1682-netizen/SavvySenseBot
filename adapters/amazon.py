from products import Product
from adapters.base import ShopAdapter


class AmazonAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "amazon"

    def can_handle(self, url: str) -> bool:
        domains = [
            "amazon.com",
            "amazon.de",
            "amazon.fr",
            "amazon.co.uk",
        ]

        url = url.lower()

        return any(domain in url for domain in domains)

    def get_product(self, url: str) -> Product | None:
        # Реальное получение данных Amazon
        # подключим через отдельный источник.
        return None

    def search(self, query: str) -> list[Product]:
        # Глобальный поиск Amazon подключим позже.
        return []