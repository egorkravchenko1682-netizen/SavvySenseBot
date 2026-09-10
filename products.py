from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    name: str
    shop: str
    url: str

    price: Optional[float] = None
    currency: Optional[str] = None

    old_price: Optional[float] = None

    brand: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None

    image_url: Optional[str] = None

    delivery_price: Optional[float] = None
    delivery_currency: Optional[str] = None

    seller: Optional[str] = None

    product_id: Optional[str] = None

    is_exact_match: bool = False