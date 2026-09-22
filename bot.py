import os

import telebot

from core import SavvyCore
from core.models import SavvyRequest, UserContext


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


bot = telebot.TeleBot(BOT_TOKEN)

savvy = SavvyCore()


@bot.message_handler(commands=["start"])
def start_command(message):
    text = (
        "🧠 SAVVY SENSE\n\n"
        "🌎 Ищу товары по всему миру.\n\n"
        "Отправь мне:\n"
        "• название товара\n"
        "• ссылку на товар\n"
        "• фотографию товара\n\n"
        "Примеры:\n"
        "«Нужен iPhone до 800$»\n"
        "«Найди дешевле»\n"
        "«Сравни эти товары»"
    )

    bot.send_message(
        message.chat.id,
        text,
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    text = (
        "🧠 SAVVY SENSE — команды\n\n"
        "/start — запустить SAVVY\n"
        "/find — найти товар\n"
        "/compare — сравнить товары\n"
        "/check — проверить, стоит ли покупать\n"
        "/cheaper — найти дешевле\n"
        "/track — отслеживать цену\n"
        "/help — помощь\n\n"
        "Также можно просто отправить название товара, "
        "ссылку или фотографию."
    )

    bot.send_message(
        message.chat.id,
        text,
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
        "⚖️ Отправь товары или ссылки, которые нужно сравнить.",
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    bot.send_message(
        message.chat.id,
        "💰 Отправь ссылку или описание товара.",
    )


@bot.message_handler(commands=["cheaper"])
def cheaper_command(message):
    bot.send_message(
        message.chat.id,
        "🔎 Отправь ссылку или название товара — попробуем найти дешевле.",
    )


@bot.message_handler(commands=["track"])
def track_command(message):
    bot.send_message(
        message.chat.id,
        "📉 Отправь ссылку на товар, который нужно отслеживать.",
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
            f"❌ {response.error or 'Не удалось обработать запрос.'}",
        )
        return

    bot.send_message(
        message.chat.id,
        "📷 Фото получено.\n\n"
        "Модуль поиска по фотографии будет подключён "
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
            f"❌ {response.error or 'Ошибка обработки запроса.'}",
        )
        return

    intent = response.intent

    if intent == "compare":
        prefix = "⚖️ Запрос на сравнение принят."
    elif intent == "cheaper":
        prefix = "💰 Запрос на поиск дешевле принят."
    elif intent == "check":
        prefix = "🔎 Запрос на проверку товара принят."
    elif intent == "track":
        prefix = "📉 Запрос на отслеживание принят."
    else:
        prefix = "🔎 Запрос на поиск товара принят."

    bot.send_message(
        message.chat.id,
        f"{prefix}\n\n"
        f"🌍 Регион: {response.data.get('region')}\n"
        f"💱 Валюта: {response.data.get('currency')}\n\n"
        "Следующий модуль подключит настоящий поиск "
        "по магазинам и маркетплейсам.",
    )


@bot.message_handler(content_types=["document"])
def handle_document(message):
    bot.send_message(
        message.chat.id,
        "📄 Этот тип файла пока не поддерживается.",
    )


if __name__ == "__main__":
    print("🧠 SAVVY SENSE is starting...")
    bot.infinity_polling(
        skip_pending=True,
    )