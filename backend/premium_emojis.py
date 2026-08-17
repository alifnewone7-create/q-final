"""
=========================================================
💎 PREMIUM EMOJI SYSTEM 💎
=========================================================
Regular emoji in any outgoing channel message are converted to Telegram
Premium (custom) emoji when their emoji-id is present in data/premium_emojis.json.
"""
import json
import logging
import re

from config import DATA_DIR

logger = logging.getLogger("premium_emojis")

PREMIUM_EMOJIS_FILE = DATA_DIR / "premium_emojis.json"

DEFAULT_PREMIUM_EMOJIS = {
    "✅": "6217660507575291616",
    "✨": "5325547803936572038",
}


def load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_premium_emojis():
    """Load premium emojis from JSON file"""
    emojis = load_json_file(PREMIUM_EMOJIS_FILE, {})
    if not emojis:
        save_json_file(PREMIUM_EMOJIS_FILE, DEFAULT_PREMIUM_EMOJIS)
        logger.info(
            f"Created default {PREMIUM_EMOJIS_FILE} with {len(DEFAULT_PREMIUM_EMOJIS)} emojis")
        return DEFAULT_PREMIUM_EMOJIS
    return emojis


PREMIUM_EMOJIS = load_premium_emojis()


def p_emoji(char):
    """Convert regular emoji to premium Telegram emoji if available"""
    emoji_id = PREMIUM_EMOJIS.get(char)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'
    return char


_TAG_RE = re.compile(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', re.DOTALL)


def premiumize(text):
    """Replace every known plain emoji in the text with its premium version."""
    if not text or not PREMIUM_EMOJIS:
        return text
    # never touch emoji that already sit inside a <tg-emoji> tag
    parts = []
    last = 0
    for m in _TAG_RE.finditer(text):
        parts.append(_replace_all(text[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_replace_all(text[last:]))
    return "".join(parts)


def _replace_all(chunk):
    for char in sorted(PREMIUM_EMOJIS, key=len, reverse=True):
        if char and char in chunk:
            chunk = chunk.replace(char, p_emoji(char))
    return chunk


def strip_custom_emoji(text):
    """Same message with the custom-emoji tags reduced to their plain emoji."""
    return _TAG_RE.sub(r"\1", text)
