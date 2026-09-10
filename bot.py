import os
import re

import telebot

from search import GlobalSearch


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = telebot.TeleBot(TOKEN)

search_engine = GlobalSearch()


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь мне:\n"
        "🔎 название или описание товара\n"
        "🔗 ссылку на товар\n"
        "📸 фотографию товара\n\n"
        "Команды:\n"
        "/search — поиск товара\n"
        "/compare — сравнение\n"
        "/help — помощь"
    )


# =========================
# HELP
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE — возможности\n\n"
        "🔎 Поиск товара\n"
        "Просто напиши, что ищешь.\n\n"
        "🔗 Поиск по ссылке\n"
        "Отправь ссылку на товар.\n\n"
        "📸 Поиск по фото\n"
        "Отправь фотографию товара.\n\n"
        "⚖️ Сравнение\n"
        "/compare\n\n"
        "🌎 Глобальный поиск\n"
        "Ищем лучшие варианты среди доступных источников."
    )


# =========================
# COMPARE
# =========================

@bot.message_handler(commands=["compare"])
def compare_command(message):

    bot.send_message(
        message.chat.id,
        "⚖️ Режим сравнения включён.\n\n"
        "Отправь мне:\n"
        "🔗 ссылку на товар\n"
        "или\n"
        "📸 фотографию товара\n"
        "или\n"
        "🔎 название товара.\n\n"
        "Я подготовлю сравнение доступных предложений."
    )


# =========================
# SEARCH COMMAND
# =========================

@bot.message_handler(commands=["search"])
def search_command(message):

    bot.send_message(
        message.chat.id,
        "🔎 Напиши, какой товар нужно найти.\n\n"
        "Например:\n"
        "iPhone 17 Pro 256GB\n"
        "чёрная кожаная куртка до $100\n"
        "беспроводные наушники Sony"
    )


# =========================
# GREETINGS
# =========================

def is_greeting(text):

    greetings = [
        "привет",
        "здравствуйте",
        "здравствуй",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "hello",
        "hi",
    ]

    return text.lower().strip() in greetings


# =========================
# TEXT
# =========================

@bot.message_handler(content_types=["text"])
def handle_text(message):

    text = (message.text or "").strip()

    if not text:
        return

    if is_greeting(text):

        bot.send_message(
            message.chat.id,
            "👋 Привет!\n\n"
            "Я SAVVY SENSE — AI-помощник "
            "для умных покупок.\n\n"
            "🌎 Просто отправь мне товар, "
            "ссылку или фотографию."
        )

        return

    # Проверяем ссылку

    urls = re.findall(
        r"https?://[^\s]+",
        text
    )

    if urls:

        url = urls[0]

        bot.send_message(
            message.chat.id,
            "🌎 Анализирую товар..."
        )

        product = search_engine.get_product_from_link(
            url
        )

        if not product:

            bot.send_message(
                message.chat.id,
                "⚠️ Пока не удалось получить данные "
                "из этого магазина.\n\n"
                "Мы подключим дополнительные "
                "источники поиска."
            )

            return

        bot.send_message(
            message.chat.id,
            "📦 Товар определён.\n\n"
            "🌎 Ищу предложения и похожие варианты..."
        )

        results = search_engine.search_everywhere(
            product.name
        )

        if not results:

            bot.send_message(
                message.chat.id,
                "🔎 Пока не удалось найти "
                "сравнимые предложения."
            )

            return

        send_results(
            message.chat.id,
            results
        )

        return

    # Обычный поисковый запрос

    bot.send_message(
        message.chat.id,
        "🌎 Ищу товар по всему миру...\n\n"
        f"🔎 Запрос: {text}"
    )

    results = search_engine.search_everywhere(
        text
    )

    if not results:

        bot.send_message(
            message.chat.id,
            "🔎 Пока нет доступных результатов.\n\n"
            "Мы подключаем реальные источники "
            "товаров."
        )

        return

    send_results(
        message.chat.id,
        results
    )


# =========================
# RESULTS
# =========================

def send_results(chat_id, results):

    lines = [
        "🌎 РЕЗУЛЬТАТЫ ПОИСКА\n"
    ]

    for item in results[:10]:

        if item.price is not None:

            price = (
                f"{item.price:.2f} "
                f"{item.currency}"
            )

        else:

            price = "цена не указана"

        lines.append(
            f"🛍 {item.shop}\n"
            f"📦 {item.name}\n"
            f"💰 {price}\n"
            f"🔗 {item.url}\n"
        )

    bot.send_message(
        chat_id,
        "\n".join(lines)
    )


# =========================
# PHOTO
# =========================

@bot.message_handler(content_types=["photo"])
def handle_photo(message):

    bot.send_message(
        message.chat.id,
        "📸 Фото получено.\n\n"
        "AI-анализ изображения подключим "
        "на следующем этапе."
    )


# =========================
# START BOT
# =========================

print("SAVVY SENSE started")

bot.infinity_polling(
    skip_pending=True
)