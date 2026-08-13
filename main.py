import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Set absolute base path to ensure all modules (database, services, bot, web) are strictly resolvable on Render / Uvicorn
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update

import config
from database.connection import init_db
from services.telegram_service import bot, dp
from bot.handlers import router as bot_router
from web.app import web_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Webhook path constant: /webhook
WEBHOOK_PATH = "/webhook"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing B2B Web Service & Database...")

    # 1. Initialize SQLite Database Tables
    await init_db()

    # 2. Register Telegram Router with Dispatcher
    dp.include_router(bot_router)

    # 3. Setup Telegram Webhook on startup using RENDER_EXTERNAL_URL
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_external_url:
        base_url = render_external_url.rstrip("/")
        webhook_url = f"{base_url}{WEBHOOK_PATH}"
        try:
            await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
            logger.info(f"Telegram Bot Webhook successfully configured at: {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to set Telegram Webhook: {e}", exc_info=True)
    else:
        logger.warning(
            "RENDER_EXTERNAL_URL is not set. Webhook automatic registration skipped. "
            "Set RENDER_EXTERNAL_URL on Render environment variables to activate webhook."
        )

    yield

    # Shutdown lifecycle
    logger.info("Shutting down B2B Web Service & Telegram Bot...")
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Telegram Bot Webhook removed.")
    except Exception as e:
        logger.error(f"Error removing webhook during shutdown: {e}")

    try:
        await bot.session.close()
    except Exception as e:
        logger.error(f"Error closing bot session: {e}")
    logger.info("Shutdown completed.")

# Instantiate FastAPI application
app = FastAPI(
    title="Sales Pro B2B Service",
    lifespan=lifespan
)

# Webhook POST route for Telegram updates
@app.post("/webhook")
@app.post(f"/webhook/{config.BOT_TOKEN}")
async def bot_webhook(request: Request):
    """Endpoint receiving POST updates from Telegram Webhook and feeding them to Aiogram."""
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing Telegram webhook update: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}

# Mount Static Files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Include Web & API routes (includes GET / landing page with 200 OK response)
app.include_router(web_router)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Sales Pro Web Application Server on http://{host}:{port} ...")
    uvicorn.run(
        "main:app",
        host=host,
        port=port
    )
