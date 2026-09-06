import asyncio
import logging

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

from config import LANGUAGES

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


def _translate_to_sync(text: str, target: str) -> str | None:
    try:
        translated = GoogleTranslator(source="auto", target=target).translate(text)
    except Exception:
        logger.exception("Translation to %s failed", target)
        return None
    # deep_translator returns Google's HTML error page as the translated string instead of raising
    if translated and translated.lstrip().startswith("Error ") and "an error" in translated:
        logger.error("Google Translate returned an error page for target=%s: %s", target, translated[:120])
        return None
    return translated


async def translate_to(text: str, target: str) -> str | None:
    """Translate into an explicit target language code."""
    if target not in LANGUAGES:
        raise ValueError(f"Unsupported target language: {target!r}")
    return await asyncio.to_thread(_translate_to_sync, text, target)
