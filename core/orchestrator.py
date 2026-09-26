from __future__ import annotations

from typing import Any, Optional

from core.config import SavvyConfig
from core.models import SavvyRequest, SavvyResponse, UserContext

from intent.detector import detect_intent

from product.identity import identify_product
from product.dna import build_product_dna
from product.query import build_search_plan

from search.engine import GlobalSearchEngine
from search.adapters.demo import DemoAdapter
from search.adapters.duckduckgo import DuckDuckGoAdapter

from offer.extractor import OfferExtractor
from offer.normalizer import normalize_offers
from offer.deal_engine import DealEngine

from matching.matcher import ProductMatcher
from matching.result import MatchStatus


class SavvyCore:
    """
    Главная точка входа SAVVY SENSE.

    До этого рефакторинга каждый из следующих слоёв существовал как
    отдельный, полностью рабочий, но никак не связанный модуль:

        intent.detector       -> определение намерения
        product.identity/dna  -> понимание запроса ("Product DNA")
        product.query         -> построение плана поиска
        search.engine         -> опрос источников (адаптеры)
        offer.extractor       -> разбор товарных страниц
        matching.matcher      -> строгое сопоставление товара и оффера
        offer.deal_engine     -> оценка бюджета/состояния/риска/качества

    `core/orchestrator.py` — единственное место, которое обязано их
    соединять. Раньше оно определяло класс `SavvyOrchestrator` с
    методом `run()`, которого никто не вызывал, и на который ничего
    не ссылалось: `bot.py` импортировал несуществующий `SavvyCore`
    и вызывал несуществующий `.process()`. Этот файл — настоящая,
    рабочая реализация того контракта, который `bot.py` уже ожидает.
    """

    def __init__(
        self,
        config: Optional[SavvyConfig] = None,
        search_engine: Optional[Any] = None,
        extractor: Optional[Any] = None,
        matcher: Optional[Any] = None,
        deal_engine: Optional[Any] = None,
    ) -> None:
        self.config = config or SavvyConfig.load()

        # Каждая зависимость может быть подменена (тесты, новый
        # источник поиска и т.д.) — SavvyCore не обязан знать,
        # как именно устроены его составные части.
        self.search_engine = search_engine or GlobalSearchEngine(
            adapters=[DemoAdapter(), DuckDuckGoAdapter()],
        )
        self.extractor = extractor or OfferExtractor()
        self.matcher = matcher or ProductMatcher()
        self.deal_engine = deal_engine or DealEngine()

    # =========================
    # PUBLIC API
    # =========================

    def process(self, request: SavvyRequest) -> SavvyResponse:
        """
        Единственная публичная точка входа, которую использует bot.py.

        Никогда не бросает исключение наружу: Telegram-бот должен
        получить понятный SavvyResponse(success=False, error=...)
        вместо падения хендлера.
        """

        try:
            return self._process(request)
        except Exception as error:  # noqa: BLE001
            return SavvyResponse(
                success=False,
                error=f"{type(error).__name__}: {error}",
            )

    # =========================
    # PIPELINE
    # =========================

    def _process(self, request: SavvyRequest) -> SavvyResponse:
        user = request.user or UserContext(
            region=self.config.default_region,
            currency=self.config.default_currency,
        )

        input_type, raw_text = self._resolve_input(request)

        intent = detect_intent(text=raw_text, input_type=input_type)

        product = identify_product(text=raw_text, input_type=input_type)
        product_dna = build_product_dna(product, user=user)
        search_plan = build_search_plan(product_dna)

        data: dict[str, Any] = {
            "product": product,
            "product_dna": product_dna,
            "search_plan": search_plan,
            "offers": [],
            "deal_analysis": self._empty_deal(),
        }

        # Фото сейчас даёт только Product DNA: реального поиска по
        # изображению (reverse image search) в проекте ещё нет.
        # Честно останавливаемся здесь, а не притворяемся, что
        # что-то нашли.
        if input_type == "photo":
            return SavvyResponse(success=True, intent=intent, data=data)

        queries = search_plan.get("queries") or (
            [raw_text] if raw_text else []
        )

        if not queries:
            return SavvyResponse(success=True, intent=intent, data=data)

        region = search_plan.get("region") or user.region
        currency = search_plan.get("currency") or user.currency
        budget = search_plan.get("budget") or {}

        search_results = self.search_engine.search(
            queries=queries,
            region=region,
            currency=currency,
            budget=budget,
        )

        offers = self._extract_offers(search_results)

        if not offers:
            return SavvyResponse(success=True, intent=intent, data=data)

        offers = normalize_offers(offers)

        matched_offers = self._match_offers(product_dna, offers)
        data["offers"] = matched_offers

        if not matched_offers:
            return SavvyResponse(success=True, intent=intent, data=data)

        deal_analysis = self.deal_engine.evaluate(
            offers=matched_offers,
            budget=budget.get("max"),
            budget_currency=budget.get("currency") or currency,
            requested_condition=product_dna.get("condition") or "any",
        )
        data["deal_analysis"] = deal_analysis

        return SavvyResponse(success=True, intent=intent, data=data)

    # =========================
    # HELPERS
    # =========================

    @staticmethod
    def _resolve_input(
        request: SavvyRequest,
    ) -> tuple[str, Optional[str]]:
        """Определяет тип входа и извлекает текст, доступный для intent/identity."""

        if request.url:
            return "url", request.url

        if request.image is not None:
            return "photo", None

        text = (request.text or "").strip()
        return "text", (text or None)

    def _extract_offers(
        self,
        search_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Превращает результаты поиска в офферы.

        Источники бывают двух видов:
        - уже готовый оффер (например DemoAdapter отдаёт цену и
          продавца сразу, без отдельной страницы);
        - "сырая" ссылка (например DuckDuckGoAdapter), которую нужно
          догрузить и разобрать через OfferExtractor.

        Ошибка одного источника не должна останавливать остальные —
        тот же принцип отказоустойчивости, что и в GlobalSearchEngine.
        """

        offers: list[dict[str, Any]] = []

        for result in search_results:
            if not isinstance(result, dict):
                continue

            looks_like_offer = (
                result.get("price") is not None
                or isinstance(result.get("product"), dict)
            )

            if looks_like_offer:
                offers.append(result)
                continue

            url = result.get("url")
            if not url:
                continue

            try:
                extracted = self.extractor.extract(url, fallback=result)
            except Exception:
                # Одна упавшая страница не должна ронять весь запрос.
                continue

            if extracted:
                offers.append(extracted)

        return offers

    def _match_offers(
        self,
        product_dna: dict[str, Any],
        offers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Прогоняет каждый оффер через ProductMatcher.

        REJECTED (несовпадение обязательного атрибута или
        аксессуар/информационная страница) — оффер отбрасывается.
        EXACT и SIMILAR попадают дальше, в DealEngine, с приложенным
        результатом сопоставления в ключе "match".
        """

        matched: list[dict[str, Any]] = []

        for offer in offers:
            result = self.matcher.match(product_dna, offer)

            if result.status == MatchStatus.REJECTED:
                continue

            enriched = dict(offer)
            enriched["match"] = result.to_dict()
            matched.append(enriched)

        return matched

    @staticmethod
    def _empty_deal() -> dict[str, Any]:
        return {
            "deal_type": "no_deal",
            "best_offer": None,
            "comparison_known": False,
            "comparison_source": None,
        }
