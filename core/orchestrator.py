from __future__ import annotations

from typing import Any


class SavvyOrchestrator:
    """Координирует основной pipeline SAVVY SENSE."""

    def __init__(
        self,
        search_engine: Any,
        extractor: Any,
        matcher: Any,
        deal_engine: Any,
    ) -> None:
        self.search_engine = search_engine
        self.extractor = extractor
        self.matcher = matcher
        self.deal_engine = deal_engine

    def run(
        self,
        query: str,
        budget: float | None = None,
        budget_currency: str | None = None,
        requested_condition: str = "any",
        **kwargs: Any,
    ) -> dict[str, Any]:

        search_results = self.search_engine.search(
            query,
            **kwargs,
        )

        if not search_results:
            return self._empty_result(query)

        extracted_offers = []

        for result in search_results:
            extracted = self.extractor.extract(result)

            if extracted is not None:
                extracted_offers.append(extracted)

        if not extracted_offers:
            return self._empty_result(query)

        match_result = self.matcher.match(
            extracted_offers,
            query,
        )

        matched_offers = self._get_matched_offers(
            match_result
        )

        if not matched_offers:
            return self._empty_result(query)

        deal = self.deal_engine.evaluate(
            offers=matched_offers,
            budget=budget,
            budget_currency=budget_currency,
            requested_condition=requested_condition,
        )

        return {
            "query": query,
            "offers": matched_offers,
            "deal": deal,
        }

    @staticmethod
    def _get_matched_offers(
        match_result: Any,
    ) -> list[dict[str, Any]]:

        if isinstance(match_result, dict):

            exact = match_result.get(
                "exact",
                [],
            )

            similar = match_result.get(
                "similar",
                [],
            )

            return [
                *exact,
                *similar,
            ]

        offers = getattr(
            match_result,
            "offers",
            None,
        )

        if offers is not None:
            return list(offers)

        exact = getattr(
            match_result,
            "exact",
            [],
        )

        similar = getattr(
            match_result,
            "similar",
            [],
        )

        return [
            *exact,
            *similar,
        ]

    @staticmethod
    def _empty_result(
        query: str,
    ) -> dict[str, Any]:

        return {
            "query": query,
            "offers": [],
            "deal": {
                "deal_type": "no_deal",
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
            },
        }