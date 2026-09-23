from __future__ import annotations

from typing import Any

from offer.extractor import OfferExtractor
from offer.normalize import normalize_offers
from offer.deal_engine import DealEngine
from matching import ProductMatcher


class SavvyOrchestrator:
    """
    Главный orchestration layer SAVVY SENSE.

    Отвечает только за последовательность обработки:

        query
          ↓
        search
          ↓
        extraction
          ↓
        normalization
          ↓
        product matching
          ↓
        DealEngine

    Оркестратор не принимает самостоятельных решений
    о выгодности товара.
    """

    def __init__(
        self,
        search_engine: Any,
        extractor: OfferExtractor | None = None,
        matcher: ProductMatcher | None = None,
        deal_engine: DealEngine | None = None,
    ) -> None:

        self.search_engine = search_engine

        self.extractor = (
            extractor
            if extractor is not None
            else OfferExtractor()
        )

        self.matcher = (
            matcher
            if matcher is not None
            else ProductMatcher()
        )

        self.deal_engine = (
            deal_engine
            if deal_engine is not None
            else DealEngine()
        )

    def run(
        self,
        query: str,
        budget: float | None = None,
        budget_currency: str | None = None,
        requested_condition: str = "any",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Полный pipeline SAVVY SENSE.
        """

        # -----------------------------------------------------
        # 1. SEARCH
        # -----------------------------------------------------

        search_results = self._search(
            query=query,
            **kwargs,
        )

        if not search_results:
            return self._empty_result(
                query=query,
                reason="no_search_results",
            )

        # -----------------------------------------------------
        # 2. OFFER EXTRACTION
        # -----------------------------------------------------

        extracted_offers = []

        for result in search_results:

            try:
                extracted = self.extractor.extract(
                    result
                )
            except Exception:
                continue

            if extracted:
                extracted_offers.append(
                    extracted
                )

        if not extracted_offers:
            return self._empty_result(
                query=query,
                reason="no_extracted_offers",
            )

        # -----------------------------------------------------
        # 3. NORMALIZATION
        # -----------------------------------------------------

        try:
            normalized_offers = normalize_offers(
                extracted_offers
            )
        except Exception:
            normalized_offers = []

        if not normalized_offers:
            return self._empty_result(
                query=query,
                reason="no_normalized_offers",
            )

        # -----------------------------------------------------
        # 4. PRODUCT MATCHING
        # -----------------------------------------------------

        try:
            match_result = self.matcher.match(
                normalized_offers,
                query=query,
            )
        except TypeError:
            # Поддержка matcher-контрактов,
            # где query является первым аргументом.
            match_result = self.matcher.match(
                query,
                normalized_offers,
            )

        # -----------------------------------------------------
        # 5. CONVERT MatchResult
        # -----------------------------------------------------

        matched_offers = self._extract_matched_offers(
            match_result
        )

        if not matched_offers:
            return self._empty_result(
                query=query,
                reason="no_matching_offers",
                match_result=match_result,
            )

        # -----------------------------------------------------
        # 6. DEAL ENGINE
        # -----------------------------------------------------

        deal_result = self.deal_engine.evaluate(
            offers=matched_offers,
            budget=budget,
            budget_currency=budget_currency,
            requested_condition=requested_condition,
        )

        # -----------------------------------------------------
        # 7. FINAL RESULT
        # -----------------------------------------------------

        return {
            "query": query,
            "offers": matched_offers,
            "match_result": self._serialize_match_result(
                match_result
            ),
            "deal": deal_result,
        }

    # =========================================================
    # SEARCH
    # =========================================================

    def _search(
        self,
        query: str,
        **kwargs: Any,
    ) -> list[Any]:

        try:
            result = self.search_engine.search(
                query=query,
                **kwargs,
            )
        except TypeError:
            result = self.search_engine.search(
                query,
            )

        if result is None:
            return []

        if isinstance(result, list):
            return result

        if isinstance(result, tuple):
            return list(result)

        return [result]

    # =========================================================
    # MATCH RESULT
    # =========================================================

    @staticmethod
    def _extract_matched_offers(
        match_result: Any,
    ) -> list[dict[str, Any]]:
        """
        Извлекает offers из нового MatchResult.

        Поддерживает:
        - MatchResult с .offers
        - MatchResult с .exact
        - MatchResult с .similar
        - dict-контракт для обратной совместимости
        """

        # -----------------------------------------------------
        # Новый MatchResult
        # -----------------------------------------------------

        offers = getattr(
            match_result,
            "offers",
            None,
        )

        if offers is not None:
            return SavvyOrchestrator._as_offer_list(
                offers
            )

        # -----------------------------------------------------
        # MatchResult:
        # exact + similar
        # -----------------------------------------------------

        exact = getattr(
            match_result,
            "exact",
            None,
        )

        similar = getattr(
            match_result,
            "similar",
            None,
        )

        if exact is not None or similar is not None:

            return (
                SavvyOrchestrator._as_offer_list(exact)
                +
                SavvyOrchestrator._as_offer_list(similar)
            )

        # -----------------------------------------------------
        # Dictionary compatibility
        # -----------------------------------------------------

        if isinstance(match_result, dict):

            offers = match_result.get(
                "offers"
            )

            if offers is not None:
                return SavvyOrchestrator._as_offer_list(
                    offers
                )

            exact = match_result.get(
                "exact",
                [],
            )

            similar = match_result.get(
                "similar",
                [],
            )

            return (
                SavvyOrchestrator._as_offer_list(
                    exact
                )
                +
                SavvyOrchestrator._as_offer_list(
                    similar
                )
            )

        return []

    # =========================================================
    # OFFER CONVERSION
    # =========================================================

    @staticmethod
    def _as_offer_list(
        offers: Any,
    ) -> list[dict[str, Any]]:

        if offers is None:
            return []

        if isinstance(offers, dict):
            return [dict(offers)]

        if isinstance(offers, (list, tuple)):
            result = []

            for offer in offers:

                if isinstance(offer, dict):
                    result.append(
                        dict(offer)
                    )

                elif hasattr(
                    offer,
                    "__dict__",
                ):
                    result.append(
                        dict(vars(offer))
                    )

            return result

        if hasattr(
            offers,
            "__dict__",
        ):
            return [
                dict(vars(offers))
            ]

        return []

    # =========================================================
    # MATCH RESULT SERIALIZATION
    # =========================================================

    @staticmethod
    def _serialize_match_result(
        match_result: Any,
    ) -> dict[str, Any]:

        if match_result is None:
            return {}

        if isinstance(
            match_result,
            dict,
        ):
            return dict(match_result)

        if hasattr(
            match_result,
            "__dict__",
        ):
            return dict(
                vars(match_result)
            )

        result: dict[str, Any] = {}

        for attribute in (
            "exact_count",
            "similar_count",
            "rejected_count",
            "matched_count",
            "comparison_known",
        ):
            if hasattr(
                match_result,
                attribute,
            ):
                result[attribute] = getattr(
                    match_result,
                    attribute,
                )

        return result

    # =========================================================
    # EMPTY RESULT
    # =========================================================

    @staticmethod
    def _empty_result(
        query: str,
        reason: str,
        match_result: Any = None,
    ) -> dict[str, Any]:

        result = {
            "query": query,
            "offers": [],
            "match_result": {},
            "deal": {
                "deal_type": "no_deal",
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
                "reason": reason,
            },
        }

        if match_result is not None:
            result["match_result"] = (
                SavvyOrchestrator._serialize_match_result(
                    match_result
                )
            )

        return result