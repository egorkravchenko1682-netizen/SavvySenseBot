"""
SAVVY SENSE Offer Extraction.

Модули этого пакета отвечают за извлечение
структурированных данных из найденных предложений.
"""

from .base import BaseExtractor
from .product import ProductExtractor
from .attributes import AttributeExtractor
from .price import PriceExtractor
from .condition import ConditionExtractor
from .availability import AvailabilityExtractor
from .structured_data import StructuredDataExtractor


__all__ = [
    "BaseExtractor",
    "ProductExtractor",
    "AttributeExtractor",
    "PriceExtractor",
    "ConditionExtractor",
    "AvailabilityExtractor",
    "StructuredDataExtractor",
]