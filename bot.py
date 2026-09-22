import os

import telebot

from core import SavvyCore
from core.models import SavvyRequest, UserContext


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


bot = telebot.TeleBot(BOT_TOKEN)

savvy = SavvyCore()


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start_command(message):

    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь:\n"
        "• название товара\n"
        "• ссылку\n"
        "• фотографию товара",
    )


# =========================
# HELP
# =========================

@bot.message_handler(commands=["help"])
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

@bot.message_handler(commands=["find"])
def find_command(message):

    bot.send_message(
        message.chat.id,
        "🔎 Напиши, какой товар нужно найти.",
    )


# =========================
# COMPARE
# =========================

@bot.message_handler(commands=["compare"])
def compare_command(message):

    bot.send_message(
        message.chat.id,
        "⚖️ Отправь товары или ссылки для сравнения.",
    )


# =========================
# CHECK
# =========================

@bot.message_handler(commands=["check"])
def check_command(message):

    bot.send_message(
        message.chat.id,
        "🔎 Отправь ссылку или описание товара.",
    )


# =========================
# CHEAPER
# =========================

@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):

    bot.send_message(
        message.chat.id,
        "💰 Отправь ссылку или название товара.",
    )


# =========================
# TRACK
# =========================

@bot.message_handler(commands=["track"])
def track_command(message):

    bot.send_message(
        message.chat.id,
        "📉 Отправь ссылку на товар для отслеживания.",
    )


# =========================
# PHOTO
# =========================

@bot.message_handler(content_types=["photo"])
def handle_photo(message):

    user = UserContext(
        user_id=message.from_user.id,
    )

    request = SavvyRequest(
        image=message.photo[-1],
        user=user,
    )

    response = savvy.process(request)

    if not response.success:

        bot.send_message(
            message.chat.id,
            f"❌ {response.error or 'Ошибка обработки.'}",
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

@bot.message_handler(content_types=["text"])
def handle_text(message):

    text = message.text.strip()

    if not text:
        return

    user = UserContext(
        user_id=message.from_user.id,
    )

    request = SavvyRequest(
        text=text,
        user=user,
    )

    response = savvy.process(request)

    if not response.success:

        bot.send_message(
            message.chat.id,
            f"❌ {response.error or 'Ошибка обработки.'}",
        )

        return

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

    intent = response.intent

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

    attributes = product.get(
        "attributes",
        {},
    )

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

    if attributes.get("storage"):

        lines.append(
            f"💾 Память: "
            f"{attributes['storage']}"
        )

    if attributes.get("color"):

        lines.append(
            f"🎨 Цвет: "
            f"{attributes['color']}"
        )

    if attributes.get("gender"):

        lines.append(
            f"👤 Пол: "
            f"{attributes['gender']}"
        )

    if attributes.get("material"):

        lines.append(
            f"🧵 Материал: "
            f"{attributes['material']}"
        )

    if product.get("budget") is not None:

        lines.append(
            f"💰 Бюджет: "
            f"{product['budget']:.2f} "
            f"{product.get('currency', '')}"
        )

    lines.extend(
        [

            "",

            f"🌍 Регион: "
            f"{response.data.get('region')}",

            f"💱 Валюта: "
            f"{response.data.get('currency')}",
        ]
    )

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
    # NORMALIZED OFFERS
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

            lines.extend(
                [

                    "",

                    f"🛍 OFFER #{index}",

                    f"Товар: "
                    f"{product_data.get('title', '—')}",

                    f"🏪 Источник: "
                    f"{offer.get('source', '—')}",

                    f"💰 Цена: "
                    f"{offer.get('price', '—')} "
                    f"{offer.get('currency', '')}",

                    f"🚚 Доставка: "
                    f"{offer.get('delivery', 0):.2f} "
                    f"{offer.get('currency', '')}",

                    f"🧾 Налоги: "
                    f"{offer.get('taxes', 0):.2f} "
                    f"{offer.get('currency', '')}",

                    f"📦 Пошлины: "
                    f"{offer.get('duties', 0):.2f} "
                    f"{offer.get('currency', '')}",

                    f"💳 Комиссии: "
                    f"{offer.get('fees', 0):.2f} "
                    f"{offer.get('currency', '')}",

                    f"💰 TOTAL COST: "
                    f"{offer.get('total_cost', 0):.2f} "
                    f"{offer.get('currency', '')}",

                    f"👤 Продавец: "
                    f"{offer.get('seller', '—')}",

                    f"📦 Состояние: "
                    f"{offer.get('condition', '—')}",

                    f"🌍 Регион: "
                    f"{offer.get('region', '—')}",
                ]
            )

            if offer.get("availability"):

                lines.append(
                    f"📋 Доступность: "
                    f"{offer.get('availability')}"
                )

            if offer.get("url"):

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

    bot.send_message(
        message.chat.id,
        "\n".join(lines),
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    print(
        "🧠 SAVVY SENSE is starting..."
    )

    bot.infinity_polling(
        skip_pending=True,
    )