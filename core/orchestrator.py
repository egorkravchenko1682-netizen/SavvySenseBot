from __future__ import annotations

from typing import Any, Optional

from core.config import SavvyConfig
from core.models import SavvyRequest, SavvyResponse, UserContext

from intent.detector import detect_intent

from product.identity import identify_product
from product.dna import build_product_dna
from product.query import build_search_plan

from search.engine import GlobalSearchEngine
from search.adapters.demo import DemoAdapter
from search.adapters.duckduckgo import DuckDuckGoAdapter

from marketplaces.wildberries import WildberriesAdapter
from marketplaces.ozon import OzonAdapter
from marketplaces.ebay import EbayAdapter
from marketplaces.aliexpress import AliExpressAdapter
from marketplaces.alibaba import AlibabaAdapter
from marketplaces.china1688 import China1688Adapter

from offer.extractor import OfferExtractor
from offer.normalizer import normalize_offers
from offer.deal_engine import DealEngine

from matching.matcher import ProductMatcher
from matching.result import MatchStatus

from currency.converter import CurrencyConverter

from region.groups import regions_to_search
from region.currency_normalize import normalize_offers_currency
from region.landed_cost import apply_real_cost
from region.logistics import estimate_logistics
from region.search_sweep import sweep_regions

from gift.profile import is_gift_request, extract_gift_request
from gift.recommender import GiftRecommender


class SavvyCore:
    """
    ÐÐ»Ð°Ð²Ð½Ð°Ñ ÑÐ¾ÑÐºÐ° Ð²ÑÐ¾Ð´Ð° SAVVY SENSE.

    Ð¡Ð¾Ð±Ð¸ÑÐ°ÐµÑ Ð¿Ð°Ð¹Ð¿Ð»Ð°Ð¹Ð½:

        intent -> product identity -> product DNA -> search plan
        -> Ð¿Ð¾Ð¸ÑÐº Ð¿Ð¾ Ð½ÐµÑÐºÐ¾Ð»ÑÐºÐ¸Ð¼ ÑÐµÐ³Ð¸Ð¾Ð½Ð°Ð¼ -> Ð¸Ð·Ð²Ð»ÐµÑÐµÐ½Ð¸Ðµ -> Ð½Ð¾ÑÐ¼Ð°Ð»Ð¸Ð·Ð°ÑÐ¸Ñ
        -> Ð¾ÑÐµÐ½ÐºÐ° Ð»Ð¾Ð³Ð¸ÑÑÐ¸ÐºÐ¸/Ð¿Ð¾ÑÐ»Ð¸Ð½Ñ -> ÑÐ¾Ð¿Ð¾ÑÑÐ°Ð²Ð»ÐµÐ½Ð¸Ðµ -> Ð¾ÑÐµÐ½ÐºÐ° ÑÐ´ÐµÐ»ÐºÐ¸

    ÐÑÐ´ÐµÐ»ÑÐ½Ð°Ñ Ð²ÐµÑÐºÐ° â Ð¿Ð¾Ð´Ð±Ð¾Ñ Ð¿Ð¾Ð´Ð°ÑÐºÐ° (`intent == "gift"`): ÑÐ°Ð¼ Ð½ÐµÑ
    ÐºÐ¾Ð½ÐºÑÐµÑÐ½Ð¾Ð³Ð¾ ÑÐ¾Ð²Ð°ÑÐ° Ð´Ð»Ñ ÑÑÑÐ¾Ð³Ð¾Ð³Ð¾ ÑÐ¾Ð¿Ð¾ÑÑÐ°Ð²Ð»ÐµÐ½Ð¸Ñ, Ð¿Ð¾ÑÑÐ¾Ð¼Ñ Ð²Ð¼ÐµÑÑÐ¾
    ProductMatcher Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÑÑÑ `GiftRecommender`, Ð¿ÐµÑÐµÐ±Ð¸ÑÐ°ÑÑÐ¸Ð¹
    Ð¿Ð¾Ð´ÑÐ¾Ð´ÑÑÐ¸Ðµ ÐºÐ°ÑÐµÐ³Ð¾ÑÐ¸Ð¸ Ð¸ Ð¾ÑÐµÐ½Ð¸Ð²Ð°ÑÑÐ¸Ð¹ Ð¸Ñ ÑÐµÐ¼ Ð¶Ðµ DealEngine.

    Ð¡ÑÐ°Ð²Ð½ÐµÐ½Ð¸Ðµ "Ð´ÐµÑÐµÐ²Ð»Ðµ Ð² Ð´ÑÑÐ³Ð¾Ð¼ ÑÐµÐ³Ð¸Ð¾Ð½Ðµ, Ð²ÐºÐ»ÑÑÐ°Ñ Ð´Ð¾ÑÑÐ°Ð²ÐºÑ Ð¸ Ð¿Ð¾ÑÐ»Ð¸Ð½Ñ"
    ÑÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½Ð¾ ÑÐ°Ðº: `SavvyCore` Ð¾Ð¿ÑÐ°ÑÐ¸Ð²Ð°ÐµÑ Ð½Ðµ ÑÐ¾Ð»ÑÐºÐ¾ Ð´Ð¾Ð¼Ð°ÑÐ½Ð¸Ð¹ ÑÐµÐ³Ð¸Ð¾Ð½
    Ð¿Ð¾Ð»ÑÐ·Ð¾Ð²Ð°ÑÐµÐ»Ñ, Ð½Ð¾ Ð¸ Ð½ÐµÑÐºÐ¾Ð»ÑÐºÐ¾ Ð´Ð¾Ð¿Ð¾Ð»Ð½Ð¸ÑÐµÐ»ÑÐ½ÑÑ (ÑÐ¼.
    `region.groups.regions_to_search`), Ð¿Ð¾Ð¼ÐµÑÐ°ÐµÑ ÐºÐ°Ð¶Ð´ÑÐ¹ Ð½Ð°Ð¹Ð´ÐµÐ½Ð½ÑÐ¹
    Ð¾ÑÑÐµÑ ÐµÐ³Ð¾ Ð¸ÑÑÐ¾Ð´Ð½ÑÐ¼ ÑÐµÐ³Ð¸Ð¾Ð½Ð¾Ð¼, Ð´Ð¾Ð¿Ð¾Ð»Ð½ÑÐµÑ Ð½ÐµÐ´Ð¾ÑÑÐ°ÑÑÑÑ ÑÑÐ¾Ð¸Ð¼Ð¾ÑÑÑ
    Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸/Ð¿Ð¾ÑÐ»Ð¸Ð½Ñ Ð¾ÑÐµÐ½ÐºÐ¾Ð¹ (`region.logistics`) Ð¸ ÑÑÐ¸ÑÐ°ÐµÑ Ð¿Ð¾Ð»Ð½ÑÑ
    (landed) ÑÑÐ¾Ð¸Ð¼Ð¾ÑÑÑ (`region.landed_cost`) Ð² ÑÐµÑÐ¼Ð¸Ð½Ð°Ñ, ÐºÐ¾ÑÐ¾ÑÑÐµ ÑÐ¶Ðµ
    Ð¿Ð¾Ð½Ð¸Ð¼Ð°ÐµÑ `offer.deal_engine.DealEngine` â ÑÐ¾ ÐµÑÑÑ ÑÐ°Ð½Ð¶Ð¸ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ
    "ÐºÐ°ÐºÐ¾Ð¹ Ð¾ÑÑÐµÑ Ð²ÑÐ³Ð¾Ð´Ð½ÐµÐµ" Ð¿ÑÐ¾ÑÐ¾Ð´Ð¸Ñ Ð¿Ð¾ ÐÐ¡ÐÐ ÑÐµÐ³Ð¸Ð¾Ð½Ð°Ð¼ ÑÑÐ°Ð·Ñ, Ð° Ð½Ðµ
    Ð¿Ð¾ Ð¾Ð´Ð½Ð¾Ð¼Ñ.
    """

    def __init__(
        self,
        config: Optional[SavvyConfig] = None,
        search_engine: Optional[Any] = None,
        extractor: Optional[Any] = None,
        matcher: Optional[Any] = None,
        deal_engine: Optional[Any] = None,
        gift_recommender: Optional[Any] = None,
    ) -> None:
        self.config = config or SavvyConfig.load()

        self.search_engine = search_engine or GlobalSearchEngine(
            adapters=[
                DemoAdapter(),
                WildberriesAdapter(),
                OzonAdapter(),
                EbayAdapter(),
                AliExpressAdapter(),
                AlibabaAdapter(),
                China1688Adapter(),
                DuckDuckGoAdapter(),
            ],
        )
        self.extractor = extractor or OfferExtractor()
        self.matcher = matcher or ProductMatcher()
        self.deal_engine = deal_engine or DealEngine()
        self.currency_converter = CurrencyConverter()
        self.gift_recommender = gift_recommender or GiftRecommender(
            search_engine=self.search_engine,
            deal_engine=self.deal_engine,
            currency_converter=self.currency_converter,
        )

    # =========================
    # PUBLIC API
    # =========================

    def process(self, request: SavvyRequest) -> SavvyResponse:
        """
        ÐÐ´Ð¸Ð½ÑÑÐ²ÐµÐ½Ð½Ð°Ñ Ð¿ÑÐ±Ð»Ð¸ÑÐ½Ð°Ñ ÑÐ¾ÑÐºÐ° Ð²ÑÐ¾Ð´Ð°, ÐºÐ¾ÑÐ¾ÑÑÑ Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÑ bot.py.

        ÐÐ¸ÐºÐ¾Ð³Ð´Ð° Ð½Ðµ Ð±ÑÐ¾ÑÐ°ÐµÑ Ð¸ÑÐºÐ»ÑÑÐµÐ½Ð¸Ðµ Ð½Ð°ÑÑÐ¶Ñ: Telegram-Ð±Ð¾Ñ Ð´Ð¾Ð»Ð¶ÐµÐ½
        Ð¿Ð¾Ð»ÑÑÐ¸ÑÑ Ð¿Ð¾Ð½ÑÑÐ½ÑÐ¹ SavvyResponse(success=False, error=...)
        Ð²Ð¼ÐµÑÑÐ¾ Ð¿Ð°Ð´ÐµÐ½Ð¸Ñ ÑÐµÐ½Ð´Ð»ÐµÑÐ°.
        """

        try:
            return self._process(request)
        except Exception as error:  # noqa: BLE001
            return SavvyResponse(
                success=False,
                error=f"{type(error).__name__}: {error}",
            )

    # =========================
    # PIPELINE
    # =========================

    def _process(self, request: SavvyRequest) -> SavvyResponse:
        user = request.user or UserContext(
            region=self.config.default_region,
            currency=self.config.default_currency,
        )

        input_type, raw_text = self._resolve_input(request)

        intent = detect_intent(text=raw_text, input_type=input_type)

        # =========================
        # ÐÐÐÐÐ ÐÐ: Ð¾ÑÐ´ÐµÐ»ÑÐ½Ð°Ñ Ð²ÐµÑÐºÐ°, Ð±ÐµÐ· ÑÑÑÐ¾Ð³Ð¾Ð³Ð¾ ÑÐ¾Ð²Ð°ÑÐ° Ð´Ð»Ñ ÑÑÐ°Ð²Ð½ÐµÐ½Ð¸Ñ
        # =========================
        if input_type == "text" and is_gift_request(raw_text):
            return self._process_gift(raw_text, user)

        product = identify_product(text=raw_text, input_type=input_type)
        product_dna = build_product_dna(product, user=user)
        search_plan = build_search_plan(product_dna)

        data: dict[str, Any] = {
            "region": user.region,
            "currency": user.currency,
            "product": product,
            "product_dna": product_dna,
            "search_plan": search_plan,
            "offers": [],
            "regions_compared": [],
            "deal_analysis": self._empty_deal(),
        }

        # Ð¤Ð¾ÑÐ¾ ÑÐµÐ¹ÑÐ°Ñ Ð´Ð°ÑÑ ÑÐ¾Ð»ÑÐºÐ¾ Product DNA: ÑÐµÐ°Ð»ÑÐ½Ð¾Ð³Ð¾ Ð¿Ð¾Ð¸ÑÐºÐ° Ð¿Ð¾
        # Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ñ (reverse image search) Ð² Ð¿ÑÐ¾ÐµÐºÑÐµ ÐµÑÑ Ð½ÐµÑ.
        # Ð§ÐµÑÑÐ½Ð¾ Ð¾ÑÑÐ°Ð½Ð°Ð²Ð»Ð¸Ð²Ð°ÐµÐ¼ÑÑ Ð·Ð´ÐµÑÑ, Ð° Ð½Ðµ Ð¿ÑÐ¸ÑÐ²Ð¾ÑÑÐµÐ¼ÑÑ, ÑÑÐ¾
        # ÑÑÐ¾-ÑÐ¾ Ð½Ð°ÑÐ»Ð¸.
        if input_type == "photo":
            return SavvyResponse(success=True, intent=intent, data=data)

        queries = search_plan.get("queries") or (
            [raw_text] if raw_text else []
        )

        if not queries:
            return SavvyResponse(success=True, intent=intent, data=data)

        region = search_plan.get("region") or user.region
        currency = search_plan.get("currency") or user.currency
        budget = search_plan.get("budget") or {}
        international = search_plan.get("international", True)

        regions = regions_to_search(region, international=international)
        data["regions_compared"] = regions

        search_results = self._search_all_regions(
            queries=queries,
            regions=regions,
            currency=currency,
            budget=budget,
        )

        offers = self._extract_offers(search_results)

        if not offers:
            return SavvyResponse(success=True, intent=intent, data=data)

        offers = normalize_offers(offers)
        offers = normalize_offers_currency(
            offers,
            target_currency=currency,
            converter=self.currency_converter,
        )
        offers = [
            estimate_logistics(offer, destination_region=region)
            for offer in offers
        ]
        offers = [apply_real_cost(offer) for offer in offers]

        matched_offers = self._match_offers(product_dna, offers)
        data["offers"] = matched_offers

        if not matched_offers:
            return SavvyResponse(success=True, intent=intent, data=data)

        deal_analysis = self.deal_engine.evaluate(
            offers=matched_offers,
            budget=budget.get("max"),
            budget_currency=budget.get("currency") or currency,
            requested_condition=product_dna.get("condition") or "any",
        )
        data["deal_analysis"] = deal_analysis

        return SavvyResponse(success=True, intent=intent, data=data)

    def _process_gift(
        self,
        raw_text: Optional[str],
        user: UserContext,
    ) -> SavvyResponse:

        gift_request = extract_gift_request(raw_text)

        region = user.region
        currency = gift_request.get("currency") or user.currency

        suggestions = self.gift_recommender.recommend(
            gift_request=gift_request,
            region=region,
            currency=currency,
            international=True,
        )

        return SavvyResponse(
            success=True,
            intent="gift",
            data={
                "region": region,
                "currency": currency,
                "gift_request": gift_request,
                "gift_suggestions": suggestions,
            },
        )

    # =========================
    # HELPERS
    # =========================

    @staticmethod
    def _resolve_input(
        request: SavvyRequest,
    ) -> tuple[str, Optional[str]]:
        """ÐÐ¿ÑÐµÐ´ÐµÐ»ÑÐµÑ ÑÐ¸Ð¿ Ð²ÑÐ¾Ð´Ð° Ð¸ Ð¸Ð·Ð²Ð»ÐµÐºÐ°ÐµÑ ÑÐµÐºÑÑ, Ð´Ð¾ÑÑÑÐ¿Ð½ÑÐ¹ Ð´Ð»Ñ intent/identity."""

        if request.url:
            return "url", request.url

        if request.image is not None:
            return "photo", None

        text = (request.text or "").strip()
        return "text", (text or None)

    def _search_all_regions(
        self,
        queries: list[str],
        regions: list[str],
        currency: str,
        budget: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        ÐÑÐµÑ Ð² Ð´Ð¾Ð¼Ð°ÑÐ½ÐµÐ¼ ÑÐµÐ³Ð¸Ð¾Ð½Ðµ Ð¿Ð¾Ð»Ð½ÑÐ¼ Ð½Ð°Ð±Ð¾ÑÐ¾Ð¼ Ð·Ð°Ð¿ÑÐ¾ÑÐ¾Ð², Ð° Ð²
        Ð´Ð¾Ð¿Ð¾Ð»Ð½Ð¸ÑÐµÐ»ÑÐ½ÑÑ ÑÐµÐ³Ð¸Ð¾Ð½Ð°Ñ (ÑÐ¼. `region.groups.regions_to_search`)
        â ÑÐ¾Ð»ÑÐºÐ¾ Ð¾ÑÐ½Ð¾Ð²Ð½ÑÐ¼Ð¸ 1-2 Ð·Ð°Ð¿ÑÐ¾ÑÐ°Ð¼Ð¸, ÑÑÐ¾Ð±Ñ Ð½Ðµ Ð¿Ð»Ð¾Ð´Ð¸ÑÑ Ð»Ð¸ÑÐ½Ð¸Ðµ
        ÑÐµÑÐµÐ²ÑÐµ Ð²ÑÐ·Ð¾Ð²Ñ Ð½Ð° ÐºÐ°Ð¶Ð´Ð¾Ðµ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ Ð¿Ð¾Ð»ÑÐ·Ð¾Ð²Ð°ÑÐµÐ»Ñ.
        """

        home_region, *extra_regions = regions

        home_results = sweep_regions(
            search_engine=self.search_engine,
            queries=queries,
            regions=[home_region],
            currency=currency,
            budget=budget,
        )

        if not extra_regions:
            return home_results

        sweep_queries = queries[:2]

        extra_results = sweep_regions(
            search_engine=self.search_engine,
            queries=sweep_queries,
            regions=extra_regions,
            currency=currency,
            budget=budget,
        )

        return home_results + extra_results

    def _extract_offers(
        self,
        search_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        ÐÑÐµÐ²ÑÐ°ÑÐ°ÐµÑ ÑÐµÐ·ÑÐ»ÑÑÐ°ÑÑ Ð¿Ð¾Ð¸ÑÐºÐ° Ð² Ð¾ÑÑÐµÑÑ.

        ÐÑÑÐ¾ÑÐ½Ð¸ÐºÐ¸ Ð±ÑÐ²Ð°ÑÑ Ð´Ð²ÑÑ Ð²Ð¸Ð´Ð¾Ð²:
        - ÑÐ¶Ðµ Ð³Ð¾ÑÐ¾Ð²ÑÐ¹ Ð¾ÑÑÐµÑ (Ð½Ð°Ð¿ÑÐ¸Ð¼ÐµÑ DemoAdapter Ð¾ÑÐ´Ð°ÑÑ ÑÐµÐ½Ñ Ð¸
          Ð¿ÑÐ¾Ð´Ð°Ð²ÑÐ° ÑÑÐ°Ð·Ñ, Ð±ÐµÐ· Ð¾ÑÐ´ÐµÐ»ÑÐ½Ð¾Ð¹ ÑÑÑÐ°Ð½Ð¸ÑÑ);
        - "ÑÑÑÐ°Ñ" ÑÑÑÐ»ÐºÐ° (Ð½Ð°Ð¿ÑÐ¸Ð¼ÐµÑ DuckDuckGoAdapter), ÐºÐ¾ÑÐ¾ÑÑÑ Ð½ÑÐ¶Ð½Ð¾
          Ð´Ð¾Ð³ÑÑÐ·Ð¸ÑÑ Ð¸ ÑÐ°Ð·Ð¾Ð±ÑÐ°ÑÑ ÑÐµÑÐµÐ· OfferExtractor.

        ÐÑÐ¸Ð±ÐºÐ° Ð¾Ð´Ð½Ð¾Ð³Ð¾ Ð¸ÑÑÐ¾ÑÐ½Ð¸ÐºÐ° Ð½Ðµ Ð´Ð¾Ð»Ð¶Ð½Ð° Ð¾ÑÑÐ°Ð½Ð°Ð²Ð»Ð¸Ð²Ð°ÑÑ Ð¾ÑÑÐ°Ð»ÑÐ½ÑÐµ â
        ÑÐ¾Ñ Ð¶Ðµ Ð¿ÑÐ¸Ð½ÑÐ¸Ð¿ Ð¾ÑÐºÐ°Ð·Ð¾ÑÑÑÐ¾Ð¹ÑÐ¸Ð²Ð¾ÑÑÐ¸, ÑÑÐ¾ Ð¸ Ð² GlobalSearchEngine.
        """

        offers: list[dict[str, Any]] = []

        for result in search_results:
            if not isinstance(result, dict):
                continue

            looks_like_offer = (
                result.get("price") is not None
                or isinstance(result.get("product"), dict)
            )

            if looks_like_offer:
                offers.append(result)
                continue

            url = result.get("url")
            if not url:
                continue

            try:
                extracted = self.extractor.extract(url, fallback=result)
            except Exception:
                # ÐÐ´Ð½Ð° ÑÐ¿Ð°Ð²ÑÐ°Ñ ÑÑÑÐ°Ð½Ð¸ÑÐ° Ð½Ðµ Ð´Ð¾Ð»Ð¶Ð½Ð° ÑÐ¾Ð½ÑÑÑ Ð²ÐµÑÑ Ð·Ð°Ð¿ÑÐ¾Ñ.
                continue

            if extracted:
                if not extracted.get("region"):
                    extracted["region"] = result.get("region")
                offers.append(extracted)

        return offers

    def _match_offers(
        self,
        product_dna: dict[str, Any],
        offers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        ÐÑÐ¾Ð³Ð¾Ð½ÑÐµÑ ÐºÐ°Ð¶Ð´ÑÐ¹ Ð¾ÑÑÐµÑ ÑÐµÑÐµÐ· ProductMatcher.

        REJECTED (Ð½ÐµÑÐ¾Ð²Ð¿Ð°Ð´ÐµÐ½Ð¸Ðµ Ð¾Ð±ÑÐ·Ð°ÑÐµÐ»ÑÐ½Ð¾Ð³Ð¾ Ð°ÑÑÐ¸Ð±ÑÑÐ° Ð¸Ð»Ð¸
        Ð°ÐºÑÐµÑÑÑÐ°Ñ/Ð¸Ð½ÑÐ¾ÑÐ¼Ð°ÑÐ¸Ð¾Ð½Ð½Ð°Ñ ÑÑÑÐ°Ð½Ð¸ÑÐ°) â Ð¾ÑÑÐµÑ Ð¾ÑÐ±ÑÐ°ÑÑÐ²Ð°ÐµÑÑÑ.
        EXACT Ð¸ SIMILAR Ð¿Ð¾Ð¿Ð°Ð´Ð°ÑÑ Ð´Ð°Ð»ÑÑÐµ, Ð² DealEngine.

        ÐÐ°Ð¶Ð½Ð¾: `offer.deal_engine.DealCandidates` Ð¾ÑÐ±Ð¸ÑÐ°ÐµÑ Ð¾ÑÑÐµÑÑ Ð¿Ð¾
        Ð¿Ð»Ð¾ÑÐºÐ¸Ð¼ Ð¿Ð¾Ð»ÑÐ¼ `status` ("exact"/"similar") Ð¸ `usable is True`
        â Ð¾Ð½Ð¸ Ð²ÑÑÑÐ°Ð²Ð»ÑÑÑÑÑ Ð·Ð´ÐµÑÑ Ð¶Ðµ, Ð° Ð½Ðµ ÑÐ¾Ð»ÑÐºÐ¾ Ð²Ð½ÑÑÑÐ¸ Ð²Ð»Ð¾Ð¶ÐµÐ½Ð½Ð¾Ð³Ð¾
        `match`, Ð¸Ð½Ð°ÑÐµ DealEngine Ð½Ðµ ÑÐ²Ð¸Ð´Ð¸Ñ Ð½Ð¸ Ð¾Ð´Ð½Ð¾Ð³Ð¾ ÐºÐ°Ð½Ð´Ð¸Ð´Ð°ÑÐ°.
        """

        matched: list[dict[str, Any]] = []

        for offer in offers:
            result = self.matcher.match(product_dna, offer)

            if result.status == MatchStatus.REJECTED:
                continue

            enriched = dict(offer)
            enriched["match"] = result.to_dict()
            enriched["match_type"] = result.status.value
            enriched["status"] = result.status.value
            enriched["usable"] = enriched.get("price") is not None
            matched.append(enriched)

        return matched

    @staticmethod
    def _empty_deal() -> dict[str, Any]:
        return {
            "deal_type": "no_deal",
            "best_offer": None,
            "comparison_known": False,
            "comparison_source": None,
        }
