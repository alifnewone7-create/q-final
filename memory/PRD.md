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

## Update — 2026-06 (Premium Emoji JSON system)
- Removed the old hardcoded premium-emoji map in `messages.py` (key -> (emoji_id, plain)).
- New `backend/premium_emojis.py`: `load_json_file/save_json_file`, `PREMIUM_EMOJIS_FILE = data/premium_emojis.json`, `DEFAULT_PREMIUM_EMOJIS` (✅, ✨), `load_premium_emojis()`, `p_emoji(char)`, `premiumize(text)` (auto-convert all known plain emoji, skips already-tagged), `strip_custom_emoji()`.
- `backend/data/premium_emojis.json` seeded with {"✅": "6217660507575291616", "✨": "5325547803936572038"}.
- `messages.py` templates now use plain emoji only; `notifier.py` runs `premiumize()` on every outgoing channel message/caption (HTML parse mode) with plain-emoji fallback if Telegram rejects entities.
- Backend NOT run per user instruction; user will test on Telegram.
- NOTE: `backend/tests/test_messages.py` still asserts the old `messages.EMOJI` tuple shape — needs updating if the test suite is run.

### 2026-06 Premium emoji not rendering — diagnostics added
- `notifier._kept_custom_emoji(msg)` + `Notifier._verify()`: Telegram drops custom_emoji entities SILENTLY (no error) when the bot is not allowed to use them, so the sent message is inspected and a one-time loud warning is logged.
- `premium_emojis.reload_premium_emojis()` for runtime JSON reload.
- New admin command `/emojitest` in bot.py: reloads JSON, validates every id via getCustomEmojiStickers (reports id-vs-emoji mismatch), sends a sample to the admin chat + every connected channel and reports premium vs plain per chat.
- Telegram rule (Bot API 9.4, Feb 2026): a bot can only send custom emoji if the OWNER account has active Telegram Premium (or a Fragment username is assigned to the bot); the entity must wrap exactly the one emoji that the custom emoji id belongs to, otherwise it is ignored. Channel posts are the most restricted case.
- Local env has no BOT_TOKEN and aiogram is not installed, so only py_compile + offline premiumize checks were possible. User tests on Telegram.

### 2026-06 Premium emoji via Telegram Premium USER account (MTProto)
- Bots cannot render custom emoji in channel posts, so channel posts now go through a Telethon user account when configured.
- New `backend/user_sender.py` (Telethon 1.44.0, StringSession): `configured()`, `USER.send_message/send_photo` with real `MessageEntityCustomEmoji` entities built from `premium_emojis.to_entities()` (UTF-16 offsets verified offline).
- New `backend/userbot_login.py`: interactive one-time login printing `TG_SESSION` (also reports whether the account has Premium).
- `config.py`: optional `TG_API_ID`, `TG_API_HASH`, `TG_SESSION` (empty placeholders added to backend/.env).
- `notifier.py`: if the three vars are set -> post as user account; any failure logs and falls back to the bot. `NOTIFY.close()` disconnects the Telethon client.
- `/emojitest` now reports which sender is active, the user accounts Premium flag, id-vs-emoji validation and per-channel render result.
- requirements.txt: added `Telethon==1.44.0`. Backend not run per user instruction.
