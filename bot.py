import os
import re

import telebot

from search import GlobalSearch
from ai_parser import parse_user_request
from currency import (
    convert_to_budget_currency,
    format_money,
    normalize_currency,
)


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")


bot = telebot.TeleBot(TOKEN)

search_engine = GlobalSearch()


# =========================================================
# START
# =========================================================

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


# =========================================================
# HELP
# =========================================================

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
        "💻 мощный ноутбук для игр до 1000$\n"
        "📱 iPhone 15 до 500 EUR\n"
        "📱 iPhone 15 до 1500 PLN\n\n"
        "Я автоматически распознаю валюту "
        "и переведу цены найденных товаров "
        "в валюту твоего бюджета.\n\n"
        "Также можно отправить 📸 фото "
        "или 🔗 ссылку на товар."
    )


# =========================================================
# ПОКАЗАТЬ, ЧТО SAVVY ПОНЯЛ
# =========================================================

def show_understanding(
    chat_id,
    parsed
):

    lines = [
        "🧠 SAVVY ПОНЯЛ ЗАПРОС\n"
    ]

    if parsed.category:

        category_names = {

            "smartphone":
                "📱 Смартфон",

            "laptop":
                "💻 Ноутбук",

            "headphones":
                "🎧 Наушники",

            "tv":
                "📺 Телевизор",

            "clothing":
                "👕 Одежда",

            "shoes":
                "👟 Обувь",

            "watch":
                "⌚ Часы",

            "camera":
                "📷 Камера",

            "gaming":
                "🎮 Игровая техника",
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

            "male":
                "мужской",

            "female":
                "женский",

            "children":
                "детский",
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
            "💰 Бюджет: "
            + format_money(
                parsed.max_price,
                parsed.currency,
            )
        )

    if parsed.priorities:

        priority_names = {

            "price":
                "цена",

            "качество":
                "качество",

            "camera":
                "камера",

            "battery":
                "автономность",

            "performance":
                "производительность",

            "original":
                "оригинальность",

            "delivery":
                "доставка",
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
        "\n🌎 Ищу лучшие предложения..."
    )

    bot.send_message(
        chat_id,
        "\n".join(lines)
    )


# =========================================================
# GREETING
# =========================================================

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


# =========================================================
# /FIND
# =========================================================

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


# =========================================================
# /COMPARE
# =========================================================

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


# =========================================================
# /CHEAPER
# =========================================================

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


# =========================================================
# /CHECK
# =========================================================

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


# =========================================================
# /TRACK
# =========================================================

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


# =========================================================
# ОСНОВНАЯ ОБРАБОТКА ТЕКСТА
# =========================================================

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

    # -----------------------------------------------------
    # AI ПАРСЕР
    # -----------------------------------------------------

    parsed = parse_user_request(
        text
    )

    # -----------------------------------------------------
    # ПОКАЗЫВАЕМ ПОЛЬЗОВАТЕЛЮ,
    # ЧТО БОТ ПОНЯЛ
    # -----------------------------------------------------

    show_understanding(
        chat_id,
        parsed,
    )

    # -----------------------------------------------------
    # ПОИСК
    # -----------------------------------------------------

    search_query = parsed.original_text

    results = search_engine.search_everywhere(
        search_query
    )

    # -----------------------------------------------------
    # НИЧЕГО НЕ НАЙДЕНО
    # -----------------------------------------------------

    if not results:

        bot.send_message(
            chat_id,
            "🔎 Подходящих предложений "
            "пока не найдено.\n\n"
            "Попробуй изменить запрос "
            "или увеличить бюджет."
        )

        return

    # -----------------------------------------------------
    # РЕЗУЛЬТАТЫ
    # -----------------------------------------------------

    send_results(
        chat_id,
        results,
        parsed,
    )


# =========================================================
# ОБРАБОТКА ССЫЛКИ
# =========================================================

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
        None,
    )


# =========================================================
# ТЕКСТОВЫЕ СООБЩЕНИЯ
# =========================================================

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


# =========================================================
# ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТА
# =========================================================

def send_results(
    chat_id,
    results,
    parsed=None,
):

    lines = [
        "🌎 РЕЗУЛЬТАТЫ ПОИСКА\n"
    ]

    # -----------------------------------------------------
    # ВАЛЮТА БЮДЖЕТА
    # -----------------------------------------------------

    budget_currency = None
    budget = None

    if parsed:

        budget_currency = normalize_currency(
            parsed.currency
        )

        budget = parsed.max_price

    # -----------------------------------------------------
    # РЕЗУЛЬТАТЫ
    # -----------------------------------------------------

    for index, item in enumerate(
        results[:10],
        start=1,
    ):

        # -------------------------------------------------
        # ИСХОДНАЯ ЦЕНА
        # -------------------------------------------------

        if (
            item.price is not None
            and item.currency
        ):

            original_price = format_money(
                item.price,
                item.currency,
            )

        else:

            original_price = (
                "цена не указана"
            )

        # -------------------------------------------------
        # КОНВЕРТАЦИЯ
        # -------------------------------------------------

        converted_price = None

        if (
            item.price is not None
            and item.currency
            and budget_currency
        ):

            converted_price = (
                convert_to_budget_currency(
                    item.price,
                    item.currency,
                    budget_currency,
                )
            )

        # -------------------------------------------------
        # ЦЕНА В ВАЛЮТЕ БЮДЖЕТА
        # -------------------------------------------------

        converted_line = ""

        if (
            converted_price is not None
            and budget_currency
            and normalize_currency(
                item.currency
            ) != budget_currency
        ):

            converted_line = (
                "\n"
                "💱 ≈ "
                + format_money(
                    converted_price,
                    budget_currency,
                )
            )

        # -------------------------------------------------
        # РАЗНИЦА ДО БЮДЖЕТА
        # -------------------------------------------------

        budget_line = ""

        if (
            converted_price is not None
            and budget is not None
        ):

            difference = (
                budget
                - converted_price
            )

            if difference >= 0:

                budget_line = (
                    "\n"
                    "🎯 В бюджете: "
                    + format_money(
                        difference,
                        budget_currency,
                    )
                    + " осталось"
                )

            else:

                budget_line = (
                    "\n"
                    "⚠️ Превышение бюджета: "
                    + format_money(
                        abs(difference),
                        budget_currency,
                    )
                )

        # -------------------------------------------------
        # DEAL SCORE
        # -------------------------------------------------

        score_line = ""

        try:

            from deal_score import (
                calculate_deal_score,
                deal_label,
            )

            score = calculate_deal_score(
                item
            )

            score_line = (
                "\n"
                f"⭐ SAVVY SCORE: {score}/100 "
                f"{deal_label(score)}"
            )

        except Exception as e:

            print(
                "Deal Score error:",
                e,
            )

        # -------------------------------------------------
        # СОБИРАЕМ КАРТОЧКУ
        # -------------------------------------------------

        lines.append(
            f"{index}. 🛍 {item.shop}\n"
            f"📦 {item.name}\n"
            f"💰 {original_price}"
            f"{converted_line}"
            f"{budget_line}"
            f"{score_line}\n"
            f"🔗 {item.url}\n"
        )

    # -----------------------------------------------------
    # ОТПРАВЛЯЕМ
    # -----------------------------------------------------

    bot.send_message(
        chat_id,
        "\n".join(lines)
    )


# =========================================================
# ФОТО
# =========================================================

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


# =========================================================
# ЗАПУСК
# =========================================================

print(
    "SAVVY SENSE started"
)


bot.infinity_polling(
    skip_pending=True
)