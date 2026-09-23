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

from matching import (
    ProductMatcher,
    RejectedFilter,
)


class SavvyCore:

    def __init__(
        self,
        config: Optional[SavvyConfig] = None,
    ):
        self.config = (
            config or SavvyConfig.load()
        )

        self.search_engine = GlobalSearchEngine()

        self.search_engine.add_adapter(
            DemoAdapter()
        )

        self.search_engine.add_adapter(
            DuckDuckGoAdapter(
                max_results=5
            )
        )

        self.offer_extractor = OfferExtractor()

        self.product_matcher = ProductMatcher()

        self.rejected_filter = RejectedFilter()

        self.currency_converter = CurrencyConverter()

        self.deal_engine = DealEngine(
            max_results=self.config.max_results
        )

    def process(
        self,
        request: SavvyRequest,
    ) -> SavvyResponse:

        # =====================================================
        # REQUEST
        # =====================================================

        self._prepare_request(
            request
        )

        # =====================================================
        # INPUT
        # =====================================================

        input_data = self._parse_input(
            request
        )

        # =====================================================
        # INTENT
        # =====================================================

        intent = detect_intent(
            text=request.text,
            input_type=input_data["type"],
        )

        # =====================================================
        # PRODUCT IDENTITY
        # =====================================================

        product = identify_product(
            text=request.text,
            input_type=input_data["type"],
        )

        # =====================================================
        # PRODUCT DNA
        # =====================================================

        product_dna = build_product_dna(
            product=product,
            user=request.user,
        )

        # =====================================================
        # SEARCH PLAN
        # =====================================================

        search_plan = build_search_plan(
            product_dna=product_dna,
        )

        # =====================================================
        # GLOBAL SEARCH
        # =====================================================

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

        # =====================================================
        # OFFER EXTRACTION
        # =====================================================

        enriched_offers = []

        for offer in raw_offers:

            url = offer.get(
                "url"
            )

            # -------------------------------------------------
            # No URL
            # -------------------------------------------------

            if not url:

                enriched_offers.append(
                    offer
                )

                continue

            # -------------------------------------------------
            # Extract
            # -------------------------------------------------

            try:

                extracted = (
                    self.offer_extractor.extract(
                        url=url,
                        fallback=offer,
                    )
                )

            except Exception as error:

                print(
                    "Offer extraction failed: "
                    f"{url}: {error}"
                )

                extracted = {}

            # -------------------------------------------------
            # Existing fallback data
            # -------------------------------------------------

            fallback_product = (
                offer.get(
                    "product",
                    {},
                )
            )

            if not isinstance(
                fallback_product,
                dict,
            ):

                fallback_product = {}

            fallback_attributes = (
                fallback_product.get(
                    "attributes",
                    {},
                )
            )

            if not isinstance(
                fallback_attributes,
                dict,
            ):

                fallback_attributes = {}

            extracted_attributes = (
                extracted.get(
                    "attributes",
                    {},
                )
            )

            if not isinstance(
                extracted_attributes,
                dict,
            ):

                extracted_attributes = {}

            # -------------------------------------------------
            # Merge attributes
            # -------------------------------------------------

            merged_attributes = {
                **fallback_attributes,
                **extracted_attributes,
            }

            # Explicit extractor fields
            # have priority.
            for attribute in (
                "storage",
                "color",
                "size",
                "material",
                "gender",
                "condition",
                "quantity",
                "capacity",
                "voltage",
                "compatibility",
            ):

                value = extracted.get(
                    attribute
                )

                if value is not None:

                    merged_attributes[
                        attribute
                    ] = value

            # -------------------------------------------------
            # Product fields
            # -------------------------------------------------

            product_title = (
                extracted.get(
                    "title"
                )
                or fallback_product.get(
                    "title"
                )
                or offer.get(
                    "title"
                )
            )

            product_brand = (
                extracted.get(
                    "brand"
                )
                or fallback_product.get(
                    "brand"
                )
                or offer.get(
                    "brand"
                )
            )

            product_model = (
                extracted.get(
                    "model"
                )
                or fallback_product.get(
                    "model"
                )
                or offer.get(
                    "model"
                )
            )

            product_type = (
                extracted.get(
                    "product_type"
                )
                or fallback_product.get(
                    "product_type"
                )
                or offer.get(
                    "product_type"
                )
            )

            product_category = (
                extracted.get(
                    "category"
                )
                or fallback_product.get(
                    "category"
                )
                or offer.get(
                    "category"
                )
            )

            # -------------------------------------------------
            # Ensure condition is preserved
            # -------------------------------------------------

            condition = (
                extracted.get(
                    "condition"
                )
                or offer.get(
                    "condition"
                )
                or fallback_product.get(
                    "condition"
                )
                or merged_attributes.get(
                    "condition"
                )
                or "unknown"
            )

            merged_attributes[
                "condition"
            ] = condition

            # -------------------------------------------------
            # Build normalized product
            # -------------------------------------------------

            normalized_product = {

                "title":
                    product_title,

                "brand":
                    product_brand,

                "model":
                    product_model,

                "category":
                    product_category,

                "product_type":
                    product_type,

                "attributes":
                    merged_attributes,
            }

            # -------------------------------------------------
            # Build enriched offer
            # -------------------------------------------------

            enriched_offer = {
                **offer,

                "product":
                    normalized_product,

                "title":
                    product_title,

                "brand":
                    product_brand,

                "model":
                    product_model,

                "category":
                    product_category,

                "product_type":
                    product_type,

                "attributes":
                    merged_attributes,

                "price":
                    (
                        extracted.get(
                            "price"
                        )
                        if extracted.get(
                            "price"
                        ) is not None
                        else offer.get(
                            "price"
                        )
                    ),

                "currency":
                    (
                        extracted.get(
                            "currency"
                        )
                        or offer.get(
                            "currency"
                        )
                    ),

                "seller":
                    (
                        extracted.get(
                            "seller"
                        )
                        or offer.get(
                            "seller"
                        )
                    ),

                "availability":
                    (
                        extracted.get(
                            "availability"
                        )
                        or offer.get(
                            "availability"
                        )
                    ),

                "condition":
                    condition,

                "description":
                    (
                        extracted.get(
                            "description"
                        )
                        or offer.get(
                            "description"
                        )
                    ),

                "image":
                    (
                        extracted.get(
                            "image"
                        )
                        or offer.get(
                            "image"
                        )
                    ),

                "sku":
                    (
                        extracted.get(
                            "sku"
                        )
                        or offer.get(
                            "sku"
                        )
                    ),

                "mpn":
                    (
                        extracted.get(
                            "mpn"
                        )
                        or offer.get(
                            "mpn"
                        )
                    ),

                "gtin":
                    (
                        extracted.get(
                            "gtin"
                        )
                        or offer.get(
                            "gtin"
                        )
                    ),

                "url":
                    (
                        extracted.get(
                            "url"
                        )
                        or url
                    ),

                "extracted":
                    extracted.get(
                        "extracted",
                        False,
                    ),
            }

            enriched_offers.append(
                enriched_offer
            )

        raw_offers = enriched_offers

        # =====================================================
        # MATCHING
        # =====================================================

        match_results = []

        for offer in raw_offers:

            match = (
                self.product_matcher.match(
                    product=product_dna,
                    offer=offer,
                )
            )

            match_results.append(
                match
            )

            product_data = (
                offer.get(
                    "product",
                    {},
                )
            )

            if isinstance(
                product_data,
                dict,
            ):

                title = (
                    product_data.get(
                        "title",
                        "",
                    )
                )

            else:

                title = (
                    offer.get(
                        "title",
                        "",
                    )
                )

            print(
                "SAVVY MATCH: "
                f"{title} | "
                f"status="
                f"{match.status.value} | "
                f"score="
                f"{match.score}"
            )

        # =====================================================
        # REJECTED FILTER
        # =====================================================

        split_results = (
            self.rejected_filter.split(
                offers=raw_offers,
                match_results=match_results,
            )
        )

        exact_offers = (
            split_results.get(
                "exact",
                [],
            )
        )

        similar_offers = (
            split_results.get(
                "similar",
                [],
            )
        )

        rejected_offers = (
            split_results.get(
                "rejected",
                [],
            )
        )

        # -----------------------------------------------------
        # Attach MatchResult to accepted/rejected offers
        # -----------------------------------------------------

        matched_offers = []

        rejected_with_match = []

        for index, offer in enumerate(
            raw_offers
        ):

            if index >= len(
                match_results
            ):
                continue

            enriched_offer = {
                **offer,
                "match_result":
                    match_results[index],
            }

            if match_results[
                index
            ].is_rejected:

                rejected_with_match.append(
                    enriched_offer
                )

            else:

                matched_offers.append(
                    enriched_offer
                )

        rejected_offers = (
            rejected_with_match
        )

        exact_count = len(
            exact_offers
        )

        similar_count = len(
            similar_offers
        )

        print(
            "SAVVY DEBUG: "
            f"matched="
            f"{len(matched_offers)}, "
            f"rejected="
            f"{len(rejected_offers)}, "
            f"exact="
            f"{exact_count}, "
            f"similar="
            f"{similar_count}"
        )

        # =====================================================
        # NORMALIZATION
        # =====================================================

        offers = normalize_offers(
            matched_offers
        )

        # =====================================================
        # REAL COST
        # =====================================================

        offers = calculate_offers_real_cost(
            offers=offers,
            target_currency=(
                request.user.currency
            ),
            converter=(
                self.currency_converter
            ),
        )

        # =====================================================
        # DEAL ENGINE
        # =====================================================

        deal_analysis = (
            self.deal_engine.analyze(
                offers=offers,
                product=product_dna,
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

        # =====================================================
        # RESPONSE
        # =====================================================

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
                        len(
                            raw_offers
                        ),

                    "accepted":
                        len(
                            matched_offers
                        ),

                    "rejected":
                        len(
                            rejected_offers
                        ),

                    "exact":
                        exact_count,

                    "similar":
                        similar_count,
                },
            },
        )

    # =========================================================
    # REQUEST PREPARATION
    # =========================================================

    def _prepare_request(
        self,
        request: SavvyRequest,
    ):

        if request.user is None:

            request.user = UserContext(
                region=(
                    self.config.default_region
                ),
                currency=(
                    self.config.default_currency
                ),
            )

    # =========================================================
    # INPUT PARSER
    # =========================================================

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
            "type":
                "unknown",

            "value":
                None,

            "valid":
                False,
        }