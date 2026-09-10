from products import Product
from adapters.base import ShopAdapter


class OzonAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "ozon"

    def can_handle(self, url: str) -> bool:
        return "ozon.ru" in url.lower()

    def get_product(self, url: str) -> Product | None:
        # Получение данных Ozon подключим
        # отдельным модулем после создания
        # общей системы поиска.
        return None

    def search(self, query: str) -> list[Product]:
        # Поиск Ozon подключим позже.
        return []