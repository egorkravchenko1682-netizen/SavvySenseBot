import os

import telebot

from core import SavvyCore
from core.models import SavvyRequest, UserContext


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


bot = telebot.TeleBot(BOT_TOKEN)

savvy = SavvyCore()


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


@bot.message_handler(commands=["find"])
def find_command(message):
    bot.send_message(
        message.chat.id,
        "🔎 Напиши, какой товар нужно найти.",
    )


@bot.message_handler(commands=["compare"])
def compare_command(message):
    bot.send_message(
        message.chat.id,
        "⚖️ Отправь товары или ссылки для сравнения.",
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    bot.send_message(
        message.chat.id,
        "🔎 Отправь ссылку или описание товара.",
    )


@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):
    bot.send_message(
        message.chat.id,
        "💰 Отправь ссылку или название товара.",
    )


@bot.message_handler(commands=["track"])
def track_command(message):
    bot.send_message(
        message.chat.id,
        "📉 Отправь ссылку на товар для отслеживания.",
    )


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
        "🔬 Product Identity определит товар "
        "на следующем этапе.",
    )


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

    product = response.data.get("product", {})

    intent = response.intent

    intent_names = {
        "product_search": "🔎 Поиск товара",
        "compare": "⚖️ Сравнение",
        "cheaper": "💰 Поиск дешевле",
        "check": "🔍 Проверка товара",
        "track": "📉 Отслеживание цены",
        "unknown": "❓ Неизвестный запрос",
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
        f"Название: {product.get('name') or '—'}",
        f"Бренд: {product.get('brand') or '—'}",
        f"Категория: {product.get('category') or '—'}",
    ]

    if attributes.get("storage"):
        lines.append(
            f"💾 Память: {attributes['storage']}"
        )

    if attributes.get("color"):
        lines.append(
            f"🎨 Цвет: {attributes['color']}"
        )

    if attributes.get("gender"):
        lines.append(
            f"👤 Пол: {attributes['gender']}"
        )

    if attributes.get("material"):
        lines.append(
            f"🧵 Материал: {attributes['material']}"
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
            f"🌍 Регион: {response.data.get('region')}",
            f"💱 Валюта: {response.data.get('currency')}",
        ]
    )

    bot.send_message(
        message.chat.id,
        "\n".join(lines),
    )


if __name__ == "__main__":
    print("🧠 SAVVY SENSE is starting...")

    bot.infinity_polling(
        skip_pending=True,
    )