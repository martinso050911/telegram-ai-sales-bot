import os
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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

bot_polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_polling_task
    logger.info("Initializing B2B Web Service & Database...")

    # 1. Initialize SQLite Database Tables
    await init_db()

    # 2. Register Telegram Router
    dp.include_router(bot_router)

    # 3. Clear webhook and start Telegram bot long-polling in background asyncio task
    await bot.delete_webhook(drop_pending_updates=True)
    bot_polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Telegram Bot polling task launched successfully in background!")

    yield

    # Shutdown lifecycle
    logger.info("Shutting down B2B Web Service & Telegram Bot...")
    if bot_polling_task:
        bot_polling_task.cancel()
        try:
            await bot_polling_task
        except asyncio.CancelledError:
            pass
    await bot.session.close()
    logger.info("Shutdown completed.")

# Instantiate FastAPI application
app = FastAPI(
    title="AI Sales Pro B2B Service",
    lifespan=lifespan
)

# Mount Static Files
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Include Web & API routes
app.include_router(web_router)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting B2B Web Application Server on http://{host}:{port} ...")
    uvicorn.run(
        "main:app",
        host=host,
        port=port
    )
