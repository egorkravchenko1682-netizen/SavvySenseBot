from abc import ABC, abstractmethod
from typing import List

from products import Product


class ShopAdapter(ABC):

    @property
    @abstractmethod
    def shop_name(self) -> str:
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass

    @abstractmethod
    def get_product(self, url: str) -> Product | None:
        pass

    @abstractmethod
    def search(self, query: str) -> List[Product]:
        pass