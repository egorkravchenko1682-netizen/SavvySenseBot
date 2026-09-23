from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MatchStatus(str, Enum):
    EXACT = "exact"
    SIMILAR = "similar"
    REJECTED = "rejected"


class AttributeStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass
class AttributeComparison:
    attribute: str
    requested: Any = None
    actual: Any = None
    status: AttributeStatus = AttributeStatus.UNKNOWN
    reason: str | None = None


@dataclass
class MatchResult:
    status: MatchStatus

    score: float = 0.0

    identity_match: bool = False

    comparisons: list[AttributeComparison] = field(
        default_factory=list
    )

    matched_attributes: list[str] = field(
        default_factory=list
    )

    mismatched_attributes: list[str] = field(
        default_factory=list
    )

    unknown_attributes: list[str] = field(
        default_factory=list
    )

    reasons: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_exact(self) -> bool:
        return self.status == MatchStatus.EXACT

    @property
    def is_similar(self) -> bool:
        return self.status == MatchStatus.SIMILAR

    @property
    def is_rejected(self) -> bool:
        return self.status == MatchStatus.REJECTED

    @property
    def has_unknowns(self) -> bool:
        return bool(
            self.unknown_attributes
        )

    @property
    def has_mismatches(self) -> bool:
        return bool(
            self.mismatched_attributes
        )

    def add_comparison(
        self,
        comparison: AttributeComparison,
    ) -> None:

        self.comparisons.append(
            comparison
        )

        if (
            comparison.status
            == AttributeStatus.MATCH
        ):
            if (
                comparison.attribute
                not in self.matched_attributes
            ):
                self.matched_attributes.append(
                    comparison.attribute
                )

        elif (
            comparison.status
            == AttributeStatus.MISMATCH
        ):
            if (
                comparison.attribute
                not in self.mismatched_attributes
            ):
                self.mismatched_attributes.append(
                    comparison.attribute
                )

        else:
            if (
                comparison.attribute
                not in self.unknown_attributes
            ):
                self.unknown_attributes.append(
                    comparison.attribute
                )

    def add_reason(
        self,
        reason: str,
    ) -> None:

        if reason and reason not in self.reasons:
            self.reasons.append(reason)

    def to_dict(self) -> dict[str, Any]:

        return {
            "status": self.status.value,
            "score": self.score,
            "identity_match": self.identity_match,
            "comparisons": [
                {
                    "attribute": item.attribute,
                    "requested": item.requested,
                    "actual": item.actual,
                    "status": item.status.value,
                    "reason": item.reason,
                }
                for item in self.comparisons
            ],
            "matched_attributes":
                self.matched_attributes,
            "mismatched_attributes":
                self.mismatched_attributes,
            "unknown_attributes":
                self.unknown_attributes,
            "reasons":
                self.reasons,
            "metadata":
                self.metadata,
        }