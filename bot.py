import os
import re

import telebot

from search import GlobalSearch
from ai_parser import parse_user_request


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
        "Добро пожаловать в умный поиск товаров.\n\n"
        "🌎 Я помогу найти товар, сравнить цены "
        "и выбрать наиболее выгодное предложение.\n\n"
        "Просто отправь мне:\n\n"
        "📸 фотографию\n"
        "🔗 ссылку\n"
        "✍️ описание товара\n\n"
        "Я сам определю, что тебе нужно."
    )


@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        "ℹ️ SAVVY SENSE\n\n"
        "Просто отправь мне любой запрос.\n\n"
        "Например:\n\n"
        "📱 iPhone 15 до 500$\n"
        "👕 чёрная футболка Adidas до 100р\n"
        "🎧 хорошие наушники до 200€\n"
        "💻 мощный ноутбук для игр до 1000$\n\n"
        "Также можно отправить 📸 фото "
        "или 🔗 ссылку на товар."
    )


def show_understanding(
    chat_id,
    parsed
):

    lines = [
        "🧠 SAVVY ПОНЯЛ ЗАПРОС\n"
    ]

    if parsed.category:
        category_names = {
            "smartphone": "📱 Смартфон",
            "laptop": "💻 Ноутбук",
            "headphones": "🎧 Наушники",
            "tv": "📺 Телевизор",
            "clothing": "👕 Одежда",
            "shoes": "👟 Обувь",
            "watch": "⌚ Часы",
            "camera": "📷 Камера",
            "gaming": "🎮 Игровая техника",
        }

        lines.append(
            "Категория: "
            + category_names.get(
                parsed.category,
                parsed.category,
            )
        )

    if parsed.brand:

        lines.append(
            "🏷 Бренд: "
            + parsed.brand
        )

    if parsed.model:

        lines.append(
            "📦 Модель: "
            + parsed.model
        )

    if parsed.color:

        lines.append(
            "🎨 Цвет: "
            + parsed.color
        )

    if parsed.gender:

        gender_names = {
            "male": "мужской",
            "female": "женский",
            "children": "детский",
        }

        lines.append(
            "👤 Для: "
            + gender_names.get(
                parsed.gender,
                parsed.gender,
            )
        )

    if (
        parsed.max_price is not None
        and parsed.currency
    ):

        lines.append(
            f"💰 Бюджет: "
            f"{parsed.max_price:g} "
            f"{parsed.currency}"
        )

    if parsed.priorities:

        priority_names = {
            "price": "цена",
            "качество": "качество",
            "camera": "камера",
            "battery": "автономность",
            "performance": "производительность",
            "original": "оригинальность",
            "delivery": "доставка",
        }

        readable = []

        for priority in parsed.priorities:

            readable.append(
                priority_names.get(
                    priority,
                    priority,
                )
            )

        lines.append(
            "⭐ Приоритеты: "
            + ", ".join(readable)
        )

    lines.append(
        "\n🌎 Начинаю поиск..."
    )

    bot.send_message(
        chat_id,
        "\n".join(lines)
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

    return (
        text.lower().strip()
        in greetings
    )


@bot.message_handler(commands=["find"])
def find_command(message):

    query = message.text.replace(
        "/find",
        "",
        1,
    ).strip()

    if not query:

        bot.send_message(
            message.chat.id,
            "🔎 Просто напиши, "
            "что хочешь найти."
        )

        return

    process_text_query(
        message.chat.id,
        query,
    )


@bot.message_handler(commands=["compare"])
def compare_command(message):

    query = message.text.replace(
        "/compare",
        "",
        1,
    ).strip()

    if not query:

        bot.send_message(
            message.chat.id,
            "⚖️ Напиши товар, "
            "который нужно сравнить."
        )

        return

    process_text_query(
        message.chat.id,
        query,
    )


@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):

    query = message.text.replace(
        "/cheaper",
        "",
        1,
    ).strip()

    if not query:

        bot.send_message(
            message.chat.id,
            "💰 Отправь название "
            "или ссылку на товар."
        )

        return

    process_text_query(
        message.chat.id,
        query,
    )


@bot.message_handler(commands=["check"])
def check_command(message):

    query = message.text.replace(
        "/check",
        "",
        1,
    ).strip()

    if not query:

        bot.send_message(
            message.chat.id,
            "🧠 Отправь название "
            "или ссылку на товар."
        )

        return

    process_text_query(
        message.chat.id,
        query,
    )


@bot.message_handler(commands=["track"])
def track_command(message):

    query = message.text.replace(
        "/track",
        "",
        1,
    ).strip()

    if not query:

        bot.send_message(
            message.chat.id,
            "🔔 Отправь название "
            "или ссылку на товар."
        )

        return

    bot.send_message(
        message.chat.id,
        "🔔 Товар получен.\n\n"
        f"{query}\n\n"
        "Система отслеживания цены "
        "будет подключена следующим этапом."
    )


def process_text_query(
    chat_id,
    text,
):

    urls = re.findall(
        r"https?://[^\s]+",
        text,
    )

    if urls:

        process_link(
            chat_id,
            urls[0],
        )

        return

    parsed = parse_user_request(
        text
    )

    show_understanding(
        chat_id,
        parsed,
    )

    search_query = parsed.original_text

    results = search_engine.search_everywhere(
        search_query
    )

    if not results:

        bot.send_message(
            chat_id,
            "🔎 Пока не удалось найти "
            "подходящие предложения.\n\n"
            "Я сохранил структуру запроса "
            "и следующим этапом улучшим "
            "поисковый слой."
        )

        return

    send_results(
        chat_id,
        results,
    )


def process_link(
    chat_id,
    url,
):

    bot.send_message(
        chat_id,
        "🔗 Ссылка получена.\n\n"
        "🧠 Определяю товар..."
    )

    product = search_engine.get_product_from_link(
        url
    )

    if not product:

        bot.send_message(
            chat_id,
            "⚠️ Пока не удалось получить "
            "данные о товаре по этой ссылке."
        )

        return

    bot.send_message(
        chat_id,
        "📦 Товар определён:\n\n"
        f"{product.name}\n\n"
        "🌎 Ищу его и похожие предложения..."
    )

    results = search_engine.search_everywhere(
        product.name
    )

    if not results:

        bot.send_message(
            chat_id,
            "🔎 Пока не удалось найти "
            "сравнимые предложения."
        )

        return

    send_results(
        chat_id,
        results,
    )


@bot.message_handler(content_types=["text"])
def handle_text(message):

    text = (
        message.text or ""
    ).strip()

    if not text:
        return

    if is_greeting(text):

        bot.send_message(
            message.chat.id,
            "👋 Привет!\n\n"
            "Я SAVVY SENSE — AI-помощник "
            "для умных покупок.\n\n"
            "Просто отправь товар, "
            "ссылку или фотографию."
        )

        return

    process_text_query(
        message.chat.id,
        text,
    )


def send_results(
    chat_id,
    results,
):

    lines = [
        "🌎 РЕЗУЛЬТАТЫ ПОИСКА\n"
    ]

    for index, item in enumerate(
        results[:10],
        start=1,
    ):

        if item.price is not None:

            price = (
                f"{item.price:.2f} "
                f"{item.currency}"
            )

        else:

            price = "цена не указана"

        lines.append(
            f"{index}. 🛍 {item.shop}\n"
            f"📦 {item.name}\n"
            f"💰 {price}\n"
            f"🔗 {item.url}\n"
        )

    bot.send_message(
        chat_id,
        "\n".join(lines)
    )


@bot.message_handler(
    content_types=["photo"]
)
def handle_photo(message):

    bot.send_message(
        message.chat.id,
        "📸 Фото получено.\n\n"
        "Следующим этапом подключим "
        "компьютерное зрение, чтобы SAVVY "
        "сам определял товар по фотографии "
        "и искал его по всему миру."
    )


print(
    "SAVVY SENSE started"
)


bot.infinity_polling(
    skip_pending=True
)