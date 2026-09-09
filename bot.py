import os
import re
import telebot
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🧠 SAVVY SENSE\n\n"
        "Твой AI-помощник для умных покупок.\n\n"
        "🔗 Отправь мне ссылку на товар — "
        "я определю её и подготовлю поиск похожих вариантов."
    )
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text or ""
    urls = re.findall(
        r"https?://[^\s]+",
        text
    )
    if urls:
        url = urls[0]
        bot.send_message(
            message.chat.id,
            "🔗 Ссылка получена!\n\n"
            f"Товар:\n{url}\n\n"
            "🔎 Следующий этап — поиск этого товара "
            "и похожих вариантов."
        )
    else:
        bot.send_message(
            message.chat.id,
            "🔗 Отправь мне ссылку на товар, "
            "и я начну с неё поиск."
        )
bot.infinity_polling()