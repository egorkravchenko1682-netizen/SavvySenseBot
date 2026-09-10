import os
import re

import telebot

from search import GlobalSearch


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = telebot.TeleBot(TOKEN)

search_engine = GlobalSearch()


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь:\n"
        "🔗 ссылку на товар\n"
        "🔎 описание товара\n"
        "📸 фотографию товара"
    )


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
            "🌎 Могу искать товары по всему миру.\n\n"
            "Например:\n"
            "• Чёрная кожаная куртка до $100\n"
            "• iPhone 17 Pro дешевле\n"
            "• Найди такой же товар дешевле\n"
            "• Отправь ссылку на товар\n"
            "• Отправь фотографию товара"
        )
        return

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

        product = search_engine.get_product_from_link(url)

        if not product:
            bot.send_message(
                message.chat.id,
                "⚠️ Пока не удалось получить данные "
                "из этого магазина.\n\n"
                "Мы подключим его к глобальному "
                "поиску на следующем этапе."
            )
            return

        bot.send_message(
            message.chat.id,
            "📦 Товар определён.\n\n"
            "🌎 Теперь ищу его и похожие варианты "
            "в других магазинах по всему миру..."
        )

        results = search_engine.search_everywhere(
            product.name
        )

        if not results:
            bot.send_message(
                message.chat.id,
                "🔎 Пока не удалось получить "
                "сравнимые предложения."
            )
            return

        send_results(
            message.chat.id,
            results
        )

        return

    bot.send_message(
        message.chat.id,
        "🌎 Ищу товар по всему миру...\n\n"
        f"🔎 Запрос: {text}"
    )

    results = search_engine.search_everywhere(text)

    if not results:
        bot.send_message(
            message.chat.id,
            "🔎 Пока нет доступных результатов.\n\n"
            "Система глобального поиска ещё "
            "подключается к магазинам."
        )
        return

    send_results(
        message.chat.id,
        results
    )


def send_results(chat_id, results):

    lines = [
        "🌎 РЕЗУЛЬТАТЫ ПОИСКА\n"
    ]

    for item in results[:10]:

        if item.price is not None:
            price = f"{item.price:.2f} {item.currency}"
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


@bot.message_handler(content_types=["photo"])
def handle_photo(message):

    bot.send_message(
        message.chat.id,
        "📸 Фото получено.\n\n"
        "AI-анализ изображения подключим "
        "на следующем этапе."
    )


print("SAVVY SENSE started")

bot.infinity_polling(
    skip_pending=True
)