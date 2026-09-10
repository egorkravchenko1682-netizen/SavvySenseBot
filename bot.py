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
        "🌎 Я ищу товары по всему миру.\n\n"
        "Отправь мне:\n"
        "🔗 ссылку на товар\n"
        "🔎 название или описание товара\n"
        "📸 фотографию товара\n\n"
        "Я постараюсь найти лучший вариант по цене и условиям."
    )


@bot.message_handler(
    content_types=["text"]
)
def handle_text(message):

    text = (message.text or "").strip()

    if not text:
        return

    urls = re.findall(
        r"https?://[^\s]+",
        text
    )

    if urls:

        url = urls[0]

        bot.send_message(
            message.chat.id,
            "🌎 Анализирую товар и готовлю глобальный поиск..."
        )

        product = search_engine.get_product_from_link(url)

        if product:

            name = product.name
            shop = product.shop
            price = product.price
            currency = product.currency

            price_text = (
                f"{price:.2f} {currency}"
                if price is not None
                else "цена не определена"
            )

            bot.send_message(
                message.chat.id,
                "📦 ТОВАР ОПРЕДЕЛЁН\n\n"
                f"Название: {name}\n"
                f"Магазин: {shop}\n"
                f"Цена: {price_text}\n\n"
                "🌎 Теперь ищем этот товар "
                "и его аналоги по всему миру."
            )

            results = search_engine.search_everywhere(
                name
            )

            if results:

                lines = [
                    "\n💰 НАЙДЕННЫЕ ВАРИАНТЫ:\n"
                ]

                for item in results[:10]:

                    item_price = (
                        f"{item.price:.2f} "
                        f"{item.currency}"
                        if item.price is not None
                        else "цена не указана"
                    )

                    lines.append(
                        f"• {item.shop}: "
                        f"{item_price}"
                    )

                bot.send_message(
                    message.chat.id,
                    "\n".join(lines)
                )

            else:

                bot.send_message(
                    message.chat.id,
                    "🔎 Пока не удалось получить "
                    "результаты глобального сравнения."
                )

        else:

            bot.send_message(
                message.chat.id,
                "⚠️ Пока я не могу получить данные "
                "из этого магазина.\n\n"
                "Но магазин можно подключить "
                "к глобальному поиску."
            )

        return

    bot.send_message(
        message.chat.id,
        "🔎 Ищу товар по всему миру...\n\n"
        f"Запрос: {text}"
    )

    results = search_engine.search_everywhere(text)

    if not results:

        bot.send_message(
            message.chat.id,
            "Пока не найдено доступных предложений."
        )

        return

    lines = [
        "🌎 РЕЗУЛЬТАТЫ ГЛОБАЛЬНОГО ПОИСКА\n"
    ]

    for item in results[:10]:

        item_price = (
            f"{item.price:.2f} {item.currency}"
            if item.price is not None
            else "цена не указана"
        )

        lines.append(
            f"🛍 {item.shop}\n"
            f"📦 {item.name}\n"
            f"💰 {item_price}\n"
            f"🔗 {item.url}\n"
        )

    bot.send_message(
        message.chat.id,
        "\n".join(lines)
    )


@bot.message_handler(
    content_types=["photo"]
)
def handle_photo(message):

    bot.send_message(
        message.chat.id,
        "📸 Фото получено.\n\n"
        "В следующем этапе подключим "
        "AI-анализ изображения и поиск "
        "похожих товаров по всему миру."
    )


print("SAVVY SENSE started")

bot.infinity_polling(
    skip_pending=True
)