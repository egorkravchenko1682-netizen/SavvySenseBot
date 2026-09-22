from typing import Optional

from .config import SavvyConfig
from .models import (
    SavvyRequest,
    SavvyResponse,
    UserContext,
)

from input import (
    parse_text,
    parse_url,
    parse_photo,
)

from intent import detect_intent

from product import (
    identify_product,
    build_product_dna,
    build_search_plan,
)

from search import GlobalSearchEngine
from search.adapters import DemoAdapter

from offer import normalize_offers

from currency import CurrencyConverter

from cost.calculator import (
    calculate_offers_real_cost,
)

from deal import DealEngine


class SavvyCore:

    def __init__(
        self,
        config: Optional[SavvyConfig] = None,
    ):

        self.config = (
            config or SavvyConfig.load()
        )

        self.search_engine = (
            GlobalSearchEngine()
        )

        self.search_engine.add_adapter(
            DemoAdapter()
        )

        self.currency_converter = (
            CurrencyConverter()
        )

        self.deal_engine = (
            DealEngine(
                max_results=self.config.max_results
            )
        )

    def process(
        self,
        request: SavvyRequest,
    ) -> SavvyResponse:

        # =========================
        # PREPARE REQUEST
        # =========================

        self._prepare_request(
            request
        )

        # =========================
        # INPUT
        # =========================

        input_data = (
            self._parse_input(request)
        )

        # =========================
        # INTENT
        # =========================

        intent = detect_intent(
            text=request.text,
            input_type=input_data["type"],
        )

        # =========================
        # PRODUCT IDENTITY
        # =========================

        product = identify_product(
            text=request.text,
            input_type=input_data["type"],
        )

        # =========================
        # PRODUCT DNA
        # =========================

        product_dna = build_product_dna(
            product=product,
            user=request.user,
        )

        # =========================
        # SEARCH PLAN
        # =========================

        search_plan = build_search_plan(
            product_dna=product_dna,
        )

        # =========================
        # GLOBAL SEARCH
        # =========================

        raw_offers = []

        if search_plan.get("queries"):

            raw_offers = (
                self.search_engine.search(
                    queries=search_plan[
                        "queries"
                    ],

                    region=search_plan.get(
                        "region",
                        request.user.region,
                    ),

                    currency=search_plan.get(
                        "currency",
                        request.user.currency,
                    ),

                    budget=search_plan.get(
                        "budget",
                        {},
                    ),
                )
            )

        # =========================
        # OFFER NORMALIZATION
        # =========================

        offers = normalize_offers(
            raw_offers
        )

        # =========================
        # REAL COST
        # =========================

        offers = calculate_offers_real_cost(
            offers=offers,

            target_currency=(
                request.user.currency
            ),

            converter=(
                self.currency_converter
            ),
        )

        # =========================
        # DEAL ENGINE
        # =========================

        deal_analysis = (
            self.deal_engine.analyze(
                offers=offers,
                product=product,
            )
        )

        # =========================
        # BLOCK 10.1
        # SYNC MATCH TYPE
        # =========================

        offers = self._apply_match_types(
            offers=offers,
            deal_analysis=deal_analysis,
        )

        # =========================
        # RESPONSE
        # =========================

        return SavvyResponse(
            success=True,

            intent=intent,

            data={

                "region":
                    request.user.region,

                "currency":
                    request.user.currency,

                "input":
                    input_data,

                "product":
                    product,

                "product_dna":
                    product_dna,

                "search_plan":
                    search_plan,

                "raw_offers":
                    raw_offers,

                "offers":
                    offers,

                "deal_analysis":
                    deal_analysis,
            },
        )

    # =========================
    # REQUEST PREPARATION
    # =========================

    def _prepare_request(
        self,
        request: SavvyRequest,
    ):

        if request.user is None:

            request.user = UserContext(
                region=(
                    self.config
                    .default_region
                ),

                currency=(
                    self.config
                    .default_currency
                ),
            )

    # =========================
    # INPUT PARSER
    # =========================

    def _parse_input(
        self,
        request: SavvyRequest,
    ) -> dict:

        if request.url:

            return parse_url(
                request.url
            )

        if request.image is not None:

            return parse_photo(
                request.image
            )

        if request.text:

            return parse_text(
                request.text
            )

        return {
            "type": "unknown",
            "value": None,
            "valid": False,
        }

    # =========================
    # BLOCK 10.1
    # APPLY DEAL MATCH TYPES
    # =========================

    def _apply_match_types(
        self,
        offers: list[dict],
        deal_analysis: dict,
    ) -> list[dict]:
        """
        Синхронизирует результат Deal Engine
        с основным списком offers.

        Ранее Deal Engine правильно определял
        exact/similar, но bot.py получал
        исходные offers без match_type.

        Теперь каждый offer получает:

        match_type = "exact"
        или
        match_type = "similar"
        """

        exact_matches = (
            deal_analysis.get(
                "exact_matches",
                [],
            )
        )

        similar_matches = (
            deal_analysis.get(
                "similar_matches",
                [],
            )
        )

        # Создаем индексы для быстрого поиска.
        exact_keys = set()
        similar_keys = set()

        for offer in exact_matches:

            exact_keys.add(
                self._offer_key(
                    offer
                )
            )

        for offer in similar_matches:

            similar_keys.add(
                self._offer_key(
                    offer
                )
            )

        updated_offers = []

        for offer in offers:

            key = self._offer_key(
                offer
            )

            updated_offer = {
                **offer
            }

            if key in exact_keys:

                updated_offer[
                    "match_type"
                ] = "exact"

            elif key in similar_keys:

                updated_offer[
                    "match_type"
                ] = "similar"

            else:

                updated_offer[
                    "match_type"
                ] = "unknown"

            updated_offers.append(
                updated_offer
            )

        return updated_offers

    # =========================
    # OFFER IDENTITY
    # =========================

    @staticmethod
    def _offer_key(
        offer: dict,
    ) -> tuple:

        product = offer.get(
            "product",
            {},
        )

        return (
            str(
                offer.get(
                    "source",
                    "",
                )
            ).strip().lower(),

            str(
                product.get(
                    "title",
                    "",
                )
            ).strip().lower(),

            str(
                offer.get(
                    "seller",
                    "",
                )
            ).strip().lower(),

            str(
                offer.get(
                    "url",
                    "",
                )
            ).strip().lower(),

            round(
                float(
                    offer.get(
                        "price",
                        0,
                    )
                    or 0
                ),
                2,
            ),
        )