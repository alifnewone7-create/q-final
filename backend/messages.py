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


# ---- Mathematical Monospace font converter -------------------------------
# maps ASCII A-Z / a-z / 0-9 to the Unicode "Mathematical Monospace" block so
# messages render in the stylised font requested (e.g. TaNix Alpha 2.0).

def mono(text):
    out = []
    for ch in str(text):
        o = ord(ch)
        if 65 <= o <= 90:        # A-Z
            out.append(chr(0x1D670 + (o - 65)))
        elif 97 <= o <= 122:     # a-z
            out.append(chr(0x1D68A + (o - 97)))
        elif 48 <= o <= 57:      # 0-9
            out.append(chr(0x1D7F6 + (o - 48)))
        else:
            out.append(ch)
    return "".join(out)


def _fmt_pct(value):
    """Signed percentage, whole number when possible."""
    v = round(value, 1)
    if abs(v - round(v)) < 0.05:
        return f"{int(round(v)):+d}"
    return f"{v:+.1f}"


def strip_custom_emoji(text):
    """Same message with the custom-emoji tags reduced to their plain emoji."""
    return _TAG_RE.sub(r"\1", text)


def _dir_emoji(direction):
    return em("call") if direction == "CALL" else em("put")


def signal_caption(display, direction, entry_str, payout, reason, owner_tag):
    payout_str = f"{int(payout)}%" if payout else "\u2014"
    return (
        f"{em('brand')} {mono('TaNix Alpha 2.0')} {em('brand')}\n"
        f"{LINE}\n\n"
        f"{em('asset')} {mono('Asset')} : {mono(display)}\n\n"
        f"{em('signal')} {mono('Signal')} : {_dir_emoji(direction)} {mono(direction)}\n"
        f"{em('entry')} {mono('Entry Time')} : {mono(entry_str)}\n"
        f"{em('payout')} {mono('Payout')} : {mono(payout_str)}\n"
        f"{em('mtg')} {mono('MTG')} : {mono('1 - Step')}\n\n"
        f"{em('owner')} {mono('Owner')} : {mono(owner_tag)}\n"
        f"{LINE}"
    )


def result_caption(display, direction, time_str, result,
                   wins=0, losses=0, total_pct=0.0):
    if result == "WIN":
        res = f"{em('win')} {mono('WIN')}"
    elif result == "WIN_MTG":
        res = f"{em('win')} {mono('MTG WIN')}"
    else:
        res = f"{em('loss')} {mono('LOSS')}"
    total = wins + losses
    rate = round(wins / total * 100) if total else 0
    tail = f"{mono('GAIN')}" if total_pct >= 0 else f"{mono('LOSS')}"
    return (
        f"{em('result_head')} {mono('SIGNAL RESULT')}\n"
        f"{RLINE}\n\n"
        f"{em('asset')} {mono('Asset')} : {mono(display)}\n"
        f"{em('res_signal')} {mono('Signal')} : {_dir_emoji(direction)} {mono(direction)}\n"
        f"{em('time')} {mono('Time')} : {mono(time_str)}\n\n"
        f"{em('result')} {mono('Result')} : {res}\n"
        f"{RLINE}\n\n"
        f"\U0001f60d {mono('WIN')} : {mono(f'{wins:02d}')} | "
        f"{mono('LOSS')} : {mono(f'{losses:02d}')} - ({mono(f'{rate}')}%)\n"
        f"\U0001f300 {mono('Total')} : {mono(_fmt_pct(total_pct))}% {tail}"
    )
