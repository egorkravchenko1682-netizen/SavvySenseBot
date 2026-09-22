from .decision import (
    calculate_score,
    choose_best_deal,
    explain_decision,
    make_decision,
)
from .intent import build_search_request
from .models import SearchResult, UserProfile
from .offers import filter_offers, sort_by_real_cost
from .search import SearchOrchestrator


class SavvyEngine:
    """
    Центральное ядро SAVVY SENSE.

    Получает запрос пользователя и проходит
    через весь pipeline:
    
    запрос
      ↓
    intent
      ↓
    поиск
      ↓
    фильтрация
      ↓
    real cost
      ↓
    cheapest
      ↓
    best deal
      ↓
    SAVVY Score
      ↓
    BUY / WAIT / SKIP
    """

    def __init__(
        self,
        search_orchestrator: SearchOrchestrator,
    ):
        self.search_orchestrator = search_orchestrator

    async def search(
        self,
        query: str,
        profile: UserProfile,
    ) -> SearchResult:

        # 1. Понимаем запрос пользователя
        request = build_search_request(
            query,
            profile,
        )

        # 2. Ищем предложения
        offers = await self.search_orchestrator.search(
            request
        )

        # 3. Фильтруем неподходящие предложения
        offers = filter_offers(
            offers,
            request,
        )

        # 4. Сортируем по полной стоимости
        offers = sort_by_real_cost(
            offers
        )

        result = SearchResult(
            request=request,
            offers=offers,
        )

        # 5. Самое дешёвое предложение
        if offers:
            result.cheapest = offers[0]

        # 6. Лучшее сочетание условий
        result.best_deal = choose_best_deal(
            offers
        )

        # 7. SAVVY Score + решение
        if result.best_deal:

            result.savvy_score = calculate_score(
                result.best_deal
            )

            result.decision = make_decision(
                result.best_deal
            )

            result.explanation = (
                explain_decision(
                    result.best_deal,
                    result.decision,
                )
            )

        return result