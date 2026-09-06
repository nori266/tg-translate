import asyncio
import logging
import time

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

from config import LANGUAGES

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 5000  # deep_translator rejects anything at or above this
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.0


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

    return _translate_to_sync(text, dest)


async def translate_auto(text: str) -> str | None:
    return await asyncio.to_thread(_translate_sync, text)


def detect_source_lang(text: str) -> str | None:
    """Best-effort source language, limited to the supported set. None if unrecognised.

    Cyrillic-dominant text is decided by script, since langdetect confuses RU with MK/BG.
    """
    cyrillic = sum(1 for c in text if 0x0400 <= ord(c) <= 0x04FF and c.isalpha())
    latin = sum(1 for c in text if ord(c) < 0x0080 and c.isalpha())
    if cyrillic > latin:
        return "ru"
    try:
        lang = detect(text)
    except LangDetectException:
        return None
    return lang if lang in LANGUAGES else None


def _is_error_page(translated: str | None) -> bool:
    # deep_translator returns Google's HTML error page as the translated string instead of raising
    return bool(translated) and translated.lstrip().startswith("Error ") and "an error" in translated


def _translate_to_sync(text: str, target: str) -> str | None:
    if not 0 < len(text) < MAX_TEXT_CHARS:
        logger.error("Text of %d chars is outside the translatable range (0, %d)", len(text), MAX_TEXT_CHARS)
        return None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            translated = GoogleTranslator(source="auto", target=target).translate(text)
        except Exception:
            logger.warning("Translation to %s raised on attempt %d/%d", target, attempt, MAX_ATTEMPTS, exc_info=True)
            translated = None
        else:
            if _is_error_page(translated):
                logger.warning(
                    "Google Translate returned an error page for target=%s on attempt %d/%d: %s",
                    target, attempt, MAX_ATTEMPTS, translated[:120],
                )
                translated = None
        if translated:
            return translated
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    logger.error("Translation to %s failed after %d attempts", target, MAX_ATTEMPTS)
    return None


async def translate_to(text: str, target: str) -> str | None:
    """Translate into an explicit target language code."""
    if target not in LANGUAGES:
        raise ValueError(f"Unsupported target language: {target!r}")
    return await asyncio.to_thread(_translate_to_sync, text, target)
