"""Channel message templates using Telegram premium (custom) emoji.

Custom emoji are sent as HTML entities: <tg-emoji emoji-id="...">fallback</tg-emoji>.
Telegram shows the premium emoji to clients that can render it and falls back to
the plain emoji inside the tag everywhere else. If Telegram refuses the entities
altogether (bot not allowed to use custom emoji), notifier.py strips the tags and
resends the same text with the plain emoji.
"""
import html
import re

# key -> (custom_emoji_id, plain fallback emoji)
EMOJI = {
    "brand":       ("5325547803936572038", "\u2728"),
    "asset":       ("5451654705241398333", "\U0001f48e"),
    "signal":      ("5192982912496052999", "\U0001f680"),
    "call":        ("5449683594425410231", "\U0001f7e2"),
    "put":         ("5447183459602669338", "\U0001f534"),
    "entry":       ("6285240160120477644", "\u23f3"),
    "payout":      ("5294167145079395967", "\U0001f4b5"),
    "mtg":         ("5310278924616356636", "\U0001f6e1"),
    "owner":       ("6267115986541877538", "\U0001f451"),
    "analysis":    ("5422439311196834318", "\U0001f4a1"),
    "result_head": ("5422439311196834318", "\U0001f4ca"),
    "res_signal":  ("5190806721286657692", "\U0001f985"),
    "time":        ("5382194935057372936", "\u23f3"),
    "result":      ("6102723562076900877", "\U0001f498"),
    "win":         ("6217660507575291616", "\u2705"),
    "loss":        ("6102584400841546557", "\u274c"),
}

LINE = "\u2501" * 20
RLINE = "\u2501" * 21
PLINE = "\u2501" * 9 + "\u30fb" + "\u2501" * 9

_TAG_RE = re.compile(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>', re.DOTALL)


def em(key):
    eid, plain = EMOJI[key]
    return f'<tg-emoji emoji-id="{eid}">{plain}</tg-emoji>'


def strip_custom_emoji(text):
    """Same message with the custom-emoji tags reduced to their plain emoji."""
    return _TAG_RE.sub(r"\1", text)


def _dir_emoji(direction):
    return em("call") if direction == "CALL" else em("put")


def signal_caption(display, direction, entry_str, payout, reason, owner_tag):
    payout_str = f"{int(payout)}%" if payout else "\u2014"
    return (
        f"{em('brand')} TaNix Alpha 2.0 {em('brand')}\n"
        f"{LINE}\n\n"
        f"{em('asset')} Asset : {html.escape(display)}\n\n"
        f"{em('signal')} Signal : {_dir_emoji(direction)} {direction}\n"
        f"{em('entry')} Entry Time : {entry_str}\n"
        f"{em('payout')} Payout : {payout_str}\n"
        f"{em('mtg')} MTG : 1 - Step\n\n"
        f"{em('owner')} Owner : {html.escape(owner_tag)}\n"
        f"{LINE}\n\n"
        f"{em('analysis')} Analysis: {html.escape(reason)}"
    )


def result_caption(display, direction, time_str, result):
    if result == "WIN":
        res = f"{em('win')} WIN"
    elif result == "WIN_MTG":
        res = f"{em('win')} MTG WIN"
    else:
        res = f"{em('loss')} LOSS"
    return (
        f"{em('result_head')} SIGNAL RESULT\n"
        f"{RLINE}\n\n"
        f"{em('asset')} Asset : {html.escape(display)}\n"
        f"{em('res_signal')} Signal : {_dir_emoji(direction)} {direction}\n"
        f"{em('time')} Time : {time_str}\n\n"
        f"{em('result')} Result : {res}\n"
        f"{RLINE}"
    )
