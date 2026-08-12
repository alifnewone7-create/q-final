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

def _main():
    import start  # obfuscated launcher module

    # start.py starts the bot inside its _run() function, which only runs
    # under `if __name__ == "__main__"`. When imported that guard is False,
    # so we must call it explicitly.
    if hasattr(start, "_run"):
        start._run()
    elif hasattr(start, "main"):
        start.main()


if __name__ == "__main__":
    try:
        _main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        pass
    except BaseException:
        # show the real error instead of letting the window close instantly
        import traceback
        # restore a real stdout in case it was redirected by start.py
        try:
            sys.stdout = sys.__stdout__
        except Exception:
            pass
        print("\n==================  ERROR  ==================")
        traceback.print_exc()
        print("=============================================")
        try:
            input("\nPress ENTER to close this window...")
        except Exception:
            pass
