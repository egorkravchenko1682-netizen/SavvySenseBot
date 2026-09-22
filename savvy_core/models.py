from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeliveryProfile:
    country: str = "BY"
    city: Optional[str] = None
    currency: str = "BYN"
    max_delivery_days: Optional[int] = None
    max_shipping_cost: Optional[float] = None


@dataclass
class UserProfile:
    user_id: int
    delivery: DeliveryProfile = field(
        default_factory=DeliveryProfile
    )
    preferences: dict = field(default_factory=dict)


@dataclass
class SearchRequest:
    original_query: str
    intent: str

    category: Optional[str] = None
    keywords: list[str] = field(default_factory=list)

    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: Optional[str] = None

    country: Optional[str] = None
    city: Optional[str] = None

    recipient: Optional[str] = None
    use_case: Optional[str] = None

    search_region: str = (
        "regional_then_cis_then_global"
    )


@dataclass
class Offer:
    title: str
    seller: str
    source: str
    url: str

    price: float
    currency: str

    shipping_cost: float = 0.0
    taxes: float = 0.0
    fees: float = 0.0

    available: bool = True
    delivery_days: Optional[int] = None
    seller_rating: Optional[float] = None

    @property
    def real_cost(self) -> float:
        return (
            self.price
            + self.shipping_cost
            + self.taxes
            + self.fees
        )


@dataclass
class SearchResult:
    request: SearchRequest

    offers: list[Offer] = field(
        default_factory=list
    )

    cheapest: Optional[Offer] = None
    best_deal: Optional[Offer] = None

    savvy_score: Optional[int] = None
    decision: Optional[str] = None
    explanation: Optional[str] = None