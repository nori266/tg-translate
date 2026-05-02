import asyncio
import logging

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


def _detect_lang(text: str) -> str | None:
    """Detect EN or RU. Returns 'en', 'ru', or None.

    Strategy:
    - Cyrillic-dominant text → 'ru' (script-based; langdetect confuses RU with MK/BG)
    - Latin-dominant text    → use langdetect and accept only 'en'
    - Mixed or other         → None
    """
    cyrillic = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF and c.isalpha())
    latin = sum(1 for c in text if ord(c) < 0x0080 and c.isalpha())
    total = cyrillic + latin
    if total == 0:
        return None
    if cyrillic / total > 0.5:
        return "ru"
    if latin / total > 0.5:
        try:
            return "en" if detect(text) == "en" else None
        except LangDetectException:
            return None
    return None


def _translate_sync(text: str) -> str | None:
    """Detect language and translate EN→RU or RU→EN. Returns None if not applicable or on error."""
    lang = _detect_lang(text)

    if lang == "en":
        dest = "ru"
    elif lang == "ru":
        dest = "en"
    else:
        return None

    try:
        return GoogleTranslator(source="auto", target=dest).translate(text)
    except Exception:
        logger.exception("Translation failed")
        return None


async def translate_auto(text: str) -> str | None:
    return await asyncio.to_thread(_translate_sync, text)
