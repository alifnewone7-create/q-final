#!/usr/bin/env python3
"""PyInstaller entry point (NOT obfuscated).

Handles frozen-app paths so that .env (and data) live NEXT TO the .exe
and the bundled obfuscated modules stay importable.
"""
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # folder where the .exe actually lives (user-editable .env goes here)
    APP_DIR = Path(sys.executable).parent
    # make the bundled loose modules importable
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and meipass not in sys.path:
        sys.path.insert(0, meipass)
else:
    APP_DIR = Path(__file__).parent

# load the .env that sits next to the exe BEFORE importing config
try:
    from dotenv import load_dotenv
    load_dotenv(APP_DIR / ".env")
except Exception:
    pass

# run everything from the exe folder so data/ is created next to the exe
try:
    os.chdir(APP_DIR)
except Exception:
    pass

import start  # obfuscated launcher -> starts the Telegram bot
