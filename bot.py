import os
import telebot

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "Отправь мне ссылку на товар — "
        "и я помогу разобраться, стоит ли его покупать."
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_message(
        message.chat.id,
        "🔎 Получил твой запрос.\n\n"
        "Скоро SAVVY SENSE сможет найти товар, "
        "сравнить цены и помочь принять решение."
    )

bot.infinity_polling()
