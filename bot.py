import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from savvy_core.engine import SavvyEngine
from savvy_core.models import UserProfile
from savvy_core.search import (
    DemoSearchProvider,
    SearchOrchestrator,
)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not configured"
    )


search_orchestrator = SearchOrchestrator(
    providers=[
        DemoSearchProvider(),
    ]
)

engine = SavvyEngine(
    search_orchestrator
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🧠 SAVVY SENSE\n\n"
        "Твой персональный AI Shopping Assistant\n"
        "для СНГ и всего мира.\n\n"
        "Я умею:\n"
        "🔎 искать товары\n"
        "💰 сравнивать цены\n"
        "🌍 искать по СНГ и миру\n"
        "📷 искать по фото\n"
        "🔗 анализировать ссылки\n"
        "🧠 учитывать твои предпочтения\n"
        "⭐ выбирать лучший вариант\n"
        "💡 помогать решить — покупать или подождать\n\n"
        "🌍 Регион: Беларусь (BY)\n"
        "💱 Валюта: BYN\n\n"
        "Просто напиши:\n\n"
        "Нужен iPhone 15 до 800$"
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    if not update.message.text:
        return

    query = update.message.text.strip()

    if not query:
        return

    user_id = update.effective_user.id

    profile = UserProfile(
        user_id=user_id
    )

    await update.message.reply_text(
        "🔎 SAVVY анализирует запрос..."
    )

    try:
        result = await engine.search(
            query=query,
            profile=profile,
        )

    except Exception as exc:
        print(f"[SAVVY ERROR] {exc}")

        await update.message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса."
        )

        return

    if not result.offers:
        await update.message.reply_text(
            "😔 Подходящих предложений пока не найдено."
        )
        return

    request = result.request
    cheapest = result.cheapest
    best = result.best_deal

    response = (
    "🧠 SAVVY SENSE\n\n"
    f"🔎 Запрос: {request.original_query}\n"
    f"🛍 Товар: {' '.join(request.keywords)}\n"
    f"🌍 Регион: {request.country}\n"
    f"💱 Валюта: {request.currency}\n"
    f"🎯 Intent: {request.intent}\n"
)

    if request.max_price is not None:
        response += (
            f"💰 Бюджет: до "
            f"{request.max_price:.2f} "
            f"{request.currency}\n"
        )

    response += "\n"

    if cheapest:
        response += (
            "💰 CHEAPEST\n"
            f"{cheapest.title}\n"
            f"Цена: {cheapest.price:.2f} "
            f"{cheapest.currency}\n"
            f"🚚 Доставка: {cheapest.shipping_cost:.2f} "
            f"{cheapest.currency}\n"
            f"💵 REAL COST: {cheapest.real_cost:.2f} "
            f"{cheapest.currency}\n"
            f"🏪 Продавец: {cheapest.seller}\n"
            f"⭐ Рейтинг: "
            f"{cheapest.seller_rating or 'нет данных'}\n"
            f"🔗 {cheapest.url}\n\n"
        )

    if best:
        response += (
            "🏆 BEST DEAL\n"
            f"{best.title}\n"
            f"💵 REAL COST: {best.real_cost:.2f} "
            f"{best.currency}\n"
            f"⭐ Рейтинг продавца: "
            f"{best.seller_rating or 'нет данных'}\n"
            f"🚚 Доставка: "
            f"{best.delivery_days or 'нет данных'} дней\n"
            f"🧠 SAVVY SCORE: "
            f"{result.savvy_score}/100\n"
            f"📌 Решение: "
            f"{result.decision}\n\n"
            f"{result.explanation}"
        )

    await update.message.reply_text(
        response
    )


def main():
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print(
        "🧠 SAVVY SENSE bot started."
    )

    application.run_polling()


if __name__ == "__main__":
    main()