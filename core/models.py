from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UserContext:
    user_id: Optional[int] = None
    region: str = "BY"
    currency: str = "USD"

    preferences: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SavvyRequest:
    text: Optional[str] = None
    image: Optional[Any] = None
    url: Optional[str] = None

    user: Optional[UserContext] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SavvyResponse:
    success: bool
    intent: Optional[str] = None

    data: dict[str, Any] = field(
        default_factory=dict
    )

    error: Optional[str] = None