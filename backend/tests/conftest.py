"""Pytest bootstrap: env vars + sys.path so backend modules import cleanly."""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("QUOTEX_EMAIL", "a@b.c")
os.environ.setdefault("QUOTEX_PASSWORD", "p")
