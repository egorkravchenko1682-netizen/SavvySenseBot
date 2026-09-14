import os
import time
import base64
import telebot

from savvy_core import (
    get_profile,
    set_region,
    save_preference,
    add_track,
    list_tracks,
    ask_ai,
    ask_ai_image,
    understand,
    region_from_text,
    REGIONS,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def send_safe(chat_id, text):
    text = text or "Не удалось сформировать ответ."

    for attempt in range(3):
        try:
            parts = [
                text[i:i + 3900]
                for i in range(0, len(text), 3900)
            ]

            for part in parts:
                bot.send_message(
                    chat_id,
                    part,
                    disable_web_page_preview=True,
                )

            return

        except Exception as e:
            print("TELEGRAM SEND:", e)
            time.sleep(2 * (attempt + 1))


def profile_text(profile):
    region = REGIONS[profile.region]

    return (
        f'🌍 Регион: <b>{region["name"]}</b> '
        f'({profile.region})\n'
        f'💱 Валюта: <b>{profile.currency}</b>'
    )


@bot.message_handler(commands=["start"])
def start(message):
    profile = get_profile(
        message.from_user.id,
        message.from_user.language_code,
    )

    send_safe(
        message.chat.id,
        f"""
<b>🧠 SAVVY SENSE</b>

Твой персональный AI Shopping Assistant
для СНГ и всего мира.

Я умею:
🔎 искать товары
💰 сравнивать цены
🌍 искать по СНГ и миру
📷 искать по фото
🔗 анализировать ссылки
🧠 учитывать твои предпочтения
⭐ выбирать лучший вариант
💡 помогать решить — покупать или подождать

{profile_text(profile)}

Просто напиши:

<i>Нужен iPhone 15 до 800$</i>
""",
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    send_safe(
        message.chat.id,
        """
<b>🧠 SAVVY SENSE</b>

/find — найти товар
/compare — сравнить
/check — проверить товар
/cheaper — найти дешевле
/track — отслеживать
/region — изменить регион
/remember — сохранить предпочтение

Но команды необязательны.

Просто отправь:
• название товара
• ссылку
• фотографию
• свой запрос обычным языком
""",
    )


@bot.message_handler(commands=["region"])
def region_cmd(message):
    parts = message.text.split(maxsplit=1)

    if len(parts) == 1:
        send_safe(
            message.chat.id,
            "Укажи регион:\n"
            "BY — Беларусь\n"
            "RU — Россия\n"
            "KZ — Казахстан\n"
            "UZ — Узбекистан\n"
            "KG — Кыргызстан\n"
            "AM — Армения\n"
            "AZ — Азербайджан\n"
            "TJ — Таджикистан\n"
            "MD — Молдова",
        )
        return

    code = parts[1].strip().upper()

    try:
        set_region(message.from_user.id, code)

        send_safe(
            message.chat.id,
            "✅ Регион установлен.\n\n"
            + profile_text(
                get_profile(message.from_user.id)
            ),
        )

    except Exception:
        send_safe(
            message.chat.id,
            "❌ Неизвестный регион.",
        )


@bot.message_handler(commands=["remember"])
def remember_cmd(message):
    parts = message.text.split(maxsplit=1)

    if len(parts) != 2 or "=" not in parts[1]:
        send_safe(
            message.chat.id,
            "Формат:\n"
            "/remember ключ=значение\n\n"
            "Например:\n"
            "/remember favorite_brands=Apple,Nike",
        )
        return

    key, value = [
        x.strip()
        for x in parts[1].split("=", 1)
    ]

    save_preference(
        message.from_user.id,
        key,
        value,
    )

    send_safe(
        message.chat.id,
        "🧠 Запомнил. Буду учитывать это "
        "в следующих покупках.",
    )


@bot.message_handler(commands=["track"])
def track_cmd(message):
    parts = message.text.split(maxsplit=1)

    if len(parts) == 1:
        tracks = list_tracks(
            message.from_user.id
        )

        if tracks:
            text = "🔔 Твои отслеживания:\n\n"
            text += "\n".join(
                f"• {item}"
                for item in tracks
            )
        else:
            text = "🔔 Пока ничего не отслеживается."

        send_safe(message.chat.id, text)
        return

    add_track(
        message.from_user.id,
        parts[1],
    )

    send_safe(
        message.chat.id,
        "🔔 Добавил в отслеживание:\n\n"
        f"<b>{parts[1]}</b>",
    )


def handle_query(message, mode="shop", text=None):
    text = (
        text
        if text is not None
        else (message.text or "")
    ).strip()

    profile = get_profile(
        message.from_user.id,
        message.from_user.language_code,
    )

    profile = region_from_text(
        text,
        profile,
    )

    try:
        set_region(
            message.from_user.id,
            profile.region,
        )
    except Exception:
        pass

    parsed = understand(
        text,
        profile,
    )

    query = (
        parsed.get("search_query")
        or text
    )

    print(
        "SAVVY QUERY:",
        query,
        "REGION:",
        profile.region,
        "CURRENCY:",
        parsed.get(
            "currency",
            profile.currency,
        ),
        "MAX:",
        parsed.get("max_price"),
    )

    send_safe(
        message.chat.id,
        "⏳ <b>SAVVY анализирует рынок...</b>\n\n"
        "Регион → поиск → сравнение → "
        "стоимость → качество → рекомендация",
    )

    answer = ask_ai(
        query,
        profile,
        mode=mode,
    )

    send_safe(
        message.chat.id,
        answer,
    )


@bot.message_handler(commands=["find"])
def find_cmd(message):
    text = message.text.replace(
        "/find",
        "",
        1,
    ).strip()

    if text:
        handle_query(
            message,
            "shop",
            text,
        )
    else:
        send_safe(
            message.chat.id,
            "Напиши, что нужно найти.",
        )


@bot.message_handler(commands=["compare"])
def compare_cmd(message):
    text = message.text.replace(
        "/compare",
        "",
        1,
    ).strip()

    if text:
        handle_query(
            message,
            "compare",
            text,
        )
    else:
        send_safe(
            message.chat.id,
            "Напиши товары или модели "
            "для сравнения.",
        )


@bot.message_handler(commands=["check"])
def check_cmd(message):
    text = message.text.replace(
        "/check",
        "",
        1,
    ).strip()

    if text:
        handle_query(
            message,
            "analyze",
            text,
        )
    else:
        send_safe(
            message.chat.id,
            "Пришли ссылку или название товара.",
        )


@bot.message_handler(commands=["cheaper"])
def cheaper_cmd(message):
    text = message.text.replace(
        "/cheaper",
        "",
        1,
    ).strip()

    if text:
        handle_query(
            message,
            "cheaper",
            text,
        )
    else:
        send_safe(
            message.chat.id,
            "Напиши товар, для которого "
            "нужно найти дешевле.",
        )


@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    profile = get_profile(
        message.from_user.id,
        message.from_user.language_code,
    )

    try:
        file_info = bot.get_file(
            message.photo[-1].file_id
        )

        data = bot.download_file(
            file_info.file_path
        )

        image_url = (
            "data:image/jpeg;base64,"
            + base64.b64encode(data).decode("ascii")
        )

        send_safe(
            message.chat.id,
            "📷 <b>Вижу товар.</b>\n\n"
            "Определяю товар и ищу лучшие варианты...",
        )

        answer = ask_ai_image(
            image_url,
            message.caption or "",
            profile,
        )

        send_safe(
            message.chat.id,
            answer,
        )

    except Exception as e:
        print("PHOTO ERROR:", e)

        send_safe(
            message.chat.id,
            "❌ Не удалось обработать фото. "
            "Попробуй отправить его ещё раз.",
        )


@bot.message_handler(
    func=lambda m: True,
    content_types=["text"],
)
def text_handler(message):
    if not message.text:
        return

    if message.text.startswith("/"):
        return

    handle_query(
        message,
        "shop",
        message.text,
    )


def run_polling():
    while True:
        try:
            print("SAVVY SENSE started")

            bot.delete_webhook(
                drop_pending_updates=False
            )

            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30,
                allowed_updates=["message"],
            )

        except Exception as e:
            print("POLLING ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run_polling()