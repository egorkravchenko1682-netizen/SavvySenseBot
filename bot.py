import os, re, time, threading
import telebot
from savvy_core import get_profile, set_region, save_preference, add_track, list_tracks, ask_ai, ask_ai_image, understand, region_from_text, REGIONS

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN is not set')

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')


def send_safe(chat_id, text):
    text = text or 'Не удалось сформировать ответ.'
    for i in range(3):
        try:
            for part in [text[j:j+3900] for j in range(0, len(text), 3900)]:
                bot.send_message(chat_id, part, disable_web_page_preview=True)
            return
        except Exception as e:
            print('TELEGRAM SEND:', e)
            time.sleep(2 * (i + 1))


def profile_text(p):
    r = REGIONS[p.region]
    return f'🌍 Регион: <b>{r["name"]}</b> ({p.region})\n💱 Валюта: <b>{p.currency}</b>'

@bot.message_handler(commands=['start'])
def start(m):
    p = get_profile(m.from_user.id, m.from_user.language_code)
    send_safe(m.chat.id, f'''<b>🧠 SAVVY SENSE</b>\nТвой AI-помощник по покупкам для СНГ и всего мира.\n\nЯ могу искать по фото, ссылке или обычному сообщению, сравнивать предложения, учитывать твой регион, бюджет и предпочтения и выбирать лучший вариант.\n\n{profile_text(p)}\n\nПросто напиши: <i>«Нужен iPhone 15 до 800$»</i>''')

@bot.message_handler(commands=['help'])
def help_cmd(m):
    send_safe(m.chat.id, '''<b>SAVVY умеет:</b>\n/find — поиск\n/compare — сравнение\n/check — стоит ли покупать\n/cheaper — найти дешевле\n/track — отслеживание\n/region — регион\n\nНо команды не обязательны: просто отправь запрос, ссылку или фото.''')

@bot.message_handler(commands=['region'])
def region_cmd(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        send_safe(m.chat.id, 'Укажи код региона: BY, RU, KZ, UZ, KG, AM, AZ, TJ или MD.')
        return
    code = parts[1].strip().upper()
    try:
        set_region(m.from_user.id, code)
        send_safe(m.chat.id, f'✅ {profile_text(get_profile(m.from_user.id))}')
    except Exception:
        send_safe(m.chat.id, 'Неизвестный регион.')

@bot.message_handler(commands=['remember'])
def remember_cmd(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) != 2 or '=' not in parts[1]:
        send_safe(m.chat.id, 'Формат: /remember ключ=значение\nНапример: /remember favorite_brands=Apple,Nike')
        return
    key, value = [x.strip() for x in parts[1].split('=', 1)]
    save_preference(m.from_user.id, key, value)
    send_safe(m.chat.id, '🧠 Запомнил. Буду учитывать это в следующих покупках.')

@bot.message_handler(commands=['track'])
def track_cmd(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) == 1:
        tracks = list_tracks(m.from_user.id)
        send_safe(m.chat.id, 'Твои отслеживания:\n' + ('\n'.join(f'• {x}' for x in tracks) if tracks else 'Пока пусто.'))
        return
    add_track(m.from_user.id, parts[1])
    send_safe(m.chat.id, '🔔 Добавил запрос в отслеживание: <b>' + parts[1] + '</b>')


def handle_query(m, mode='shop', text=None):
    text = (text if text is not None else (m.text or '')).strip()
    p = get_profile(m.from_user.id, m.from_user.language_code)
    p = region_from_text(text, p)
    try:
        set_region(m.from_user.id, p.region)
    except Exception:
        pass
    parsed = understand(text, p)
    q = parsed.get('search_query') or text
    print('SAVVY QUERY:', q, 'REGION:', p.region, 'CURRENCY:', parsed.get('currency', p.currency), 'MAX:', parsed.get('max_price'))
    send_safe(m.chat.id, '⏳ SAVVY анализирует рынок: регион → поиск → сравнение → итоговая стоимость → рекомендация...')
    answer = ask_ai(q, p, mode=mode)
    send_safe(m.chat.id, answer)

@bot.message_handler(commands=['find'])
def find_cmd(m):
    text = m.text.replace('/find', '', 1).strip()
    if text: handle_query(m, 'shop', text)
    else: send_safe(m.chat.id, 'Напиши, что ищем. Например: <i>кроссовки Nike 42 до 200 BYN</i>')

@bot.message_handler(commands=['compare'])
def compare_cmd(m):
    text = m.text.replace('/compare', '', 1).strip()
    handle_query(m, 'compare', text) if text else send_safe(m.chat.id, 'Напиши товары или модели для сравнения.')

@bot.message_handler(commands=['check'])
def check_cmd(m):
    text = m.text.replace('/check', '', 1).strip()
    handle_query(m, 'analyze', text) if text else send_safe(m.chat.id, 'Пришли ссылку или название товара.')

@bot.message_handler(commands=['cheaper'])
def cheaper_cmd(m):
    text = m.text.replace('/cheaper', '', 1).strip()
    handle_query(m, 'cheaper', text) if text else send_safe(m.chat.id, 'Напиши товар, для которого найти дешевле.')

@bot.message_handler(content_types=['photo'])
def photo_handler(m):
    p = get_profile(m.from_user.id, m.from_user.language_code)
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        data = bot.download_file(file_info.file_path)
        import base64
        image_url = 'data:image/jpeg;base64,' + base64.b64encode(data).decode('ascii')
        send_safe(m.chat.id, '📷 Вижу товар. Ищу совпадения и лучшие варианты...')
        answer = ask_ai_image(image_url, m.caption or '', p)
        send_safe(m.chat.id, answer)
    except Exception as e:
        print('PHOTO ERROR:', e)
        send_safe(m.chat.id, 'Не удалось обработать фото. Попробуй отправить его ещё раз.')

@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_handler(m):
    if m.text.startswith('/'):
        return
    handle_query(m, 'shop', text)


def run_polling():
    while True:
        try:
            print('SAVVY SENSE started')
            bot.delete_webhook(drop_pending_updates=False)
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30, allowed_updates=['message'])
        except Exception as e:
            print('POLLING ERROR:', e)
            time.sleep(5)

if __name__ == '__main__':
    run_polling()
