from typing import Any


class DealEngine:
    """
    Анализирует нормализованные предложения SAVVY.

    Предложения без известной цены не считаются
    дешевле предложений с известной ценой.
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

        budget = product.get("budget")

        target_currency = (
            product.get("currency")
            or "USD"
        )

        for offer in offers:

            product_data = offer.get(
                "product",
                {},
            )

            total_cost = offer.get(
                "total_cost"
            )

            cost_known = (
                offer.get(
                    "cost_known"
                )
                and total_cost is not None
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
                    and cost_known
                    and offer_currency
                    == target_currency
                    and float(total_cost)
                    > float(budget)
                ):

                    over_budget.append(
                        classified_offer
                    )

            else:

                similar_matches.append(
                    classified_offer
                )

        exact_matches.sort(
            key=self._sort_key
        )

        similar_matches.sort(
            key=self._sort_key
        )

        over_budget.sort(
            key=self._sort_key
        )

        cheaper = []

        priced_exact = [
            offer
            for offer in exact_matches
            if offer.get(
                "cost_known"
            )
            and offer.get(
                "total_cost"
            ) is not None
        ]

        if priced_exact:

            cheapest_cost = min(
                float(
                    offer.get(
                        "total_cost"
                    )
                )
                for offer in priced_exact
            )

            for offer in priced_exact:

                if (
                    float(
                        offer.get(
                            "total_cost"
                        )
                    )
                    <= cheapest_cost
                ):

                    cheaper.append(
                        offer
                    )

        best_exact = None

        if priced_exact:

            best_exact = priced_exact[0]

        return {
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

    @staticmethod
    def _sort_key(
        offer: dict[str, Any],
    ):

        cost_known = (
            offer.get("cost_known")
            and offer.get("total_cost")
            is not None
        )

        if not cost_known:

            return (
                1,
                float("inf"),
            )

        return (
            0,
            float(
                offer.get(
                    "total_cost"
                )
            ),
        )

    def _is_exact_match(
        self,
        product: dict[str, Any],
        offer_product: dict[str, Any],
    ) -> bool:

        requested_name = product.get(
            "name"
        )

        offer_title = offer_product.get(
            "title"
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

        if requested in offered:
            return True

        if offered in requested:
            return True

        requested_brand = product.get(
            "brand"
        )

        offered_brand = offer_product.get(
            "brand"
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