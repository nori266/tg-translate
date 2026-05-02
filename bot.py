import logging
from html import escape

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, CHAR_THRESHOLD, GROUP_CHAT_IDS
from translation import translate_auto

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-translate messages exceeding CHAR_THRESHOLD."""
    text = update.effective_message.text
    if not text or len(text) <= CHAR_THRESHOLD:
        return
    translated = await translate_auto(text)
    if not translated:
        return
    await update.effective_message.reply_html(f"<i>{escape(translated)}</i>")


async def handle_translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/translate — reply to any message to get a translation."""
    message = update.effective_message
    replied = message.reply_to_message
    if not replied or not replied.text:
        await message.reply_text("Reply to a message with /translate to translate it.")
        return
    translated = await translate_auto(replied.text)
    if not translated:
        await message.reply_text("Language not detected or not supported (only EN↔RU).")
        return
    await replied.reply_html(f"<i>{escape(translated)}</i>")


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline mode: @botname <text> → offers translated text to send."""
    query = update.inline_query.query.strip()
    if not query:
        await update.inline_query.answer([], cache_time=0)
        return
    translated = await translate_auto(query)
    if not translated:
        await update.inline_query.answer([], cache_time=0)
        return
    title = translated[:64] + ("…" if len(translated) > 64 else "")
    result = InlineQueryResultArticle(
        id="1",
        title=title,
        input_message_content=InputTextMessageContent(
            message_text=f"<i>{escape(translated)}</i>",
            parse_mode="HTML",
        ),
        description="Send translation",
    )
    await update.inline_query.answer([result], cache_time=0)


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    group_filter = filters.Chat(chat_id=GROUP_CHAT_IDS)

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & group_filter,
        handle_message,
    ))
    app.add_handler(CommandHandler("translate", handle_translate_command))
    app.add_handler(InlineQueryHandler(handle_inline_query))

    logger.info("Bot started. CHAR_THRESHOLD=%d, GROUP_CHAT_IDS=%s", CHAR_THRESHOLD, GROUP_CHAT_IDS)
    app.run_polling()


if __name__ == "__main__":
    main()
