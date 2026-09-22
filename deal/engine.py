from typing import Any


class DealEngine:
    """
    Анализирует нормализованные предложения SAVVY.

    Deal Engine определяет:
    - exact match
    - similar product
    - over budget
    - best exact match

    Важно:
    classified_offers сохраняет ВСЕ предложения
    в исходном порядке и добавляет каждому
    match_type.
    """

    def __init__(
        self,
        max_results: int = 20,
    ):

        self.max_results = max_results

    def analyze(
        self,
        offers: list[dict[str, Any]],
        product: dict[str, Any],
    ) -> dict[str, Any]:

        exact_matches = []
        similar_matches = []
        over_budget = []

        classified_offers = []

        budget = product.get(
            "budget"
        )

        target_currency = (
            product.get("currency")
            or "USD"
        )

        for offer in offers:

            product_data = offer.get(
                "product",
                {},
            )

            total_cost = float(
                offer.get(
                    "total_cost",
                    0,
                )
                or 0
            )

            offer_currency = (
                offer.get(
                    "total_currency"
                )
                or offer.get(
                    "currency"
                )
                or target_currency
            )

            exact = self._is_exact_match(
                product=product,
                offer_product=product_data,
            )

            match_type = (
                "exact"
                if exact
                else "similar"
            )

            classified_offer = {
                **offer,

                "match_type":
                    match_type,
            }

            classified_offers.append(
                classified_offer
            )

            if exact:

                exact_matches.append(
                    classified_offer
                )

                if (
                    budget is not None
                    and offer_currency
                    == target_currency
                    and total_cost
                    > float(budget)
                ):

                    over_budget.append(
                        classified_offer
                    )

            else:

                similar_matches.append(
                    classified_offer
                )

        # =========================
        # SORT
        # =========================

        exact_matches.sort(
            key=lambda item:
            float(
                item.get(
                    "total_cost",
                    0,
                )
                or 0
            )
        )

        similar_matches.sort(
            key=lambda item:
            float(
                item.get(
                    "total_cost",
                    0,
                )
                or 0
            )
        )

        over_budget.sort(
            key=lambda item:
            float(
                item.get(
                    "total_cost",
                    0,
                )
                or 0
            )
        )

        # =========================
        # CHEAPER
        # =========================

        cheaper = []

        if exact_matches:

            cheapest_cost = float(
                exact_matches[0].get(
                    "total_cost",
                    0,
                )
                or 0
            )

            for offer in exact_matches:

                if float(
                    offer.get(
                        "total_cost",
                        0,
                    )
                    or 0
                ) <= cheapest_cost:

                    cheaper.append(
                        offer
                    )

        # =========================
        # BEST EXACT
        # =========================

        best_exact = (
            exact_matches[0]
            if exact_matches
            else None
        )

        # =========================
        # RESULT
        # =========================

        return {

            # Все предложения уже
            # с match_type
            "classified_offers":
                classified_offers,

            "exact_matches":
                exact_matches[
                    :self.max_results
                ],

            "cheaper":
                cheaper[
                    :self.max_results
                ],

            "similar_matches":
                similar_matches[
                    :self.max_results
                ],

            "over_budget":
                over_budget[
                    :self.max_results
                ],

            "best_exact":
                best_exact,

            "counts": {

                "exact":
                    len(exact_matches),

                "similar":
                    len(similar_matches),

                "over_budget":
                    len(over_budget),
            },
        }

    # =========================
    # EXACT MATCH
    # =========================

    def _is_exact_match(
        self,
        product: dict[str, Any],
        offer_product: dict[str, Any],
    ) -> bool:

        requested_name = (
            product.get("name")
        )

        offer_title = (
            offer_product.get("title")
        )

        if not requested_name:
            return False

        if not offer_title:
            return False

        requested = self._normalize_text(
            requested_name
        )

        offered = self._normalize_text(
            offer_title
        )

        # Полное совпадение названия
        if requested in offered:
            return True

        if offered in requested:
            return True

        # =========================
        # BRAND
        # =========================

        requested_brand = (
            product.get("brand")
        )

        offered_brand = (
            offer_product.get("brand")
        )

        if (
            requested_brand
            and offered_brand
            and self._normalize_text(
                requested_brand
            )
            != self._normalize_text(
                offered_brand
            )
        ):
            return False

        # =========================
        # STORAGE
        # =========================

        requested_attributes = (
            product.get(
                "attributes",
                {},
            )
        )

        requested_storage = (
            requested_attributes.get(
                "storage"
            )
        )

        if requested_storage:

            if self._normalize_text(
                requested_storage
            ) not in offered:

                return False

        # =========================
        # BRAND IN TITLE
        # =========================

        normalized_brand = (
            self._normalize_text(
                requested_brand or ""
            )
        )

        if normalized_brand:

            return (
                normalized_brand
                in offered
            )

        return False

    # =========================
    # NORMALIZE TEXT
    # =========================

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:

        return (
            str(value)
            .lower()
            .replace("-", " ")
            .replace("_", " ")
            .strip()
        )