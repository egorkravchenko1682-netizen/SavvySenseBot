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


class SavvyCore:

    def __init__(
        self,
        config: Optional[SavvyConfig] = None,
    ):
        self.config = config or SavvyConfig.load()

    def process(
        self,
        request: SavvyRequest,
    ) -> SavvyResponse:

        self._prepare_request(request)

        input_data = self._parse_input(request)

        intent = detect_intent(
            text=request.text,
            input_type=input_data["type"],
        )

        product = identify_product(
            text=request.text,
            input_type=input_data["type"],
        )

        product_dna = build_product_dna(
            product=product,
            user=request.user,
        )

        search_plan = build_search_plan(
            product_dna=product_dna,
        )

        return SavvyResponse(
            success=True,
            intent=intent,
            data={
                "region": request.user.region,
                "currency": request.user.currency,

                "input": input_data,

                "product": product,

                "product_dna": product_dna,

                "search_plan": search_plan,
            },
        )

    def _prepare_request(
        self,
        request: SavvyRequest,
    ):

        if request.user is None:
            request.user = UserContext(
                region=self.config.default_region,
                currency=self.config.default_currency,
            )

    def _parse_input(
        self,
        request: SavvyRequest,
    ) -> dict:

        if request.url:
            return parse_url(request.url)

        if request.image is not None:
            return parse_photo(request.image)

        if request.text:
            return parse_text(request.text)

        return {
            "type": "unknown",
            "value": None,
            "valid": False,
        }