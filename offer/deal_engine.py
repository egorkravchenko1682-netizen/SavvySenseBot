from __future__ import annotations

from typing import Any

from .deal_candidates import DealCandidates
from .deal_quality_comparator import DealQualityComparator
from .deal_budget import DealBudget
from .deal_condition import DealCondition
from .deal_quality import DealQuality
from .deal_quality_confidence import DealQualityConfidence
from .deal_quality_result import DealQualityResult
from .offer_reliability import OfferReliability
from .offer_risk import OfferRisk
from .review_confidence import ReviewConfidence
from .risk_level import RiskLevel
from .risk_filter import RiskFilter
from .risk_decision import RiskDecision


class DealEngine:
    """Формирует сделку с учётом состояния, бюджета, качества и риска."""

    def __init__(self) -> None:
        self.candidates = DealCandidates()
        self.comparator = DealQualityComparator()
        self.budget = DealBudget()
        self.condition = DealCondition()
        self.quality = DealQuality()
        self.quality_confidence = DealQualityConfidence()
        self.quality_result = DealQualityResult()
        self.review_confidence = ReviewConfidence()
        self.reliability = OfferReliability()
        self.risk = OfferRisk()
        self.risk_level = RiskLevel()
        self.risk_filter = RiskFilter()
        self.risk_decision = RiskDecision()

    def evaluate(
        self,
        offers: list[dict[str, Any]],
        budget: float | None = None,
        budget_currency: str | None = None,
        requested_condition: str = "any",
    ) -> dict[str, Any]:

        candidates = self.candidates.select(offers)

        condition_result = self.condition.apply(
            offers=candidates["exact"] + candidates["similar"],
            requested_condition=requested_condition,
        )

        filtered_offers = condition_result["offers"]

        enriched_offers = []

        for offer in filtered_offers:

            enriched_offer = dict(offer)

            review_confidence = self.review_confidence.calculate(
                offer.get("review_count")
            )

            reliability = self.reliability.calculate(
                enriched_offer
            )

            enriched_offer.update(
                {
                    "review_confidence": review_confidence[
                        "review_confidence"
                    ],
                    "review_confidence_score": review_confidence[
                        "review_confidence_score"
                    ],
                    "review_confidence_known": review_confidence[
                        "review_confidence_known"
                    ],
                    "offer_reliability": reliability[
                        "offer_reliability"
                    ],
                    "offer_reliability_score": reliability[
                        "offer_reliability_score"
                    ],
                    "offer_reliability_known": reliability[
                        "offer_reliability_known"
                    ],
                }
            )

            quality = self.quality.calculate(
                seller=enriched_offer,
                reviews=enriched_offer,
                review_confidence=review_confidence,
                offer_reliability=reliability,
            )

            enriched_offer.update(
                {
                    "deal_quality": quality.get(
                        "deal_quality"
                    ),
                    "deal_quality_score": quality.get(
                        "deal_quality_score"
                    ),
                    "deal_quality_known": quality.get(
                        "deal_quality_known",
                        False,
                    ),
                }
            )

            quality_confidence = (
                self.quality_confidence.calculate(
                    enriched_offer
                )
            )

            enriched_offer.update(
                {
                    "deal_quality_confidence": (
                        quality_confidence[
                            "deal_quality_confidence"
                        ]
                    ),
                    "deal_quality_confidence_score": (
                        quality_confidence[
                            "deal_quality_confidence_score"
                        ]
                    ),
                    "deal_quality_confidence_known": (
                        quality_confidence[
                            "deal_quality_confidence_known"
                        ]
                    ),
                }
            )

            risk = self.risk.calculate(
                enriched_offer
            )

            enriched_offer.update(
                {
                    "offer_risk": risk[
                        "offer_risk"
                    ],
                    "offer_risk_points": risk[
                        "offer_risk_points"
                    ],
                    "offer_risk_known": risk[
                        "offer_risk_known"
                    ],
                }
            )

            risk_level = self.risk_level.evaluate(
                risk
            )

            enriched_offer.update(
                {
                    "risk_level": risk_level[
                        "risk_level"
                    ],
                    "risk_level_score": risk_level[
                        "risk_level_score"
                    ],
                    "risk_level_known": risk_level[
                        "risk_level_known"
                    ],
                }
            )

            risk_decision = self.risk_decision.decide(
                enriched_offer
            )

            enriched_offer.update(
                {
                    "risk_decision": risk_decision[
                        "risk_decision"
                    ],
                    "risk_decision_known": risk_decision[
                        "risk_decision_known"
                    ],
                }
            )

            enriched_offers.append(
                enriched_offer
            )

        risk_result = self.risk_filter.select(
            enriched_offers
        )

        exact = [
            offer
            for offer in enriched_offers
            if offer.get("status") == "exact"
        ]

        similar = [
            offer
            for offer in enriched_offers
            if offer.get("status") == "similar"
        ]

        exact_budget = self.budget.apply(
            exact,
            budget,
            budget_currency,
        )

        similar_budget = self.budget.apply(
            similar,
            budget,
            budget_currency,
        )

        exact_result = self.comparator.find_best(
            exact_budget["within_budget"]
        )

        if exact_result["comparison_known"]:
            return self._result(
                deal_type="exact",
                result=exact_result,
                candidates=candidates,
                condition_result=condition_result,
                exact_budget=exact_budget,
                similar_budget=similar_budget,
                risk_result=risk_result,
            )

        similar_result = self.comparator.find_best(
            similar_budget["within_budget"]
        )

        if similar_result["comparison_known"]:
            return self._result(
                deal_type="similar",
                result=similar_result,
                candidates=candidates,
                condition_result=condition_result,
                exact_budget=exact_budget,
                similar_budget=similar_budget,
                risk_result=risk_result,
            )

        return {
            "deal_type": "no_deal",
            "best_offer": None,
            "comparison_known": False,
            "comparison_source": None,
            "deal_quality": None,
            "deal_quality_score": None,
            "deal_quality_known": False,
            "deal_quality_confidence": None,
            "deal_quality_confidence_score": None,
            "deal_quality_confidence_known": False,
            "offer_risk": None,
            "offer_risk_points": None,
            "offer_risk_known": False,
            "risk_level": None,
            "risk_level_score": None,
            "risk_level_known": False,
            "risk_decision": None,
            "risk_decision_known": False,
            "exact_count": candidates["exact_count"],
            "similar_count": candidates["similar_count"],
            "within_budget_count": (
                exact_budget["within_budget_count"]
                + similar_budget["within_budget_count"]
            ),
            "over_budget_count": (
                exact_budget["over_budget_count"]
                + similar_budget["over_budget_count"]
            ),
            "condition_matched_count": (
                condition_result["matched_count"]
            ),
            "condition_mismatched_count": (
                condition_result["mismatched_count"]
            ),
            "condition_unknown_count": (
                condition_result["unknown_count"]
            ),
            "safe_count": risk_result["safe_count"],
            "risky_count": risk_result["risky_count"],
            "risk_unknown_count": risk_result["unknown_count"],
        }

    def _result(
        self,
        deal_type: str,
        result: dict[str, Any],
        candidates: dict[str, Any],
        condition_result: dict[str, Any],
        exact_budget: dict[str, Any],
        similar_budget: dict[str, Any],
        risk_result: dict[str, Any],
    ) -> dict[str, Any]:

        best_offer = result["best_offer"]

        quality = self.quality_result.build(
            {
                "best_offer": best_offer,
            }
        )

        return {
            "deal_type": deal_type,
            "best_offer": best_offer,
            "comparison_known": True,
            "comparison_source": result[
                "comparison_source"
            ],

            "deal_quality": quality[
                "deal_quality"
            ],
            "deal_quality_score": quality[
                "deal_quality_score"
            ],
            "deal_quality_known": quality[
                "deal_quality_known"
            ],

            "deal_quality_confidence": best_offer.get(
                "deal_quality_confidence"
            ),
            "deal_quality_confidence_score": best_offer.get(
                "deal_quality_confidence_score"
            ),
            "deal_quality_confidence_known": best_offer.get(
                "deal_quality_confidence_known",
                False,
            ),

            "offer_risk": best_offer.get(
                "offer_risk"
            ),
            "offer_risk_points": best_offer.get(
                "offer_risk_points"
            ),
            "offer_risk_known": best_offer.get(
                "offer_risk_known",
                False,
            ),

            "risk_level": best_offer.get(
                "risk_level"
            ),
            "risk_level_score": best_offer.get(
                "risk_level_score"
            ),
            "risk_level_known": best_offer.get(
                "risk_level_known",
                False,
            ),

            "risk_decision": best_offer.get(
                "risk_decision"
            ),
            "risk_decision_known": best_offer.get(
                "risk_decision_known",
                False,
            ),

            "review_confidence": best_offer.get(
                "review_confidence"
            ),
            "review_confidence_score": best_offer.get(
                "review_confidence_score"
            ),
            "review_confidence_known": best_offer.get(
                "review_confidence_known",
                False,
            ),

            "offer_reliability": best_offer.get(
                "offer_reliability"
            ),
            "offer_reliability_score": best_offer.get(
                "offer_reliability_score"
            ),
            "offer_reliability_known": best_offer.get(
                "offer_reliability_known",
                False,
            ),

            "exact_count": candidates[
                "exact_count"
            ],
            "similar_count": candidates[
                "similar_count"
            ],

            "within_budget_count": (
                exact_budget[
                    "within_budget_count"
                ]
                + similar_budget[
                    "within_budget_count"
                ]
            ),

            "over_budget_count": (
                exact_budget[
                    "over_budget_count"
                ]
                + similar_budget[
                    "over_budget_count"
                ]
            ),

            "condition_matched_count": (
                condition_result[
                    "matched_count"
                ]
            ),

            "condition_mismatched_count": (
                condition_result[
                    "mismatched_count"
                ]
            ),

            "condition_unknown_count": (
                condition_result[
                    "unknown_count"
                ]
            ),

            "safe_count": risk_result[
                "safe_count"
            ],
            "risky_count": risk_result[
                "risky_count"
            ],
            "risk_unknown_count": risk_result[
                "unknown_count"
            ],
        }