from __future__ import annotations

from typing import Any, Optional

from offer.deal_engine import DealEngine
from offer.normalizer import normalize_offers

from currency.converter import CurrencyConverter

from region.groups import regions_to_search
from region.currency_normalize import normalize_offers_currency
from region.landed_cost import apply_real_cost
from region.logistics import estimate_logistics
from region.search_sweep import sweep_regions

from .catalog import candidate_categories


class GiftRecommender:
    """
    Подбирает подарок по получателю и бюджету — без конкретного товара
    для строгого сопоставления (в отличие от обычного поиска).

    Идея: перебрать несколько подходящих категорий подарков
    (`gift.catalog`), для каждой найти предложения (по всем регионам
    сравнения, как и в обычном поиске), посчитать их полную стоимость
    и оценить качество/риск через уже существующий `DealEngine` —
    а затем выбрать несколько лучших категорий.

    Строгого `ProductMatcher` здесь нет: для категории вроде "женские
    духи" нет единственного "правильного" товара, поэтому каждый
    найденный оффер считается кандидатом ("exact" в терминах
    DealEngine — не потому что он точно совпадает с чем-то конкретным,
    а потому что DealEngine больше ничего не отбраковывает по
    совпадению).
    """

    def __init__(
        self,
        search_engine: Any,
        deal_engine: Optional[DealEngine] = None,
        currency_converter: Optional[CurrencyConverter] = None,
    ) -> None:
        self.search_engine = search_engine
        self.deal_engine = deal_engine or DealEngine()
        self.currency_converter = currency_converter or CurrencyConverter()

    def recommend(
        self,
        gift_request: dict[str, Any],
        region: str,
        currency: str,
        international: bool = True,
        max_suggestions: int = 3,
    ) -> list[dict[str, Any]]:

        budget = gift_request.get("budget")
        budget_currency = gift_request.get("currency") or currency
        recipient = gift_request.get("recipient", "generic")

        categories = candidate_categories(recipient)
        regions = regions_to_search(region, international=international)

        budget_dict = (
            {"max": budget, "currency": budget_currency}
            if budget is not None
            else {}
        )

        suggestions: list[dict[str, Any]] = []

        for category in categories:
            offers = self._collect_category_offers(
                category=category,
                regions=regions,
                currency=currency,
                budget_dict=budget_dict,
                destination_region=region,
            )

            if not offers:
                continue

            deal = self.deal_engine.evaluate(
                offers=offers,
                budget=budget,
                budget_currency=budget_currency,
                requested_condition="any",
            )

            if not deal.get("comparison_known"):
                continue

            suggestions.append(
                {
                    "category": category,
                    "offer": deal["best_offer"],
                    "deal_type": deal.get("deal_type"),
                    "deal_quality": deal.get("deal_quality"),
                    "deal_quality_score": deal.get("deal_quality_score"),
                    "risk_level": deal.get("risk_level"),
                    "risk_decision": deal.get("risk_decision"),
                }
            )

        suggestions.sort(key=self._ranking_key)

        return suggestions[:max_suggestions]

    def _collect_category_offers(
        self,
        category: str,
        regions: list[str],
        currency: str,
        budget_dict: dict[str, Any],
        destination_region: str,
    ) -> list[dict[str, Any]]:

        raw_results = sweep_regions(
            search_engine=self.search_engine,
            queries=[category],
            regions=regions,
            currency=currency,
            budget=budget_dict,
        )

        offers = [
            result
            for result in raw_results
            if isinstance(result, dict) and result.get("price") is not None
        ]

        if not offers:
            return []

        offers = normalize_offers(offers)
        offers = normalize_offers_currency(
            offers,
            target_currency=currency,
            converter=self.currency_converter,
        )
        offers = [
            estimate_logistics(offer, destination_region=destination_region)
            for offer in offers
        ]
        offers = [apply_real_cost(offer) for offer in offers]

        for offer in offers:
            # У подарка нет единственного "правильного" товара для
            # строгого ProductMatcher — каждый найденный по категории
            # оффер считается пригодным кандидатом для DealEngine.
            offer["status"] = "exact"
            offer["usable"] = True

        return offers

    @staticmethod
    def _ranking_key(suggestion: dict[str, Any]) -> tuple[Any, ...]:
        offer = suggestion["offer"] or {}

        # Сначала — не заблокированные по риску, затем выше качество
        # сделки, затем ниже полная (или хотя бы частичная) стоимость.
        blocked = suggestion.get("risk_decision") == "block"
        quality_score = suggestion.get("deal_quality_score") or 0
        cost = (
            offer.get("real_cost")
            if offer.get("real_cost_known")
            else offer.get("real_cost_partial")
            if offer.get("real_cost_partial") is not None
            else offer.get("price")
        )
        cost = cost if cost is not None else float("inf")

        return (blocked, -quality_score, cost)
