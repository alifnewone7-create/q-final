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

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
