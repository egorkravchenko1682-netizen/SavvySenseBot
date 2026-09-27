from __future__ import annotations

from typing import Any, Optional

from product.identity import extract_budget

# Слова-триггеры "это запрос на подарок", а не на конкретный товар.
GIFT_TRIGGER_WORDS = (
    "подарок",
    "подарить",
    "подарунок",
    "gift",
    "презент",
)

# Порядок важен: более специфичные маркеры проверяются раньше, чтобы
# "подруге" не спутать с "другу".
_RECIPIENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("girlfriend", ("девушке", "девушки", "девушку", "жене", "жены", "супруге")),
    ("boyfriend", ("парню", "парня", "мужу", "мужа", "супругу", "молодому человеку")),
    ("brother", ("брату", "брата", "братику", "братишке")),
    ("sister", ("сестре", "сестры", "сестричке", "сестрёнке")),
    ("mother", ("маме", "мамы", "матери", "мамуле")),
    ("father", ("папе", "папы", "отцу", "папуле")),
    ("friend_female", ("подруге", "подруги", "подружке")),
    ("friend_male", ("другу", "друга", "приятелю")),
    ("colleague", ("коллеге", "коллеги", "начальнику", "начальнице")),
    ("child", ("сыну", "сына", "дочке", "дочери", "ребенку", "ребёнку")),
)

_OCCASION_PATTERNS: dict[str, tuple[str, ...]] = {
    "birthday": ("день рождения", "днем рождения", "днём рождения", " др "),
    "new_year": ("новый год", "новому году", "нг"),
    "march8": ("8 марта", "8марта"),
    "wedding": ("свадьб",),
    "valentine": ("14 февраля", "день влюбленных", "день влюблённых"),
}


def is_gift_request(text: Optional[str]) -> bool:
    """
    Определяет, что запрос — это просьба подобрать подарок, а не
    поиск конкретного товара.
    """

    text_l = (text or "").lower()
    return any(word in text_l for word in GIFT_TRIGGER_WORDS)


def extract_gift_request(text: Optional[str]) -> dict[str, Any]:
    """
    Извлекает из текста получателя, повод и бюджет подарка.

    Неизвестные значения не выдумываются: получатель по умолчанию —
    "generic" (универсальный подарок), повод — None, если явно не
    назван.
    """

    text_l = (text or "").lower()

    recipient = "generic"

    for key, markers in _RECIPIENT_PATTERNS:
        if any(marker in text_l for marker in markers):
            recipient = key
            break

    occasion = None

    for key, markers in _OCCASION_PATTERNS.items():
        if any(marker in text_l for marker in markers):
            occasion = key
            break

    budget, currency = extract_budget(text or "")

    return {
        "recipient": recipient,
        "occasion": occasion,
        "budget": budget,
        "currency": currency,
    }
