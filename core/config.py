import os
from dataclasses import dataclass


@dataclass
class SavvyConfig:
    default_region: str = "BY"
    default_currency: str = "USD"
    max_results: int = 20

    @classmethod
    def load(cls):
        return cls(
            default_region=os.getenv("SAVVY_REGION", "BY"),
            default_currency=os.getenv("SAVVY_CURRENCY", "USD"),
            max_results=int(
                os.getenv("SAVVY_MAX_RESULTS", "20")
            ),
        )