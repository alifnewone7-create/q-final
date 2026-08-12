# PRD — Binary Algo Prime (Quotex Telegram Signal Bot)

## Original Problem Statement
1. Clone https://github.com/alifnewone7-create/q-run.git into /app/backend (default Emergent boilerplate removed). DONE (previous session)
2. Build full Telegram bot system on top of pyquotex (this session):
   - Bot token: 8940978558:AAF3YQ7HRtCL4dqlOR-Ry1oPFf0ZQkhyG8o, admin-only (user id 7188243734)
   - /start → 4 options: Add Channel, My Channels, Start Session, Settings
   - Add Channel via native channel picker; bot must be admin in channel (else warn)
   - Start Session → OTC / Real / Crypto / All Markets categories; markets shown as inline buttons with live payout % from pyquotex, 16/page with Next/Prev, multi-select with ✅ tick, selected list in message text
   - Start Session button → choose connected channel → signals go there
   - Signal = chart image + "✨ Binary Algo Prime ✨" caption (Asset, Signal CALL/PUT, Entry Time, MTG: 1 Step Required, Owner @Iamhear1, Analysis line)
   - Analysis predicts NEXT 1m candle (CALL = next candle green, PUT = red)
   - MTG-1 ONLY (No-MTG removed per user); entry 11:18 → check 11:18 candle at 11:19; if loss check next candle at 11:20 (✅¹ win / ❌ loss)
   - Result message with fresh chart image at result time
   - All signals+results saved to JSON (data/signals.json)
   - Close Session stops signals; Send Partial button posts partial report to channel (date, total, per-signal lines M1 ASSET HH:MM DIR ✅/✅¹/❌, Placar WxL -> %, win/loss summary)
   - Settings → MTG Settings → only MTG-1 option, current shown in text

## User Choices
- Quotex: quotex-new@hamham.uk / iamhear, PRACTICE account
- Chart generated from candle data (matplotlib dark theme) — no browser on server
- Owner fixed: @Iamhear1
- **User will test the full flow on their LOCAL PC** — Quotex login from this cloud pod is Cloudflare-blocked (verified: "Login failed. Unknown error"). Telegram side works from pod.

## Architecture (standalone Python app, no web server/DB)
```
/app/backend/
├── bot.py         # entry point — python-telegram-bot v22 polling, all menus/callbacks
├── sessions.py    # SessionManager SM: signal loop, MTG-1 result, partial report
├── ticks.py       # TickCollector: all-market tick→1m OHLC (running candle), starts with backend
├── qx.py          # QuotexManager: connect, get_markets(category), get_candles_1m
├── analysis.py    # next-candle scoring (pressure/momentum/wick/streak), reason text
├── charting.py    # dark candlestick PNG (matplotlib Agg)
├── storage.py     # JSON: data/channels.json, data/settings.json, data/signals.json
├── config.py      # loads .env
├── .env           # BOT_TOKEN, ADMIN_ID, QUOTEX_EMAIL/PASSWORD, ACCOUNT_TYPE, OWNER_TAG
├── pyquotex/      # bundled library (from cloned repo)
└── engine.py      # OLD desktop EEL app from repo (untouched, not used by bot)
```
Run: `cd backend && pip install -r requirements.txt && python bot.py`

## Implemented (01.08.2026 / June 2026 session)
- Full bot: main menu, add channel (KeyboardButtonRequestChat + admin check + auto-register via my_chat_member), my channels w/ remove, category → paginated multi-select market keyboard w/ payout %, channel pick, session start/close, send partial, settings (MTG-1 only)
- Signal engine: analysis window at sec ~14, entry = next minute, signal w/ chart, candle1 check (+63s), MTG step candle2 (+123s), result w/ fresh chart, JSON persistence
- **Tick collector (`ticks.py`)**: starts with backend (post_init), subscribes ALL open markets on ONE Quotex websocket (1 account is enough — confirmed to user), discards partial first minute (starts at next minute boundary), builds live 1m OHLC per market from ticks (incl. RUNNING candle), resubscribes every 5min, reconnects if 90s idle. Sessions merge API history + tick candles: chart images now include the running candle; analysis uses closed candles only; results prefer tick-built candles (instant) w/ API fallback.
- Tested locally: captions/partial format match spec exactly, chart render verified (screenshot), bot polls Telegram OK, tick→OHLC building + drain + merged candles unit-tested w/ fakes, Quotex error handled gracefully (collector retries every 30s)
- NOT testable from pod: real Quotex data flow (Cloudflare) — user validates on local PC

## Notes / Cautions
- Do NOT run `python bot.py` persistently on the pod while user tests locally — two getUpdates pollers conflict (Telegram 409).
- Supervisor backend/frontend are not used (standalone script app); ignore supervisor crash loops.
- requirements.txt appended (not frozen) to stay portable for user's local PC.

## Bug Fixes (01.08.2026, after user local test)
- User local PC error `Expecting value: line 1 column 1 (char 0)`: root cause = `pyquotex/http/login.py get_profile()` did json.loads on the FIRST script tag of /trade page (empty tag → JSONDecodeError). Fixed: scans all script tags for `window.settings`, regex-extracts JSON, 3 retries, graceful (None, None) + clear login error message. `qx.ensure_connected` now deletes stale session.json on failure and wraps errors as ConnectionError. TICKS.stop() wired to Application post_shutdown (no more pending-task warning).
- Testing agent iteration_1: 16/16 unit tests pass (login fix cases, qx wrapping, tick OHLC, merged candles) + bot smoke clean. Test file: /app/backend/tests/test_bot_units.py

- Iteration 2 (user local: "Login succeeded but session token could not be extracted", session.json never created): RCA = (1) login flow requests `Accept-Encoding: br` but Brotli lib missing on user PC → garbage HTML → window.settings invisible; (2) get_profile ignored the login POST response (already on /trade). Fix: Brotli==1.2.0 added to requirements, login.py rewritten — `_extract_settings()` 3-tier extractor (raw-HTML window.settings regex → script scan → "token":"..." fallback), POST-response reuse, on failure dumps page to `login_debug.html` (user can share it for diagnosis). Testing agent iteration_2: 24/24 tests pass. USER MUST re-run `pip install -r requirements.txt` locally.

## Backlog
- P1: User local test feedback fixes (Quotex login/session flow)
- P2: Owner tag via settings, signal confidence threshold setting, multi-channel broadcast per session
