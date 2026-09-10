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
# /start — ЗАПУСТИТЬ SAVVY SENSE
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Добро пожаловать в умный поиск товаров.\n\n"
        "🌎 Я помогу найти товар, сравнить цены "
        "и выбрать наиболее выгодное предложение.\n\n"
        "Выбери действие:\n\n"
        "🔎 /find — найти товар\n"
        "⚖️ /compare — сравнить товары\n"
        "🧠 /check — стоит ли покупать?\n"
        "💰 /cheaper — найти дешевле\n"
        "🔔 /track — отслеживать цену\n"
        "ℹ️ /help — как это работает\n\n"
        "Или просто отправь мне фото, ссылку "
        "или описание товара."
    )


# =========================
# /find — НАЙТИ ТОВАР
# =========================

@bot.message_handler(commands=["find"])
def find_command(message):

    query = message.text.replace(
        "/find",
        "",
        1
    ).strip()

    if query:

        bot.send_message(
            message.chat.id,
            "🔎 НАЙТИ ТОВАР\n\n"
            f"Ищу:\n{query}\n\n"
            "🌎 Выполняю поиск..."
        )

        results = search_engine.search_everywhere(
            query
        )

        if results:
            send_results(
                message.chat.id,
                results
            )
        else:
            bot.send_message(
                message.chat.id,
                "🔎 Пока не удалось найти "
                "доступные предложения."
            )

        return

    bot.send_message(
        message.chat.id,
        "🔎 НАЙТИ ТОВАР\n\n"
        "Напиши название или описание товара.\n\n"
        "Например:\n"
        "• iPhone 17 Pro 256GB\n"
        "• чёрная кожаная куртка до $100\n"
        "• Sony WH-1000XM6\n\n"
        "Также можешь просто отправить 📸 фото "
        "или 🔗 ссылку."
    )


# =========================
# /compare — СРАВНИТЬ
# =========================

@bot.message_handler(commands=["compare"])
def compare_command(message):

    query = message.text.replace(
        "/compare",
        "",
        1
    ).strip()

    if query:

        bot.send_message(
            message.chat.id,
            "⚖️ СРАВНЕНИЕ\n\n"
            f"Получил запрос:\n{query}\n\n"
            "🔎 Ищу доступные варианты для сравнения..."
        )

        results = search_engine.search_everywhere(
            query
        )

        if results:
            send_results(
                message.chat.id,
                results
            )
        else:
            bot.send_message(
                message.chat.id,
                "⚖️ Пока недостаточно доступных "
                "предложений для сравнения."
            )

        return

    bot.send_message(
        message.chat.id,
        "⚖️ СРАВНИТЬ ТОВАРЫ\n\n"
        "Отправь ссылку или напиши товары, "
        "которые хочешь сравнить.\n\n"
        "Например:\n"
        "/compare iPhone 17 Pro\n\n"
        "Я сравню доступные предложения."
    )


# =========================
# /check — СТОИТ ЛИ ПОКУПАТЬ
# =========================

@bot.message_handler(commands=["check"])
def check_command(message):

    query = message.text.replace(
        "/check",
        "",
        1
    ).strip()

    if query:

        bot.send_message(
            message.chat.id,
            "🧠 ПРОВЕРКА ТОВАРА\n\n"
            f"Товар:\n{query}\n\n"
            "🔎 Анализирую доступную информацию..."
        )

        bot.send_message(
            message.chat.id,
            "📊 Анализ будет включать:\n\n"
            "💰 цену\n"
            "⭐ рейтинг\n"
            "💬 отзывы\n"
            "🏪 продавца\n"
            "📦 предложение\n"
            "⚖️ соотношение цены и качества\n\n"
            "После подключения источников "
            "я смогу сформировать итоговую "
            "рекомендацию «Стоит покупать»."
        )

        return

    bot.send_message(
        message.chat.id,
        "🧠 СТОИТ ЛИ ПОКУПАТЬ?\n\n"
        "Отправь ссылку на товар или его название.\n\n"
        "Например:\n"
        "/check iPhone 17 Pro\n\n"
        "Я проверю товар и оценю его выгоду."
    )


# =========================
# /cheaper — НАЙТИ ДЕШЕВЛЕ
# =========================

@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):

    query = message.text.replace(
        "/cheaper",
        "",
        1
    ).strip()

    if query:

        bot.send_message(
            message.chat.id,
            "💰 ИЩУ ДЕШЕВЛЕ\n\n"
            f"Товар:\n{query}\n\n"
            "🌎 Ищу более выгодные предложения..."
        )

        results = search_engine.search_everywhere(
            query
        )

        if results:
            send_results(
                message.chat.id,
                results
            )
        else:
            bot.send_message(
                message.chat.id,
                "💰 Пока не удалось найти "
                "доступные более дешёвые варианты."
            )

        return

    bot.send_message(
        message.chat.id,
        "💰 НАЙТИ ДЕШЕВЛЕ\n\n"
        "Отправь ссылку или название товара.\n\n"
        "Например:\n"
        "/cheaper AirPods Pro 3\n\n"
        "Я попробую найти более выгодные варианты."
    )


# =========================
# /track — ОТСЛЕЖИВАНИЕ ЦЕНЫ
# =========================

@bot.message_handler(commands=["track"])
def track_command(message):

    query = message.text.replace(
        "/track",
        "",
        1
    ).strip()

    if query:

        bot.send_message(
            message.chat.id,
            "🔔 ОТСЛЕЖИВАНИЕ ЦЕНЫ\n\n"
            f"Товар:\n{query}\n\n"
            "Функция отслеживания будет сохранять "
            "товар и уведомлять при изменении цены."
        )

        return

    bot.send_message(
        message.chat.id,
        "🔔 ОТСЛЕЖИВАНИЕ ЦЕНЫ\n\n"
        "Отправь ссылку или название товара.\n\n"
        "Например:\n"
        "/track iPhone 17 Pro\n\n"
        "После подключения системы уведомлений "
        "я смогу сообщать об изменении цены."
    )


# =========================
# /help — КАК ЭТО РАБОТАЕТ
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        "ℹ️ КАК РАБОТАЕТ SAVVY SENSE\n\n"
        "🔎 /find\n"
        "Найти нужный товар.\n\n"
        "⚖️ /compare\n"
        "Сравнить доступные предложения.\n\n"
        "🧠 /check\n"
        "Проверить товар и понять, стоит ли его покупать.\n\n"
        "💰 /cheaper\n"
        "Попробовать найти более выгодную цену.\n\n"
        "🔔 /track\n"
        "Отслеживать изменение цены.\n\n"
        "📸 Фото\n"
        "Отправь фотографию товара.\n\n"
        "🔗 Ссылка\n"
        "Отправь ссылку на товар.\n\n"
        "✍️ Текст\n"
        "Просто напиши, что хочешь купить.\n\n"
        "🌎 SAVVY SENSE автоматически определит "
        "тип запроса."
    )


# =========================
# ПРИВЕТСТВИЯ
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
# ОБЫЧНЫЙ ТЕКСТОВЫЙ ПОИСК
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
            "Просто отправь мне товар, "
            "ссылку или фотографию."
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

        product = search_engine.get_product_from_link(
            url
        )

        if not product:

            bot.send_message(
                message.chat.id,
                "⚠️ Пока не удалось получить данные "
                "из этого магазина.\n\n"
                "Мы подключаем дополнительные "
                "источники."
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
            "🔎 Пока нет доступных результатов."
        )

        return

    send_results(
        message.chat.id,
        results
    )


# =========================
# РЕЗУЛЬТАТЫ
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
# ФОТО
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
# ЗАПУСК
# =========================

print("SAVVY SENSE started")

bot.infinity_polling(
    skip_pending=True
)