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

    product = response.data.get(
        "product",
        {},
    )

    product_dna = response.data.get(
        "product_dna",
        {},
    )

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

    intent = response.intent

    # =========================
    # INTENT NAME
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
    # BASIC RESPONSE
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

    if attributes.get("storage"):

        lines.append(
            f"💾 Память: "
            f"{attributes['storage']}"
        )

    # =========================
    # COLOR
    # =========================

    if attributes.get("color"):

        lines.append(
            f"🎨 Цвет: "
            f"{attributes['color']}"
        )

    # =========================
    # GENDER
    # =========================

    if attributes.get("gender"):

        lines.append(
            f"👤 Пол: "
            f"{attributes['gender']}"
        )

    # =========================
    # MATERIAL
    # =========================

    if attributes.get("material"):

        lines.append(
            f"🧵 Материал: "
            f"{attributes['material']}"
        )

    # =========================
    # BUDGET
    # =========================

    if product.get("budget") is not None:

        lines.append(
            f"💰 Бюджет: "
            f"{product['budget']:.2f} "
            f"{product.get('currency', '')}"
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
    # SEND RESULT
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