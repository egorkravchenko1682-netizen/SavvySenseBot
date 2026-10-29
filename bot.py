import logging
import os
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from core import SavvyCore

from core.models import (
    SavvyRequest,
    UserContext,
)
from webapp.server import configure_api, start_server as start_webapp_server

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
).strip()

DEFAULT_WEBAPP_URL = "https://savvysensebot-production.up.railway.app"
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip() or DEFAULT_WEBAPP_URL
try:
    parsed_webapp_url = urlsplit(WEBAPP_URL)
    if (
        parsed_webapp_url.scheme != "https"
        or not parsed_webapp_url.hostname
        or parsed_webapp_url.username
        or parsed_webapp_url.password
        or parsed_webapp_url.port not in {None, 443}
        or parsed_webapp_url.path not in {"", "/"}
        or parsed_webapp_url.query
        or parsed_webapp_url.fragment
    ):
        WEBAPP_URL = ""
except ValueError:
    WEBAPP_URL = ""

WEBAPP_REGION_CURRENCIES = {
    "BY": "BYN",
    "RU": "RUB",
    "KZ": "KZT",
    "UZ": "UZS",
    "KG": "KGS",
    "AM": "AMD",
    "AZ": "AZN",
    "MD": "MDL",
}

WEBAPP_REQUESTS = defaultdict(deque)
WEBAPP_REQUESTS_LOCK = threading.Lock()
WEBAPP_REQUEST_LIMIT = 3
WEBAPP_REQUEST_WINDOW_SECONDS = 60


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set"
    )


# =========================
# TELEGRAM BOT
# =========================

bot = telebot.TeleBot(
    BOT_TOKEN
)


savvy = SavvyCore()


# =========================
# TELEGRAM MESSAGE HELPERS
# =========================

# Telegram позволяет до 4096 символов.
# Оставляем запас, чтобы служебные символы
# и форматирование никогда не упирались
# в жёсткий лимит.
TELEGRAM_MAX_MESSAGE_LENGTH = 3800


def send_long_message(
    chat_id,
    text: str,
):
    """
    Безопасно отправляет длинный текст.

    Если сообщение длиннее лимита Telegram,
    автоматически разбивает его на несколько
    сообщений.

    Сначала стараемся разбивать по строкам,
    чтобы карточки товаров не разрывались
    посреди строки.
    """

    if not text:
        return

    text = str(text)

    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        bot.send_message(
            chat_id,
            text,
        )
        return

    chunks = []
    current = ""

    for line in text.split("\n"):

        # Если отдельная строка сама длиннее
        # допустимого размера — режем её отдельно.
        if len(line) > TELEGRAM_MAX_MESSAGE_LENGTH:

            if current:
                chunks.append(
                    current.rstrip()
                )
                current = ""

            for start in range(
                0,
                len(line),
                TELEGRAM_MAX_MESSAGE_LENGTH,
            ):
                chunks.append(
                    line[
                        start:
                        start
                        + TELEGRAM_MAX_MESSAGE_LENGTH
                    ]
                )

            continue

        candidate = (
            line
            if not current
            else current + "\n" + line
        )

        if len(candidate) <= TELEGRAM_MAX_MESSAGE_LENGTH:

            current = candidate

        else:

            if current:
                chunks.append(
                    current.rstrip()
                )

            current = line

    if current:
        chunks.append(
            current.rstrip()
        )

    for chunk in chunks:

        if not chunk:
            continue

        bot.send_message(
            chat_id,
            chunk,
        )


# =========================
# FORMAT HELPERS
# =========================

def format_money(
    value,
    currency="USD",
):
    """
    Безопасное форматирование денежных значений.

    None -> неизвестно
    число -> 2 знака после запятой
    """

    if value is None:
        return "неизвестно"

    try:
        return (
            f"{float(value):.2f} "
            f"{currency}"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "неизвестно"


def format_price(
    value,
    currency="USD",
):
    """
    Форматирование цены.

    Используется отдельно, чтобы
    неизвестная цена отображалась
    как 'неизвестна'.
    """

    if value is None:
        return "неизвестна"

    try:
        return (
            f"{float(value):.2f} "
            f"{currency}"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "неизвестна"


# =========================
# START
# =========================

@bot.message_handler(
    commands=["start"]
)
def start_command(message):
    reply_markup = None
    instructions = (
        "🧠 SAVVY SENSE\n\n"
        "Найду подходящие предложения и помогу выбрать лучший вариант.\n\n"
        "Поиск, сравнение и результат — прямо в приложении."
    )

    if WEBAPP_URL:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(
            text="✨ SavvyApp",
            web_app=WebAppInfo(url=WEBAPP_URL),
        ))
        instructions += "\n\nНажми кнопку, чтобы начать."
        # Remove the old reply-keyboard launcher: Telegram leaves it visible
        # across deploys, and that launch mode does not provide authenticated initData.
        bot.send_message(
            message.chat.id,
            "Обновил запуск SAVVY — используй кнопку ✨ SavvyApp ниже или в меню чата.",
            reply_markup=ReplyKeyboardRemove(),
        )

    bot.send_message(
        message.chat.id,
        instructions,
        reply_markup=reply_markup,
    )


def _miniapp_search(user_id, payload):
    query = payload.get("query")
    region = payload.get("region")
    if (
        not isinstance(query, str)
        or not 2 <= len(query.strip()) <= 300
        or not isinstance(region, str)
        or region not in WEBAPP_REGION_CURRENCIES
    ):
        raise ValueError("Укажи название товара и страну доставки.")

    query = query.strip()
    try:
        parsed_query = urlsplit(query)
    except ValueError as error:
        raise ValueError("Введи название товара, а не ссылку.") from error
    if parsed_query.scheme or query.lower().startswith("www."):
        raise ValueError("Пока поиск работает по названию товара, не по ссылке.")

    if not _allow_webapp_request(user_id):
        raise RuntimeError("Слишком много поисков подряд. Попробуй через минуту.")

    response = savvy.process(SavvyRequest(
        text=query,
        user=UserContext(
            user_id=user_id,
            region=region,
            currency=WEBAPP_REGION_CURRENCIES[region],
        ),
    ))
    if not response.success:
        raise RuntimeError("Не удалось завершить поиск. Попробуй изменить запрос.")

    data = response.data or {}
    deal = data.get("deal_analysis") or {}
    best = deal.get("best_offer")
    offers = [offer for offer in data.get("offers", []) if isinstance(offer, dict)]
    usable_offers = [offer for offer in offers if offer.get("usable") is True]

    def offer_key(offer):
        product = offer.get("product") if isinstance(offer.get("product"), dict) else {}
        return tuple(str(value or "") for value in (
            offer.get("url"), offer.get("source"), offer.get("price"),
            offer.get("currency"), offer.get("region"), product.get("title"),
        ))

    if not best:
        return {
            "query": query,
            "currency": data.get("currency", WEBAPP_REGION_CURRENCIES[region]),
            "best": None,
            "alternatives": [],
            "found_count": len({offer_key(offer) for offer in usable_offers}),
            "message": "Надёжного предложения с ценой пока нет. Попробуй уточнить бренд или модель.",
        }

    # Put exact matches first; keep the first screen focused on a few choices.
    candidates = [offer for offer in usable_offers if offer.get("status") == "exact"]
    if not candidates:
        candidates = [offer for offer in usable_offers if offer.get("status") == "similar"]

    selected = [best]
    seen_keys = {offer_key(best)}
    for offer in candidates:
        key = offer_key(offer)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected.append(offer)
        if len(selected) >= 5:
            break
    alternatives = [_miniapp_offer(offer, data) for offer in selected[:5]]
    best_card = alternatives[0]

    match = best.get("match") or {}
    exact = best.get("status") == "exact"
    why = [
        "Совпадение товара подтверждено по найденным характеристикам." if exact
        else "Это близкий вариант: SAVVY не смог подтвердить полное совпадение.",
    ]
    matched = match.get("matched_attributes") if isinstance(match, dict) else None
    if matched:
        names = {
            "brand": "бренд", "model": "модель", "color": "цвет",
            "size": "размер", "storage": "память", "material": "материал",
            "category": "категория", "condition": "состояние",
        }
        visible = [names.get(str(item).lower(), str(item)) for item in matched[:3]]
        why.append("Совпали: " + ", ".join(visible) + ".")
    match_group = "точных совпадений" if exact else "похожих вариантов"
    comparison_source = deal.get("comparison_source")
    if comparison_source == "real_cost":
        why.append(f"Минимальная подтверждённая полная стоимость среди найденных {match_group} с ценой.")
    elif comparison_source == "price":
        why.append(f"Минимальная цена товара среди найденных {match_group}; доставка могла быть не учтена.")
    elif comparison_source == "quality":
        why.append("При одинаковой цене у этого предложения лучше оценка качества по доступным данным.")
    elif comparison_source == "risk":
        why.append("При одинаковой стоимости у этого предложения ниже расчётный риск.")
    else:
        why.append("Других сравнимых предложений с ценой не найдено.")
    best_card["why"] = why[:4]
    best_card["match_type"] = "Точное совпадение" if exact else "Похожий товар"

    return {
        "query": query,
        "currency": data.get("currency", WEBAPP_REGION_CURRENCIES[region]),
        "best": best_card,
        "alternatives": alternatives[1:],
        "found_count": len({offer_key(offer) for offer in candidates}),
        "message": None,
    }


def _miniapp_offer(offer, data):
    url = offer.get("url")
    try:
        parsed = urlsplit(url) if isinstance(url, str) else None
    except ValueError:
        parsed = None
    if not parsed or parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        url = None
    product = offer.get("product") if isinstance(offer.get("product"), dict) else {}
    price = offer.get("price")
    total_known = offer.get("real_cost_known") is True and offer.get("real_cost") is not None
    total = offer.get("real_cost") if total_known else offer.get("real_cost_partial")
    return {
        "title": str(product.get("title") or "Найденное предложение")[:300],
        "source": str(offer.get("source") or "Магазин")[:80],
        "seller": str(offer.get("seller"))[:120] if offer.get("seller") else None,
        "region": str(offer.get("region"))[:40] if offer.get("region") else None,
        "match_type": "Точное совпадение" if offer.get("status") == "exact" else "Похожий товар",
        "currency": offer.get("real_cost_currency") or offer.get("currency") or data.get("currency"),
        "price": price,
        "total": total,
        "total_known": total_known,
        "delivery": offer.get("delivery"),
        "delivery_estimated": bool(offer.get("delivery_estimated")),
        "taxes": offer.get("taxes"),
        "taxes_estimated": bool(offer.get("taxes_estimated")),
        "duties": offer.get("duties"),
        "duties_estimated": bool(offer.get("duties_estimated")),
        "risk": offer.get("risk_level") or "unknown",
        "quality": offer.get("deal_quality_score"),
        "url": url,
    }


# =========================
# HELP
# =========================

@bot.message_handler(
    commands=["help"]
)
def help_command(message):

    bot.send_message(
        message.chat.id,

        "🧠 SAVVY SENSE\n\n"

        "/start — запустить\n"
        "/find — найти товар\n"
        "/compare — сравнить\n"
        "/check — проверить товар\n"
        "/cheaper — найти дешевле\n"
        "/track — отслеживать цену\n"
        "/help — помощь",
    )


# =========================
# FIND
# =========================

@bot.message_handler(
    commands=["find"]
)
def find_command(message):

    bot.send_message(
        message.chat.id,

        "🔎 Напиши, какой товар нужно найти.",
    )


# =========================
# COMPARE
# =========================

@bot.message_handler(
    commands=["compare"]
)
def compare_command(message):

    bot.send_message(
        message.chat.id,

        "⚖️ Отправь товары или ссылки "
        "для сравнения.",
    )


# =========================
# CHECK
# =========================

@bot.message_handler(
    commands=["check"]
)
def check_command(message):

    bot.send_message(
        message.chat.id,

        "🔎 Отправь ссылку или "
        "описание товара.",
    )


# =========================
# CHEAPER
# =========================

@bot.message_handler(
    commands=["cheaper"]
)
def cheaper_command(message):

    bot.send_message(
        message.chat.id,

        "💰 Отправь ссылку или "
        "название товара.",
    )


# =========================
# TRACK
# =========================

@bot.message_handler(
    commands=["track"]
)
def track_command(message):

    bot.send_message(
        message.chat.id,

        "📉 Отправь ссылку на товар "
        "для отслеживания.",
    )


# =========================
# PHOTO
# =========================

@bot.message_handler(
    content_types=["photo"]
)
def handle_photo(message):

    user = UserContext(
        user_id=message.from_user.id,
    )

    request = SavvyRequest(
        image=message.photo[-1],
        user=user,
    )

    response = savvy.process(
        request
    )

    if not response.success:

        bot.send_message(
            message.chat.id,

            f"❌ "
            f"{response.error or 'Ошибка обработки.'}",
        )

        return

    bot.send_message(
        message.chat.id,

        "📷 Фото получено.\n\n"

        "🧬 Product DNA подготовлено.\n\n"

        "🔎 Следующий этап — поиск товара "
        "по изображению.",
    )


# =========================
# TEXT
# =========================

@bot.message_handler(
    content_types=["text"]
)
def handle_text(message):
    bot.send_message(
        message.chat.id,
        "Поиск и результаты SAVVY находятся в приложении. Нажми ✨ SavvyApp в меню чата или отправь /start.",
    )


def _allow_webapp_request(user_id):
    now = time.monotonic()
    with WEBAPP_REQUESTS_LOCK:
        history = WEBAPP_REQUESTS[user_id]
        while history and now - history[0] >= WEBAPP_REQUEST_WINDOW_SECONDS:
            history.popleft()
        if len(history) >= WEBAPP_REQUEST_LIMIT:
            return False
        history.append(now)
        if len(WEBAPP_REQUESTS) > 5000:
            expired_users = [
                key for key, values in WEBAPP_REQUESTS.items()
                if not values or now - values[-1] >= WEBAPP_REQUEST_WINDOW_SECONDS
            ]
            for key in expired_users:
                WEBAPP_REQUESTS.pop(key, None)
        return True


@bot.message_handler(
    content_types=["web_app_data"]
)
def handle_webapp_data(message):
    bot.send_message(
        message.chat.id,
        "Для поиска открой актуальную версию Mini App: нажми /start и выбери ✨ SavvyApp.",
    )


def _process_text_query(chat_id, user_id, text, region="BY", currency="USD"):
    text = (text or "").strip()

    if not text:
        return

    user = UserContext(
        user_id=user_id,
        region=region,
        currency=currency,
    )

    request = SavvyRequest(
        text=text,
        user=user,
    )

    response = savvy.process(
        request
    )

    if not response.success:

        bot.send_message(
            chat_id,

            f"❌ "
            f"{response.error or 'Ошибка обработки.'}",
        )

        return

    if response.intent == "gift":
        _send_gift_suggestions(chat_id, response)
        return

    # =========================
    # DATA
    # =========================

    product = response.data.get(
        "product",
        {},
    )

    product_dna = response.data.get(
        "product_dna",
        {},
    )

    search_plan = response.data.get(
        "search_plan",
        {},
    )

    offers = response.data.get(
        "offers",
        [],
    )

    deal_analysis = response.data.get(
        "deal_analysis",
        {},
    )

    intent = response.intent

    # =========================
    # INTENT LABELS
    # =========================

    intent_names = {

        "product_search":
            "🔎 Поиск товара",

        "compare":
            "⚖️ Сравнение",

        "cheaper":
            "💰 Поиск дешевле",

        "check":
            "🔍 Проверка товара",

        "track":
            "📉 Отслеживание цены",

        "unknown":
            "❓ Неизвестный запрос",
    }

    intent_text = intent_names.get(
        intent,
        intent,
    )

    # =========================
    # PRODUCT ATTRIBUTES
    # =========================

    attributes = product.get(
        "attributes",
        {},
    )

    # =========================
    # MESSAGE
    # =========================

    lines = [

        "🧠 SAVVY SENSE",

        "",

        f"🎯 Intent: {intent_text}",

        "",

        "📦 PRODUCT IDENTITY",

        f"Название: "
        f"{product.get('name') or '—'}",

        f"Бренд: "
        f"{product.get('brand') or '—'}",

        f"Категория: "
        f"{product.get('category') or '—'}",
    ]

    # =========================
    # STORAGE
    # =========================

    if attributes.get(
        "storage"
    ):

        lines.append(
            f"💾 Память: "
            f"{attributes['storage']}"
        )

    # =========================
    # COLOR
    # =========================

    if attributes.get(
        "color"
    ):

        lines.append(
            f"🎨 Цвет: "
            f"{attributes['color']}"
        )

    # =========================
    # GENDER
    # =========================

    if attributes.get(
        "gender"
    ):

        lines.append(
            f"👤 Пол: "
            f"{attributes['gender']}"
        )

    # =========================
    # MATERIAL
    # =========================

    if attributes.get(
        "material"
    ):

        lines.append(
            f"🧵 Материал: "
            f"{attributes['material']}"
        )

    # =========================
    # BUDGET
    # =========================

    budget = product.get(
        "budget"
    )

    if budget is not None:

        lines.append(
            f"💰 Бюджет: "
            f"{format_money(
                budget,
                product.get(
                    "currency",
                    response.data.get(
                        "currency",
                        "USD",
                    ),
                ),
            )}"
        )

    # =========================
    # REGION
    # =========================

    lines.extend(
        [

            "",

            f"🌍 Регион: "
            f"{response.data.get('region')}",

            f"💱 Валюта: "
            f"{response.data.get('currency')}",
        ]
    )

    # =========================
    # PRODUCT DNA
    # =========================

    search_scope = product_dna.get(
        "search_scope",
        {},
    )

    lines.extend(
        [

            "",

            "🧬 PRODUCT DNA",

            f"Тип: "
            f"{product_dna.get('product_type') or '—'}",

            f"Точное совпадение: "
            f"{'да' if search_scope.get('exact_product') else 'нет'}",

            f"Искать дешевле: "
            f"{'да' if search_scope.get('cheaper_offers') else 'нет'}",

            f"Аналоги: "
            f"{'да' if search_scope.get('similar_products') else 'нет'}",

            f"Международный поиск: "
            f"{'да' if search_scope.get('international') else 'нет'}",

            f"Состояние: "
            f"{product_dna.get('condition') or '—'}",
        ]
    )

    # =========================
    # SEARCH QUERY BUILDER
    # =========================

    lines.extend(
        [

            "",

            "🔎 SEARCH QUERY BUILDER",

            "",

            "Запросы:",
        ]
    )

    queries = search_plan.get(
        "queries",
        [],
    )

    if queries:

        for query in queries:

            lines.append(
                f"• {query}"
            )

    else:

        lines.append(
            "• Поисковые запросы "
            "не сформированы"
        )

    # =========================
    # GLOBAL SEARCH
    # =========================

    lines.extend(
        [

            "",

            "🌎 GLOBAL SEARCH",

            "",

            f"Найдено предложений: "
            f"{len(offers)}",
        ]
    )

    # =========================
    # DEAL ENGINE
    # =========================

    best_offer = deal_analysis.get("best_offer")

    lines.extend(
        [

            "",

            "🧠 DEAL ENGINE",

            f"🎯 Exact matches: "
            f"{deal_analysis.get('exact_count', 0)}",

            f"🔄 Similar: "
            f"{deal_analysis.get('similar_count', 0)}",

            f"⚠️ Over budget: "
            f"{deal_analysis.get('over_budget_count', 0)}",
        ]
    )

    if response.data.get("regions_compared"):
        lines.append(
            "🌍 Регионы сравнения: "
            + ", ".join(response.data["regions_compared"])
        )

    # =========================
    # BEST OFFER (с учётом доставки и пошлины, по всем регионам)
    # =========================

    if best_offer:

        best_product = best_offer.get("product", {})

        best_currency = (
            best_offer.get("real_cost_currency")
            or best_offer.get("currency")
            or response.data.get("currency", "USD")
        )

        best_cost = (
            best_offer.get("real_cost")
            if best_offer.get("real_cost_known")
            else best_offer.get("price")
        )

        cost_label = (
            "💰 ИТОГО (с доставкой/пошлиной): "
            if best_offer.get("real_cost_known")
            else "💰 Цена (доставка/пошлина неизвестны): "
        )

        deal_label = {
            "exact": "🏆 ЛУЧШЕЕ ТОЧНОЕ СОВПАДЕНИЕ",
            "similar": "🏆 ЛУЧШИЙ ПОХОЖИЙ ВАРИАНТ",
        }.get(
            deal_analysis.get("deal_type"),
            "🏆 ЛУЧШЕЕ ПРЕДЛОЖЕНИЕ",
        )

        lines.extend(
            [

                "",

                deal_label,

                f"Товар: "
                f"{best_product.get('title', '—')}",

                f"🏪 Источник: "
                f"{best_offer.get('source', '—')}",

                f"🌍 Регион: "
                f"{best_offer.get('region', '—')}",

                f"{cost_label}"
                f"{format_money(best_cost, best_currency)}",

                f"👤 Продавец: "
                f"{best_offer.get('seller', '—')}",
            ]
        )

        if (
            best_offer.get("region")
            and best_offer.get("region") != response.data.get("region")
        ):
            lines.append(
                "ℹ️ Это предложение из другого региона — "
                "доставка/пошлина уже учтены в сумме выше."
            )

    # =========================
    # OFFERS
    # =========================

    if offers:

        for index, offer in enumerate(
            offers,
            start=1,
        ):

            product_data = offer.get(
                "product",
                {},
            )

            offer_currency = (
                offer.get("currency")
                or response.data.get("currency", "USD")
            )

            # =========================
            # MATCH TYPE
            # =========================

            match_type = offer.get(
                "match_type",
                "unknown",
            )

            if match_type == "exact":

                match_label = (
                    "🎯 EXACT MATCH"
                )

            elif match_type == "similar":

                match_label = (
                    "🔄 SIMILAR"
                )

            else:

                match_label = (
                    "❓ UNKNOWN MATCH"
                )

            # =========================
            # COST BREAKDOWN LINES
            # =========================

            def _cost_line(field, label):
                value = offer.get(field)
                estimated = offer.get(f"{field}_estimated")
                suffix = (
                    " (оценка)"
                    if estimated and value is not None
                    else ""
                )
                return (
                    f"{label}"
                    f"{format_money(value, offer_currency)}"
                    f"{suffix}"
                )

            if offer.get("real_cost_known"):
                total_line = (
                    f"💰 ИТОГО: "
                    f"{format_money(offer.get('real_cost'), offer_currency)}"
                )
            else:
                total_line = (
                    "💰 ИТОГО: неизвестно "
                    "(не все компоненты стоимости определены)"
                )

            # =========================
            # OFFER
            # =========================

            lines.extend(
                [

                    "",

                    f"🛍 OFFER #{index}",

                    match_label,

                    f"Товар: "
                    f"{product_data.get('title', '—')}",

                    f"🏪 Источник: "
                    f"{offer.get('source', '—')}",

                    f"💰 Цена: "
                    f"{format_price(
                        offer.get('price'),
                        offer_currency,
                    )}",

                    _cost_line("delivery", "🚚 Доставка: "),
                    _cost_line("taxes", "🧾 Налоги: "),
                    _cost_line("duties", "📦 Пошлина: "),
                    _cost_line("fees", "💳 Комиссии: "),

                    total_line,

                    f"👤 Продавец: "
                    f"{offer.get('seller', '—')}",

                    f"📦 Состояние: "
                    f"{offer.get('condition', '—')}",

                    f"🌍 Регион: "
                    f"{offer.get('region', '—')}",

                    f"📋 Доступность: "
                    f"{offer.get('availability', 'unknown')}",
                ]
            )

            # =========================
            # URL
            # =========================

            if offer.get(
                "url"
            ):

                lines.append(
                    f"🔗 {offer.get('url')}"
                )

    else:

        lines.extend(
            [

                "",

                "ℹ️ Предложения не найдены.",
            ]
        )

    # =========================
    # SEND
    # =========================

    final_message = "\n".join(
        lines
    )

    send_long_message(
        chat_id,
        final_message,
    )


# =========================
# GIFT RENDERING
# =========================


def _send_gift_suggestions(chat_id, response):
    """
    Форматирует ответ для intent == "gift" — подборку категорий
    подарков вместо списка предложений одного товара (у подарка нет
    единственного "правильного" товара для строгого сопоставления,
    см. `gift.recommender.GiftRecommender`).
    """

    gift_request = response.data.get("gift_request", {})
    suggestions = response.data.get("gift_suggestions", [])
    currency = response.data.get("currency", "USD")

    recipient_names = {
        "girlfriend": "девушке",
        "boyfriend": "парню",
        "brother": "брату",
        "sister": "сестре",
        "mother": "маме",
        "father": "папе",
        "friend_female": "подруге",
        "friend_male": "другу",
        "colleague": "коллеге",
        "child": "ребёнку",
        "generic": "человеку",
    }

    recipient_label = recipient_names.get(
        gift_request.get("recipient"),
        "человеку",
    )

    lines = [f"🎁 ПОДБОРКА ПОДАРКОВ ({recipient_label})"]

    budget = gift_request.get("budget")
    if budget is not None:
        lines.append(
            f"💰 Бюджет: до {format_money(budget, currency)}"
        )

    if not suggestions:
        lines.extend(
            [
                "",
                "ℹ️ Не удалось подобрать подходящий вариант в "
                "заданном бюджете — попробуйте увеличить бюджет "
                "или уточнить получателя.",
            ]
        )
        send_long_message(chat_id, "\n".join(lines))
        return

    for index, suggestion in enumerate(suggestions, start=1):
        offer = suggestion.get("offer") or {}
        product_data = offer.get("product", {})

        offer_currency = offer.get("currency") or currency

        cost = (
            offer.get("real_cost")
            if offer.get("real_cost_known")
            else offer.get("price")
        )

        cost_label = (
            "ИТОГО (с доставкой/пошлиной)"
            if offer.get("real_cost_known")
            else "Цена"
        )

        quality_score = suggestion.get("deal_quality_score")
        quality_line = (
            f"⭐ Оценка сделки: {quality_score * 100:.0f}/100"
            if isinstance(quality_score, (int, float))
            else None
        )

        lines.extend(
            [
                "",
                f"{index}. {suggestion.get('category', '—').capitalize()}",
                f"Товар: {product_data.get('title', '—')}",
                f"🏪 Источник: {offer.get('source', '—')}",
                f"🌍 Регион: {offer.get('region', '—')}",
                f"💰 {cost_label}: {format_money(cost, offer_currency)}",
            ]
        )

        if quality_line:
            lines.append(quality_line)

        if offer.get("url"):
            lines.append(f"🔗 {offer.get('url')}")

    send_long_message(chat_id, "\n".join(lines))


# =========================
# RUN
# =========================

if __name__ == "__main__":

    print(
        "🧠 SAVVY SENSE is starting..."
    )

    if WEBAPP_URL:
        try:
            bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="✨ SavvyApp",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            )
        except Exception:
            logging.getLogger(__name__).warning("Unable to set Telegram Mini App menu button")

    configure_api(BOT_TOKEN, _miniapp_search, WEBAPP_URL)
    start_webapp_server()

    bot.infinity_polling(
        skip_pending=True,
    )
