from .models import Offer, SearchRequest


class SearchProvider:
    """
    Базовый интерфейс поиска.

    В будущем сюда подключим реальные источники:
    Amazon, eBay, AliExpress, Ozon, Wildberries,
    магазины и другие сайты.
    """

    name = "base"

    async def search(
        self,
        request: SearchRequest,
    ) -> list[Offer]:
        raise NotImplementedError


class DemoSearchProvider(SearchProvider):
    """
    Временный тестовый источник.
    Нужен для проверки работы ядра SAVVY.
    """

    name = "demo"

    async def search(
        self,
        request: SearchRequest,
    ) -> list[Offer]:

        currency = request.currency or "EUR"

        return [
            Offer(
                title="SAVVY Demo Product",
                seller="Demo Store",
                source=self.name,
                url="https://example.com",
                price=79.99,
                currency=currency,
                shipping_cost=5.00,
                delivery_days=7,
                seller_rating=4.7,
            ),
            Offer(
                title="SAVVY Demo Alternative",
                seller="Alternative Store",
                source=self.name,
                url="https://example.com/alternative",
                price=69.99,
                currency=currency,
                shipping_cost=12.00,
                delivery_days=10,
                seller_rating=4.4,
            ),
        ]


class SearchOrchestrator:
    """
    Управляет всеми источниками поиска.
    """

    def __init__(
        self,
        providers: list[SearchProvider],
    ):
        self.providers = providers

    async def search(
        self,
        request: SearchRequest,
    ) -> list[Offer]:

        offers: list[Offer] = []

        for provider in self.providers:
            try:
                provider_offers = await provider.search(
                    request
                )
                offers.extend(provider_offers)

            except Exception as exc:
                print(
                    f"[SAVVY] "
                    f"{provider.name} error: {exc}"
                )

        return [
            offer
            for offer in offers
            if offer.available
        ]