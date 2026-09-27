"""
SAVVY SENSE core package.

`SavvyCore` намеренно НЕ импортируется здесь напрямую на верхнем
уровне (см. `__getattr__` ниже) — только лениво, при первом реальном
обращении. Причина — скрытая циклическая зависимость: `core.models`
и `core.config` используются "листовыми" модулями вроде
`product/dna.py`, а `core.orchestrator` (тяжёлый модуль, который
собирает воедино intent/product/search/offer/matching/gift) сам
импортирует `product`, `gift` и другие пакеты.

Раньше `from core.models import UserContext` внутри `product/dna.py`
эту цепочку целиком: чтобы отдать `core.models`, Python сначала
обязан полностью выполнить `core/__init__.py`, а тот тянул за собой
`core.orchestrator`, который в свою очередь снова пытался
импортировать `product.dna` — тот самый модуль, что всё это запустил,
но ещё не успевший доисполниться. Если бы что-то в проекте (или его
будущие модули) импортировало `product`/`gift`/`intent` РАНЬШЕ, чем
`core`, это гарантированно падало бы с `ImportError` при циклическом
импорте. `__getattr__` ниже (PEP 562) откладывает импорт
`core.orchestrator` до момента, когда кто-то реально запрашивает
`core.SavvyCore` — к этому моменту все листовые модули уже успевают
безопасно доимпортироваться.
"""

__all__ = ["SavvyCore"]


def __getattr__(name):
    if name == "SavvyCore":
        from .orchestrator import SavvyCore

        return SavvyCore

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
