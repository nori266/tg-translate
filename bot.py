import asyncio
import logging
from html import escape

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, CHAR_THRESHOLD, GROUP_CHAT_IDS, LANGUAGES
from translation import detect_source_lang, translate_auto, translate_to

LANG_CALLBACK_PREFIX = "tl:"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-translate messages exceeding CHAR_THRESHOLD. Always tracks last message for /translate."""
    msg = update.effective_message
    text = msg.text
    if not text:
        return
    context.chat_data["last_message"] = msg
    if len(text) <= CHAR_THRESHOLD:
        return
    translated = await translate_auto(text)
    if not translated:
        return
    await msg.reply_html(f"<i>{escape(translated)}</i>")


async def handle_translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/translate — reply to any message to choose a target language for it."""
    message = update.effective_message
    replied = message.reply_to_message
    if not replied or not replied.text:
        replied = context.chat_data.get("last_message")
    if not replied or not replied.text:
        await message.reply_text("No recent message to translate.")
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=f"{LANG_CALLBACK_PREFIX}{code}")
        for code, label in LANGUAGES.items()
    ]])
    await replied.reply_text("Translate to:", reply_markup=keyboard)


async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Language button tapped: replace the prompt with the translation of the message it replies to."""
    query = update.callback_query
    await query.answer()
    target = query.data.removeprefix(LANG_CALLBACK_PREFIX)
    source = query.message.reply_to_message
    if not source or not source.text:
        await query.edit_message_text("Original message is no longer available.")
        return
    translated = await translate_to(source.text, target)
    if not translated:
        await query.edit_message_text("Translation failed.")
        return
    await query.edit_message_text(f"<i>{escape(translated)}</i>", parse_mode="HTML")


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline mode: @botname <text> → one sendable result per target language."""
    query = update.inline_query.query.strip()
    if not query:
        await update.inline_query.answer([], cache_time=0)
        return
    source = detect_source_lang(query)
    targets = [code for code in LANGUAGES if code != source]
    translations = await asyncio.gather(*(translate_to(query, code) for code in targets))
    results = [
        InlineQueryResultArticle(
            id=code,
            title=LANGUAGES[code],
            input_message_content=InputTextMessageContent(
                message_text=f"{escape(query)}\n-----\n<i>{escape(translated)}</i>",
                parse_mode="HTML",
            ),
            description=translated,
        )
        for code, translated in zip(targets, translations)
        if translated
    ]
    await update.inline_query.answer(results, cache_time=0)


async def log_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    logger.info("Received message from chat_id=%s name=%r type=%s", chat.id, chat.title or chat.username, chat.type)


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    if not GROUP_CHAT_IDS:
        logger.warning("GROUP_CHAT_IDS not set — running in discovery mode, logging chat IDs only")
        app.add_handler(MessageHandler(filters.ALL, log_chat_id))
    else:
        group_filter = filters.Chat(chat_id=GROUP_CHAT_IDS)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & group_filter,
            handle_message,
        ))
        app.add_handler(CommandHandler("translate", handle_translate_command))
        app.add_handler(CallbackQueryHandler(handle_language_choice, pattern=f"^{LANG_CALLBACK_PREFIX}"))
        app.add_handler(InlineQueryHandler(handle_inline_query))

    logger.info("Bot started. CHAR_THRESHOLD=%d, GROUP_CHAT_IDS=%s", CHAR_THRESHOLD, GROUP_CHAT_IDS)
    app.run_polling()


if __name__ == "__main__":
    main()
