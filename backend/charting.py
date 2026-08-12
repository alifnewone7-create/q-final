"""Chart-X style multi-panel candlestick chart PNG generator.

Layout (top -> bottom):
    * Main price panel (candles + EMA20 + Bollinger Bands + trend lines + zones + R/P/S labels + 1M timer)
    * Volume histogram (VOL MA14)
    * RSI(7) oscillator with 25 / 75 guide lines
    * MACD (5, 13, 5) histogram + signal
"""
import io
import time
import math
from datetime import datetime, timezone, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
from matplotlib import patheffects as pe

# ---- palette (Chart-X dark) ----------------------------------------------
BG            = "#000000"
GRID          = "#101820"
BORDER        = "#1e2a38"
TEXT          = "#c9d4e3"
DIM           = "#6b7a8a"
UP            = "#00e676"
DOWN          = "#ff2e4d"
EMA_COL       = "#26c6da"
BB_COL        = "#e0e0e0"
TREND_COL     = "#e0b060"
ZONE_R        = "#3a0d15"   # resistance zone (dark red)
ZONE_S        = "#0d3a1c"   # support zone (dark green)
R_LINE        = "#8b1b28"
S_LINE        = "#1e6b3a"
MACD_UP       = "#26c6da"
MACD_DN       = "#ff2e4d"
MACD_SIG      = "#ffb74d"
RSI_COL       = "#e0b060"
WM_COL        = "#1a4a2e"

FONT_MONO     = {"family": "DejaVu Sans Mono"}


# ---- indicator helpers ---------------------------------------------------

def _ema(values, period):
    if not values:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def _sma(values, period):
    out = []
    for i in range(len(values)):
        if i + 1 < period:
            out.append(None)
        else:
            out.append(sum(values[i + 1 - period : i + 1]) / period)
    return out


def _stdev(values, period):
    out = []
    for i in range(len(values)):
        if i + 1 < period:
            out.append(None)
            continue
        window = values[i + 1 - period : i + 1]
        m = sum(window) / period
        var = sum((x - m) ** 2 for x in window) / period
        out.append(math.sqrt(var))
    return out


def _rsi(values, period=7):
    if len(values) < period + 1:
        return [None] * len(values)
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    out = [None] * (period)
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    rs = avg_g / avg_l if avg_l else 0.0
    out.append(100 - 100 / (1 + rs) if avg_l else 100.0)
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
        rs = avg_g / avg_l if avg_l else 0.0
        out.append(100 - 100 / (1 + rs) if avg_l else 100.0)
    return out


def _macd(closes, fast=5, slow=13, signal=5):
    if len(closes) < slow + signal:
        n = len(closes)
        return [None] * n, [None] * n, [None] * n
    ef = _ema(closes, fast)
    es = _ema(closes, slow)
    macd_line = [a - b for a, b in zip(ef, es)]
    sig_line = _ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, sig_line)]
    return macd_line, sig_line, hist


# ---- pattern detection (compact one-word tags) --------------------------

def _classify(c, prev=None):
    """Return short pattern tag or None."""
    o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
    rng = h - l
    if rng <= 0:
        return None
    body = abs(cl - o)
    up_wick = h - max(o, cl)
    lo_wick = min(o, cl) - l
    body_pct = body / rng
    # doji
    if body_pct < 0.10:
        return "DOJI"
    # marubozu (full body)
    if body_pct > 0.85:
        return "MARU"
    # spinning top
    if body_pct < 0.35 and up_wick > body and lo_wick > body:
        return "SPIN"
    # engulfing vs prev
    if prev is not None:
        p_o, p_c = prev["open"], prev["close"]
        p_body = abs(p_c - p_o)
        if body > p_body * 1.2:
            bull = cl > o and p_c < p_o and cl > p_o and o < p_c
            bear = cl < o and p_c > p_o and cl < p_o and o > p_c
            if bull or bear:
                return "BENG"
    return None


# ---- main render ---------------------------------------------------------

def render_chart(candles, title, badge=None):
    """candles: list[dict(time,open,high,low,close[,volume])]. Returns PNG bytes."""
    data = candles[-90:] if len(candles) >= 20 else list(candles)
    n = len(data)
    if n < 2:
        # tiny fallback so caller never crashes
        fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
        ax.set_facecolor(BG)
        ax.text(0.5, 0.5, "Insufficient data", color=TEXT, ha="center", va="center")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=BG)
        plt.close(fig)
        return buf.getvalue()

    opens  = [c["open"]  for c in data]
    highs  = [c["high"]  for c in data]
    lows   = [c["low"]   for c in data]
    closes = [c["close"] for c in data]
    vols   = [c.get("volume", abs(c["close"] - c["open"]) * 1e6) for c in data]

    # indicators
    ema20 = _ema(closes, 20)
    bb_mid = _sma(closes, 20)
    bb_sd  = _stdev(closes, 20)
    bb_up  = [(m + 2 * s) if (m is not None and s is not None) else None
              for m, s in zip(bb_mid, bb_sd)]
    bb_lo  = [(m - 2 * s) if (m is not None and s is not None) else None
              for m, s in zip(bb_mid, bb_sd)]
    rsi_v  = _rsi(closes, 7)
    macd_l, sig_l, hist = _macd(closes, 5, 13, 5)
    vol_ma14 = _sma(vols, 14)

    # figure + grid
    fig = plt.figure(figsize=(16, 9), dpi=110, facecolor=BG)
    gs = GridSpec(4, 1, figure=fig, height_ratios=[10, 2.2, 2.0, 2.0],
                  hspace=0.09, left=0.028, right=0.938, top=0.865, bottom=0.055)
    ax  = fig.add_subplot(gs[0]); ax.set_facecolor(BG)
    axv = fig.add_subplot(gs[1], sharex=ax); axv.set_facecolor(BG)
    axr = fig.add_subplot(gs[2], sharex=ax); axr.set_facecolor(BG)
    axm = fig.add_subplot(gs[3], sharex=ax); axm.set_facecolor(BG)

    for a in (ax, axv, axr, axm):
        for s in a.spines.values():
            s.set_color(BORDER); s.set_linewidth(0.6)
        a.tick_params(colors=DIM, labelsize=9, length=0)
        a.grid(color=GRID, linewidth=0.5, alpha=0.9)
        a.yaxis.tick_right(); a.yaxis.set_label_position("right")

    # ---- price zones (support/resistance bands) --------------------------
    span = max(highs) - min(lows) or 1e-9
    lo_ref = min(lows); hi_ref = max(highs)
    # 4 red bands on top half, 3 green bands on bottom
    for i in range(4):
        y0 = hi_ref - span * 0.10 * i
        ax.axhspan(y0 - span * 0.008, y0, facecolor=ZONE_R, alpha=0.55, zorder=0)
        ax.axhline(y0, color=R_LINE, linewidth=0.6, alpha=0.7, zorder=0)
    for i in range(3):
        y0 = lo_ref + span * 0.06 * i
        ax.axhspan(y0, y0 + span * 0.010, facecolor=ZONE_S, alpha=0.55, zorder=0)
        ax.axhline(y0, color=S_LINE, linewidth=0.6, alpha=0.7, zorder=0)

    # ---- diagonal trend channel -----------------------------------------
    try:
        # upper channel: connect two swing highs; lower channel: two swing lows
        i_h1 = max(range(min(10, n)), key=lambda i: highs[i])
        i_h2 = min(range(max(0, n - 10), n), key=lambda i: -highs[i])
        i_l1 = max(range(min(10, n)), key=lambda i: -lows[i])
        i_l2 = min(range(max(0, n - 10), n), key=lambda i: lows[i])
        if i_h2 > i_h1:
            slope = (highs[i_h2] - highs[i_h1]) / (i_h2 - i_h1)
            xs = [-2, n + 4]
            ys = [highs[i_h1] + slope * (x - i_h1) for x in xs]
            ax.plot(xs, ys, color=TREND_COL, linewidth=0.8, alpha=0.9, zorder=1)
            ys2 = [y - span * 0.05 for y in ys]
            ax.plot(xs, ys2, color=TREND_COL, linewidth=0.6, alpha=0.6, zorder=1)
        if i_l2 > i_l1:
            slope = (lows[i_l2] - lows[i_l1]) / (i_l2 - i_l1)
            xs = [-2, n + 4]
            ys = [lows[i_l1] + slope * (x - i_l1) for x in xs]
            ax.plot(xs, ys, color=TREND_COL, linewidth=0.8, alpha=0.9, zorder=1)
    except Exception:
        pass

    # ---- Bollinger Bands ------------------------------------------------
    xs_bb = list(range(n))
    xs_v = [x for x, v in zip(xs_bb, bb_up) if v is not None]
    if xs_v:
        ax.plot(xs_v, [bb_up[x] for x in xs_v], color=BB_COL, linewidth=0.5, alpha=0.7, zorder=2)
        ax.plot(xs_v, [bb_lo[x] for x in xs_v], color=BB_COL, linewidth=0.5, alpha=0.7, zorder=2)
        ax.plot(xs_v, [bb_mid[x] for x in xs_v], color=BB_COL, linewidth=0.4, alpha=0.35,
                linestyle=(0, (2, 2)), zorder=2)

    # ---- EMA20 ----------------------------------------------------------
    ax.plot(xs_bb, ema20, color=EMA_COL, linewidth=1.2, alpha=0.95, zorder=3)

    # ---- candles --------------------------------------------------------
    tiny = span * 0.0015
    prev = None
    labels_placed = []  # (x, y) to avoid overlap
    for i, c in enumerate(data):
        up = c["close"] >= c["open"]
        col = UP if up else DOWN
        ax.vlines(i, c["low"], c["high"], color=col, linewidth=1.0, zorder=4)
        body_h = abs(c["close"] - c["open"]) or tiny
        ax.add_patch(Rectangle(
            (i - 0.34, min(c["open"], c["close"])), 0.68, body_h,
            facecolor=col, edgecolor=col, linewidth=0.5, zorder=5,
        ))
        # sparse pattern label (skip near last candle when a badge is shown)
        tag = _classify(c, prev)
        near_badge = badge and (n - 1 - i) < 3
        if tag and (i % 4 == 0 or i == n - 1) and not near_badge:
            y = c["high"] + span * 0.015
            if not any(abs(px - i) < 3 for px, _ in labels_placed):
                ax.text(i, y, tag, color="#e8f5e9", fontsize=8, ha="center", va="bottom",
                        fontweight="bold", family="DejaVu Sans Mono",
                        bbox=dict(boxstyle="round,pad=0.22", facecolor="#0d3a1c",
                                  edgecolor=S_LINE, linewidth=0.6))
                labels_placed.append((i, y))
        prev = c

    # ---- last candle badge (WIN / signal) ------------------------------
    last = data[-1]
    last_col = UP if last["close"] >= last["open"] else DOWN
    ax.annotate(
        "", xy=(n - 1, last["close"]), xytext=(n - 1 - 2, last["close"] + span * 0.02),
        arrowprops=dict(arrowstyle="-", color=last_col, lw=0.6, alpha=0.8),
    )
    if badge in ("CALL", "PUT"):
        badge_col = UP if badge == "CALL" else DOWN
        ax.text(n - 0.5, last["high"] + span * 0.03, badge, color="#ffffff",
                fontsize=10, fontweight="bold", ha="center", va="bottom",
                family="DejaVu Sans Mono",
                bbox=dict(boxstyle="round,pad=0.28", facecolor=badge_col,
                          edgecolor=badge_col, linewidth=0))
    elif badge:
        # WIN / LOSS style
        b_col = UP if str(badge).upper().startswith("WIN") else DOWN
        ax.text(n - 0.5, last["high"] + span * 0.03, badge, color="#ffffff",
                fontsize=10, fontweight="bold", ha="center", va="bottom",
                family="DejaVu Sans Mono",
                bbox=dict(boxstyle="round,pad=0.28", facecolor=b_col,
                          edgecolor=b_col, linewidth=0))

    # ---- right side R / P / S price tags -------------------------------
    r_price = max(highs[-30:]) if n >= 5 else max(highs)
    s_price = min(lows[-30:])  if n >= 5 else min(lows)
    p_price = last["close"]
    # keep R above P and S below P visually so labels don't overlap
    gap = span * 0.06
    if r_price - p_price < gap:
        r_price = p_price + gap
    if p_price - s_price < gap:
        s_price = p_price - gap
    x_tag = n + 0.6

    def _pricetag(y, label, bg):
        ax.plot([n - 0.5, x_tag - 0.05], [y, y], color=bg, linewidth=0.5, alpha=0.9, zorder=4)
        ax.text(x_tag, y, f" {label} {y:.4f} ", color="#ffffff", fontsize=9.5,
                fontweight="bold", ha="left", va="center", family="DejaVu Sans Mono",
                bbox=dict(boxstyle="round,pad=0.30", facecolor=bg, edgecolor=bg, linewidth=0),
                clip_on=False, zorder=10)

    _pricetag(r_price, "R", "#b02234")
    _pricetag(p_price, "P", "#1f6feb")
    _pricetag(s_price, "S", "#1e7d3a")

    # ---- 1M timer box (positioned to the right of P tag) ----------------
    now = int(time.time())
    remaining = 60 - (now % 60)
    ax.text(x_tag + 7.5, p_price, f" 1M TIMER \n   00:{remaining:02d}   ",
            color=EMA_COL, fontsize=10.5, fontweight="bold", ha="left", va="center",
            family="DejaVu Sans Mono",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#001318",
                      edgecolor=EMA_COL, linewidth=1.0),
            clip_on=False, zorder=11)

    # ---- watermark ------------------------------------------------------
    ax.text(0.5, 0.5, "Binary Algo Prime", transform=ax.transAxes, color=WM_COL,
            fontsize=52, fontweight="bold", alpha=0.55, ha="center", va="center",
            zorder=0, family="DejaVu Sans")

    # ---- main axis limits + x labels ------------------------------------
    ax.set_xlim(-1.5, n + 22)
    pad = span * 0.12
    ax.set_ylim(min(lows) - pad, max(highs) + pad)
    ax.set_xticks([])

    # ---- volume ---------------------------------------------------------
    vmax = max(vols) or 1
    for i, c in enumerate(data):
        col = UP if c["close"] >= c["open"] else DOWN
        axv.bar(i, vols[i], color=col, width=0.75, alpha=0.85, edgecolor=col, linewidth=0)
    xs_vm = [i for i, v in enumerate(vol_ma14) if v is not None]
    if xs_vm:
        axv.plot(xs_vm, [vol_ma14[i] for i in xs_vm], color=TREND_COL, linewidth=0.8, alpha=0.9)
    axv.set_ylim(0, vmax * 1.15)
    axv.set_xticks([])
    axv.text(0.005, 0.85, "VOL   MA14", transform=axv.transAxes, color=DIM, fontsize=9,
             fontweight="bold", family="DejaVu Sans Mono")
    axv.text(0.005, 0.50, str(int(vols[-1])) if vols[-1] < 10000 else f"{int(vols[-1])}",
             transform=axv.transAxes, color=TEXT, fontsize=8.5, family="DejaVu Sans Mono")

    # ---- RSI ------------------------------------------------------------
    xs_r = [i for i, v in enumerate(rsi_v) if v is not None]
    if xs_r:
        axr.plot(xs_r, [rsi_v[i] for i in xs_r], color=RSI_COL, linewidth=0.9)
    axr.axhline(75, color=DIM, linewidth=0.5, linestyle=(0, (2, 2)), alpha=0.7)
    axr.axhline(25, color=DIM, linewidth=0.5, linestyle=(0, (2, 2)), alpha=0.7)
    axr.set_ylim(0, 100)
    axr.set_yticks([25, 75])
    axr.set_xticks([])
    axr.text(0.005, 0.82, f"RSI7   {rsi_v[-1]:.1f}" if rsi_v[-1] is not None else "RSI7",
             transform=axr.transAxes, color=DIM, fontsize=9,
             fontweight="bold", family="DejaVu Sans Mono")

    # ---- MACD -----------------------------------------------------------
    for i, h in enumerate(hist):
        if h is None:
            continue
        col = MACD_UP if h >= 0 else MACD_DN
        axm.bar(i, h, color=col, width=0.75, alpha=0.85, edgecolor=col, linewidth=0)
    xs_m = [i for i, v in enumerate(macd_l) if v is not None]
    if xs_m:
        axm.plot(xs_m, [macd_l[i] for i in xs_m], color=EMA_COL, linewidth=0.9)
        axm.plot(xs_m, [sig_l[i]  for i in xs_m], color=MACD_SIG, linewidth=0.9)
    axm.axhline(0, color=DIM, linewidth=0.4, alpha=0.6)
    axm.text(0.005, 0.86, "MACD  5/13/5", transform=axm.transAxes, color=DIM, fontsize=9,
             fontweight="bold", family="DejaVu Sans Mono")
    axm.text(0.005, 0.62, "MACD  SIGNAL", transform=axm.transAxes, color=DIM, fontsize=8,
             family="DejaVu Sans Mono")

    # ---- bottom time axis ----------------------------------------------
    step = max(1, n // 12)
    ticks = list(range(0, n, step))
    axm.set_xticks(ticks)
    axm.set_xticklabels(
        [time.strftime("%H:%M", time.localtime(data[i]["time"])) for i in ticks],
        color=DIM, fontsize=9, family="DejaVu Sans Mono",
    )

    # ---- headers overlay (drawn in figure coords) -----------------------
    # symbol title
    sym = title.split("·")[0].strip() if title else ""
    fig.text(0.028, 0.955, sym.upper(), color="#e6f7ff", fontsize=20,
             fontweight="bold", family="DejaVu Sans Mono",
             path_effects=[pe.withStroke(linewidth=0.4, foreground="#00343d")])
    fig.text(0.028, 0.923, "CANDLE VIEW", color=DIM, fontsize=9.5,
             fontweight="bold", family="DejaVu Sans Mono")

    # right-side timestamp box
    utc_off = 6
    now_dt = datetime.now(timezone.utc) + timedelta(hours=utc_off)
    ts = now_dt.strftime("%Y-%m-%d %H:%M") + f" UTC+{utc_off}"
    fig.patches.append(FancyBboxPatch(
        (0.795, 0.94), 0.163, 0.032, transform=fig.transFigure,
        boxstyle="round,pad=0.004", linewidth=0.7,
        edgecolor=BORDER, facecolor="#000000",
    ))
    fig.text(0.877, 0.956, ts, color=TEXT, fontsize=9.5, ha="center", va="center",
             family="DejaVu Sans Mono", fontweight="bold")

    # info bar
    trend_char = "UP \u25b2" if closes[-1] > closes[-5] else "DOWN \u25bc"
    trend_col = UP if closes[-1] > closes[-5] else DOWN
    info_parts = [
        ("TF: M1",   TEXT),
        (trend_char, trend_col),
        ("EMA20 FLAT", TEXT),
        ("PAT B",    TEXT),
        ("VOL MA14", TEXT),
        ("BB20",     TEXT),
        ("RSI7",     TEXT),
        ("MACD",     TEXT),
    ]
    fig.patches.append(FancyBboxPatch(
        (0.028, 0.878), 0.60, 0.034, transform=fig.transFigure,
        boxstyle="round,pad=0.003", linewidth=0.6,
        edgecolor=BORDER, facecolor="#000000",
    ))
    x_cursor = 0.040
    for i, (txt, col) in enumerate(info_parts):
        fig.text(x_cursor, 0.895, txt, color=col, fontsize=9, va="center",
                 fontweight="bold", family="DejaVu Sans Mono")
        x_cursor += 0.070
        if i < len(info_parts) - 1:
            fig.text(x_cursor - 0.008, 0.895, "|", color=DIM, fontsize=9, va="center",
                     family="DejaVu Sans Mono")

    # (developer stamp removed per user request)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
