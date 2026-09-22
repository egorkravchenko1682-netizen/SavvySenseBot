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

        intent = self._detect_basic_intent(
            request,
            input_data,
        )

        return SavvyResponse(
            success=True,
            intent=intent,
            data={
                "region": request.user.region,
                "currency": request.user.currency,
                "input": input_data,
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

    def _detect_basic_intent(
        self,
        request: SavvyRequest,
        input_data: dict,
    ) -> str:

        if input_data["type"] == "url":
            return "product_search"

        if input_data["type"] == "photo":
            return "product_search"

        if not request.text:
            return "unknown"

        text = request.text.lower()

        if (
            "сравни" in text
            or "сравнить" in text
        ):
            return "compare"

        if (
            "дешевле" in text
            or "дешевый" in text
        ):
            return "cheaper"

        if (
            "стоит ли" in text
            or "выгодно" in text
        ):
            return "check"

        if (
            "следи" in text
            or "отслеживай" in text
        ):
            return "track"

        return "product_search"