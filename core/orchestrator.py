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
        # Подготавливаем пользователя
        self._prepare_request(request)
        # Определяем тип входных данных
        input_data = self._parse_input(request)
        # Определяем намерение пользователя
        intent = detect_intent(
            text=request.text,
            input_type=input_data["type"],
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
        """
        Создаёт UserContext,
        если пользователь ещё не передан.
        """
        if request.user is None:
            request.user = UserContext(
                region=self.config.default_region,
                currency=self.config.default_currency,
            )
    def _parse_input(
        self,
        request: SavvyRequest,
    ) -> dict:
        """
        Передаёт входные данные
        соответствующему INPUT-модулю.
        """
        # Сначала проверяем URL
        if request.url:
            return parse_url(request.url)
        # Затем фотографию
        if request.image is not None:
            return parse_photo(request.image)
        # Затем текст
        if request.text:
            return parse_text(request.text)
        # Если ничего нет
        return {
            "type": "unknown",
            "value": None,
            "valid": False,
        }