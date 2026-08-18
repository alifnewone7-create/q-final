import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
QUOTEX_EMAIL = os.environ["QUOTEX_EMAIL"]
QUOTEX_PASSWORD = os.environ["QUOTEX_PASSWORD"]
ACCOUNT_TYPE = os.environ.get("ACCOUNT_TYPE", "PRACTICE")
OWNER_TAG = os.environ.get("OWNER_TAG", "@Iamhear1")

# Optional Telegram Premium user account (MTProto) used for channel posts so
# that premium custom emoji render. Leave empty to post with the bot instead.
TG_API_ID = os.environ.get("TG_API_ID", "").strip()
TG_API_HASH = os.environ.get("TG_API_HASH", "").strip()
TG_SESSION = os.environ.get("TG_SESSION", "").strip()

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
