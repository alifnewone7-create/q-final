"""aiogram sender for channel posts — this is what makes premium (custom) emoji work.

The admin UI keeps running on python-telegram-bot; only the outgoing channel
messages go through aiogram with parse_mode=HTML so <tg-emoji> entities are
accepted. Nothing polls here, so the two libraries never fight over getUpdates.

Every outgoing message is passed through premium_emojis.premiumize(), which
upgrades any plain emoji listed in data/premium_emojis.json to a Telegram
premium (custom) emoji. If Telegram rejects the custom-emoji entities (the bot
is not allowed to use them in that chat), the same message is resent with the
plain emoji instead of failing.
"""
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile

from premium_emojis import premiumize, strip_custom_emoji
from config import BOT_TOKEN

log = logging.getLogger("notifier")

_CUSTOM_EMOJI_ERRORS = ("custom emoji", "custom_emoji", "entity", "entities")


def _is_emoji_error(exc):
    msg = str(exc).lower()
    return any(k in msg for k in _CUSTOM_EMOJI_ERRORS)


class Notifier:
    def __init__(self):
        self._bot = None
        self.custom_emoji_ok = True

    @property
    def bot(self):
        if self._bot is None:
            self._bot = Bot(
                token=BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
        return self._bot

    async def send_photo(self, chat_id, png, caption):
        photo = BufferedInputFile(png, filename="chart.png")
        if self.custom_emoji_ok:
            try:
                return await self.bot.send_photo(
                    chat_id, photo, caption=premiumize(caption))
            except TelegramBadRequest as e:
                if not _is_emoji_error(e):
                    raise
                self.custom_emoji_ok = False
                log.warning(f"custom emoji rejected, falling back to plain emoji: {e}")
        # aiogram consumes the upload buffer, so build a fresh one for the retry
        return await self.bot.send_photo(
            chat_id, BufferedInputFile(png, filename="chart.png"),
            caption=strip_custom_emoji(caption))

    async def send_message(self, chat_id, text):
        if self.custom_emoji_ok:
            try:
                return await self.bot.send_message(chat_id, premiumize(text))
            except TelegramBadRequest as e:
                if not _is_emoji_error(e):
                    raise
                self.custom_emoji_ok = False
                log.warning(f"custom emoji rejected, falling back to plain emoji: {e}")
        return await self.bot.send_message(chat_id, strip_custom_emoji(text))

    async def close(self):
        if self._bot is not None:
            await self._bot.session.close()
            self._bot = None


NOTIFY = Notifier()
