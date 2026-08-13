"""Quotex connection manager built on the bundled pyquotex package."""
import asyncio
import os
import time
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("WEBSOCKET_CLIENT_CA_BUNDLE", certifi.where())

from pyquotex.stable_api import Quotex

from config import QUOTEX_EMAIL, QUOTEX_PASSWORD, ACCOUNT_TYPE

CRYPTO_CODES = {
    "ADAUSD_otc", "APTUSD_otc", "ARBUSD_otc", "ATOUSD_otc", "AVAUSD_otc",
    "AXSUSD_otc", "BCHUSD_otc", "BNBUSD_otc", "BONUSD_otc", "BTCUSD_otc",
    "DASUSD_otc", "DOGUSD_otc", "DOTUSD_otc", "ETCUSD_otc", "ETHUSD_otc",
    "FLOUSD_otc", "GALUSD_otc", "HMSUSD_otc", "LINUSD_otc", "LTCUSD_otc",
    "MELUSD_otc", "SHIBUSD_otc", "SOLUSD_otc", "TIAUSD_otc", "TONUSD_otc",
    "TRUUSD_otc", "TRXUSD_otc", "WIFUSD_otc", "XRPUSD_otc", "ZECUSD_otc",
}
CRYPTO_BASES = {c.replace("_otc", "") for c in CRYPTO_CODES}


def category_of(code):
    if code in CRYPTO_CODES or code.replace("_otc", "") in CRYPTO_BASES:
        return "crypto"
    return "otc" if code.endswith("_otc") else "real"


class QuotexManager:
    def __init__(self):
        self.client = None
        self.connected = False
        self._lock = asyncio.Lock()

    async def ensure_connected(self):
        async with self._lock:
            if self.connected and self.client:
                try:
                    if await self.client.check_connect():
                        return
                except Exception:
                    pass
            self.connected = False
            self.client = Quotex(
                email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD,
                host="qxbroker.com", lang="en",
            )
            # Force a FRESH login every time: drop any cached/expired session
            # so pyquotex always runs a full authenticate() instead of reusing
            # a stale SSID token from session.json.
            try:
                Path("session.json").unlink(missing_ok=True)
            except Exception:
                pass
            try:
                self.client.session_data = {}
            except Exception:
                pass
            try:
                check, reason = await self.client.connect()
            except Exception as e:
                Path("session.json").unlink(missing_ok=True)
                raise ConnectionError(f"Quotex connect error: {e}")
            if not check:
                Path("session.json").unlink(missing_ok=True)
                raise ConnectionError(f"Quotex login failed: {reason}")
            await self.client.change_account(ACCOUNT_TYPE)
            await self.client.get_instruments()
            self.connected = True

    async def get_markets(self, category):
        """Returns open markets for a category: [{code, display, payout}] sorted by payout desc."""
        await self.ensure_connected()
        instruments = await self.client.get_instruments()
        markets = []
        for i in instruments:
            try:
                code = i[1]
                display = i[2].replace("\n", "")
                is_open = bool(i[14])
                payout = i[-9]
                if not isinstance(payout, (int, float)):
                    payout = i[5]
            except (IndexError, TypeError):
                continue
            if not code or not is_open:
                continue
            if not isinstance(payout, (int, float)) or payout <= 0:
                continue
            if category not in ("all", "otcreal") and category_of(code) != category:
                continue
            if category == "otcreal" and category_of(code) == "crypto":
                continue
            markets.append({"code": code, "display": display, "payout": int(payout)})
        markets.sort(key=lambda m: (-m["payout"], m["code"]))
        return markets

    async def get_candles_1m(self, code, count=60):
        """Returns normalized 1m candles sorted by time: [{time, open, high, low, close}]."""
        await self.ensure_connected()
        raw = await self.client.get_candles(code, time.time(), count * 60, 60)
        out = {}
        for c in raw or []:
            if not isinstance(c, dict):
                continue
            if not all(k in c for k in ("time", "open", "high", "low", "close")):
                continue
            ts = (int(float(c["time"])) // 60) * 60
            out[ts] = {
                "time": ts, "open": float(c["open"]), "high": float(c["high"]),
                "low": float(c["low"]), "close": float(c["close"]),
            }
        return [out[k] for k in sorted(out)]
