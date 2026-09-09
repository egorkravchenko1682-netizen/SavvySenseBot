import os
import re
import requests
import telebot

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)


def get_wb_product(nm_id):
    url = "https://card.wb.ru/cards/v4/detail"

    params = {
        "appType": 1,
        "curr": "rub",
        "dest": -1257786,
        "lang": "ru",
        "nm": nm_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    products = data.get("products", [])

    if not products:
        products = data.get("data", {}).get("products", [])

    if not products:
        return None

    return products[0]


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🔗 Отправь ссылку на товар Wildberries."
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text or ""

    urls = re.findall(r"https?://[^\s]+", text)

    if not urls:
        bot.send_message(
            message.chat.id,
            "🔗 Отправь ссылку на товар Wildberries."
        )
        return

    url = urls[0]

    match = re.search(
        r"/catalog/(\d+)/detail",
        url
    )

    if not match:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось определить артикул Wildberries."
        )
        return

    nm_id = match.group(1)

    bot.send_message(
        message.chat.id,
        "🔎 Получаю информацию о товаре..."
    )

    try:
        product = get_wb_product(nm_id)

        if not product:
            bot.send_message(
                message.chat.id,
                "❌ Товар не найден."
            )
            return

        name = product.get("name", "Не указано")
        brand = product.get("brand", "Не указан")
        rating = product.get("reviewRating", "Нет данных")
        reviews = product.get("feedbacks", "Нет данных")

        price = "Нет данных"

        sizes = product.get("sizes", [])

        if sizes:
            price_data = sizes[0].get("price", {})

            if "product" in price_data:
                price = price_data["product"]

                try:
                    price = f"{price / 100:.2f} ₽"
                except:
                    pass

        result = (
            "🛍️ ТОВАР НАЙДЕН\n\n"
            f"📦 {name}\n"
            f"🏷 Бренд: {brand}\n"
            f"💰 Цена: {price}\n"
            f"⭐ Рейтинг: {rating}\n"
            f"💬 Отзывов: {reviews}\n\n"
            f"🔢 Артикул: {nm_id}\n\n"
            "🔎 Следующий этап — поиск похожих товаров."
        )

        bot.send_message(
            message.chat.id,
            result
        )

    except Exception as e:
        print("Wildberries error:", e)

        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось получить данные Wildberries.\n"
            "Попробуем ещё раз позже."
        )


bot.infinity_polling()