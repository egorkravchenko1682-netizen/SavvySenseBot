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

from search.adapters import (
    DemoAdapter,
    DuckDuckGoAdapter,
)

from offer import (
    normalize_offers,
    OfferExtractor,
)

from currency import CurrencyConverter

from cost.calculator import (
    calculate_offers_real_cost,
)

from deal import DealEngine

from matching import ProductMatcher


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

        self.search_engine.add_adapter(
            DuckDuckGoAdapter(
                max_results=5
            )
        )

        self.offer_extractor = (
            OfferExtractor()
        )

        self.product_matcher = (
            ProductMatcher()
        )

        self.currency_converter = (
            CurrencyConverter()
        )

        self.deal_engine = (
            DealEngine(
                max_results=(
                    self.config.max_results
                )
            )
        )

    def process(
        self,
        request: SavvyRequest,
    ) -> SavvyResponse:

        self._prepare_request(
            request
        )

        input_data = (
            self._parse_input(
                request
            )
        )

        intent = detect_intent(
            text=request.text,
            input_type=input_data[
                "type"
            ],
        )

        product = identify_product(
            text=request.text,
            input_type=input_data[
                "type"
            ],
        )

        product_dna = build_product_dna(
            product=product,
            user=request.user,
        )

        search_plan = build_search_plan(
            product_dna=product_dna,
        )

        raw_offers = []

        if search_plan.get(
            "queries"
        ):

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

        print(
            "SAVVY DEBUG: "
            f"raw offers = {len(raw_offers)}"
        )

        enriched_offers = []

        for offer in raw_offers:

            url = offer.get(
                "url"
            )

            if not url:

                enriched_offers.append(
                    offer
                )

                continue

            extracted = (
                self.offer_extractor.extract(
                    url=url,
                    fallback=offer,
                )
            )

            enriched_offer = {
                **offer,

                "product": {
                    "title":
                        extracted.get(
                            "title"
                        )
                        or offer.get(
                            "title"
                        ),

                    "brand":
                        extracted.get(
                            "brand"
                        )
                        or offer.get(
                            "brand"
                        ),

                    "category":
                        offer.get(
                            "category"
                        ),

                    "product_type":
                        offer.get(
                            "product_type"
                        ),

                    "model":
                        offer.get(
                            "model"
                        ),

                    "attributes":
                        offer.get(
                            "attributes",
                            {},
                        ),
                },

                "price":
                    extracted.get(
                        "price"
                    )
                    if extracted.get(
                        "price"
                    ) is not None
                    else offer.get(
                        "price"
                    ),

                "currency":
                    extracted.get(
                        "currency"
                    )
                    or offer.get(
                        "currency"
                    ),

                "seller":
                    extracted.get(
                        "seller"
                    )
                    or offer.get(
                        "seller"
                    ),

                "availability":
                    extracted.get(
                        "availability"
                    )
                    or offer.get(
                        "availability"
                    ),

                "description":
                    extracted.get(
                        "description"
                    )
                    or offer.get(
                        "description"
                    ),

                "image":
                    extracted.get(
                        "image"
                    )
                    or offer.get(
                        "image"
                    ),

                "url":
                    extracted.get(
                        "url"
                    )
                    or url,

                "extracted":
                    extracted.get(
                        "extracted",
                        False,
                    ),
            }

            enriched_offers.append(
                enriched_offer
            )

        raw_offers = (
            enriched_offers
        )

        matched_offers = []
        rejected_offers = []

        for offer in raw_offers:

            match = (
                self.product_matcher.match(
                    product=product,
                    offer=offer,
                )
            )

            title = (
                offer.get(
                    "product",
                    {}
                ).get(
                    "title"
                )
                if isinstance(
                    offer.get(
                        "product"
                    ),
                    dict,
                )
                else offer.get(
                    "title"
                )
            )

            print(
                "SAVVY MATCH: "
                f"{title} | "
                f"match_result={match}"
            )

            enriched_offer = {
                **offer,

                "match_result":
                    match,
            }

            if match.is_rejected:

                rejected_offers.append(
                    enriched_offer
                )

                continue

            matched_offers.append(
                enriched_offer
            )

        print(
            "SAVVY DEBUG: "
            f"matched={len(matched_offers)}, "
            f"rejected={len(rejected_offers)}"
        )

        offers = normalize_offers(
            matched_offers
        )

        offers = (
            calculate_offers_real_cost(
                offers=offers,
                target_currency=(
                    request.user.currency
                ),
                converter=(
                    self.currency_converter
                ),
            )
        )

        deal_analysis = (
            self.deal_engine.analyze(
                offers=offers,
                product=product,
            )
        )

        classified_offers = (
            deal_analysis.get(
                "classified_offers",
                [],
            )
        )

        if classified_offers:

            offers = (
                classified_offers
            )

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

                "matched_offers":
                    matched_offers,

                "rejected_offers":
                    rejected_offers,

                "offers":
                    offers,

                "deal_analysis":
                    deal_analysis,

                "matching": {
                    "total_candidates":
                        len(raw_offers),

                    "accepted":
                        len(matched_offers),

                    "rejected":
                        len(rejected_offers),

                    "exact":
                        sum(
                            1
                            for offer
                            in matched_offers
                            if (
                                offer.get(
                                    "match_result"
                                ).is_exact
                            )
                        ),

                    "similar":
                        sum(
                            1
                            for offer
                            in matched_offers
                            if (
                                offer.get(
                                    "match_result"
                                ).is_similar
                            ),
                        ),
                },
            },
        )

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