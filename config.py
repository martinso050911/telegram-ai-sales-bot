import os
import sys
import ssl
from pathlib import Path
from dotenv import load_dotenv

# Global SSL patch for Windows local environments missing CA certificates
try:
    _orig_create_default_context = ssl.create_default_context
    def _insecure_default_context(*args, **kwargs):
        ctx = _orig_create_default_context(*args, **kwargs)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    ssl.create_default_context = _insecure_default_context
    ssl._create_default_https_context = _insecure_default_context
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sales_b2b.db")

SECRET_KEY = os.getenv("SECRET_KEY", "default_b2b_secret")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "adminpass")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in .env file!")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in .env file!")
