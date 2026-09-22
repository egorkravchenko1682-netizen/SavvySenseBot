import os

import telebot

from savvy_core import (
    REGIONS,
    add_tracking,
    build_context,
    get_preferences,
    get_region,
    get_tracking,
    init_db,
    remember,
    set_region,
    understand,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set"
    )


bot = telebot.TeleBot(BOT_TOKEN)

init_db()


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    text = (
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь:\n"
        "• ссылку на товар\n"
        "• описание товара\n"
        "• фотографию товара\n\n"
        "Основные команды:\n"
        "/find — найти товар\n"
        "/compare — сравнить\n"
        "/check — стоит ли покупать\n"
        "/cheaper — найти дешевле\n"
        "/track — отслеживать цену\n"
        "/region — регион доставки\n"
        "/remember — сохранить предпочтение\n"
        "/help — помощь"
    )

    bot.send_message(
        message.chat.id,
        text,
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        (
            "🧠 SAVVY SENSE\n\n"
            "/find — найти товар\n"
            "/compare — сравнить товары\n"
            "/check — проверить покупку\n"
            "/cheaper — найти дешевле\n"
            "/track — отслеживать цену\n"
            "/region — изменить регион\n"
            "/remember — сохранить предпочтение\n\n"
            "Также можно просто написать запрос "
            "обычным текстом."
        ),
    )


@bot.message_handler(commands=["region"])
def region_command(message):
    user_id = message.from_user.id

    current = get_region(user_id)

    regions_text = "\n".join(
        f"{code} — {name}"
        for code, name in REGIONS.items()
    )

    bot.send_message(
        message.chat.id,
        (
            f"🌍 Текущий регион: {current}\n\n"
            f"Доступные регионы:\n{regions_text}\n\n"
            "Чтобы изменить регион, отправь:\n"
            "/region BY"
        ),
    )


@bot.message_handler(
    func=lambda message: (
        message.text or ""
    ).lower().startswith("/region ")
)
def set_region_command(message):
    user_id = message.from_user.id

    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(
            message.chat.id,
            "Пример: /region BY",
        )
        return

    region = parts[1].upper()

    try:
        set_region(
            user_id,
            region,
        )

        bot.send_message(
            message.chat.id,
            (
                f"🌍 Регион изменён: "
                f"{REGIONS[region]} ({region})"
            ),
        )

    except ValueError:
        bot.send_message(
            message.chat.id,
            "Неизвестный регион.",
        )


@bot.message_handler(commands=["remember"])
def remember_command(message):
    text = message.text or ""

    parts = text.split(maxsplit=2)

    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            (
                "Использование:\n"
                "/remember ключ значение\n\n"
                "Например:\n"
                "/remember brand Nike"
            ),
        )
        return

    key = parts[1]
    value = parts[2]

    remember(
        message.from_user.id,
        key,
        value,
    )

    bot.send_message(
        message.chat.id,
        f"🧠 Запомнил:\n{key} = {value}",
    )


@bot.message_handler(commands=["track"])
def track_command(message):
    text = message.text or ""

    query = text[len("/track"):].strip()

    if not query:
        bot.send_message(
            message.chat.id,
            (
                "Напиши товар для отслеживания.\n\n"
                "Например:\n"
                "/track iPhone 16 Pro"
            ),
        )
        return

    add_tracking(
        user_id=message.from_user.id,
        product=query,
    )

    bot.send_message(
        message.chat.id,
        (
            "🔔 Товар добавлен в отслеживание:\n\n"
            f"{query}"
        ),
    )


@bot.message_handler(commands=["find"])
def find_command(message):
    process_text(
        message,
        message.text,
    )


@bot.message_handler(commands=["compare"])
def compare_command(message):
    process_text(
        message,
        message.text,
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    process_text(
        message,
        message.text,
    )


@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):
    process_text(
        message,
        message.text,
    )


def process_text(message, text):
    user_id = message.from_user.id

    result = understand(text)

    context = build_context(user_id)

    response = (
        "🧠 SAVVY SENSE\n\n"
        f"🔎 Запрос: {result['query']}\n"
        f"🎯 Intent: {result['intent']}\n"
        f"🌍 Регион: {context['region']}\n"
        f"💱 Валюта: {context['currency']}"
    )

    if result.get("budget") is not None:
        response += (
            f"\n💰 Бюджет: "
            f"до {result['budget']:.2f}"
        )

    response += (
        "\n\n"
        "⚙️ Запрос принят ядром SAVVY.\n"
        "🔧 Поисковый модуль будет подключён "
        "следующим блоком."
    )

    bot.send_message(
        message.chat.id,
        response,
    )


@bot.message_handler(
    content_types=["photo"]
)
def photo_handler(message):
    bot.send_message(
        message.chat.id,
        (
            "📷 Фото получено.\n\n"
            "SAVVY сохранил входной тип "
            "запроса.\n\n"
            "Модуль определения товара по фото "
            "подключим следующим блоком."
        ),
    )


@bot.message_handler(
    content_types=["text"]
)
def text_handler(message):
    if message.text.startswith("/"):
        return

    process_text(
        message,
        message.text,
    )


if __name__ == "__main__":
    print("🧠 SAVVY SENSE started")

    bot.infinity_polling(
        skip_pending=True
    )