from products import Product
from adapters.base import ShopAdapter


class AliExpressAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "aliexpress"

    def can_handle(self, url: str) -> bool:
        domains = [
            "aliexpress.com",
            "aliexpress.ru",
        ]

        url = url.lower()

        return any(domain in url for domain in domains)

    def get_product(self, url: str) -> Product | None:
        # Реальное получение данных AliExpress
        # подключим на этапе интеграции источников.
        return None

    def search(self, query: str) -> list[Product]:
        # Поиск AliExpress подключим позже.
        return []