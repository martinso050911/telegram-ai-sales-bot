import logging
import ssl
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
import config

logger = logging.getLogger(__name__)

class CustomAiohttpSession(AiohttpSession):
    """Custom AiohttpSession ensuring SSL compatibility on Windows environments."""
    async def create_session(self) -> aiohttp.ClientSession:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        return aiohttp.ClientSession(
            connector=connector,
            json_serialize=self.json_dumps,
        )

# Initialize shared Bot and Dispatcher instances
session = CustomAiohttpSession()
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher()

async def notify_admin_new_lead(lead_id: int, name: str, phone: str, email: str = None, company: str = None, message: str = None):
    """Sends immediate Telegram notification to admin when a new lead is submitted on website."""
    if not config.ADMIN_TELEGRAM_ID:
        logger.warning("ADMIN_TELEGRAM_ID is not configured in .env. Skipping Telegram lead notification.")
        return

    notification_text = (
        f"🚨 **НОВАЯ ЗАЯВКА С САЙТА №{lead_id}**\n\n"
        f"👤 **Имя:** {name}\n"
        f"📞 **Телефон:** `{phone}`\n"
    )
    if email:
        notification_text += f"✉️ **Email:** {email}\n"
    if company:
        notification_text += f"🏢 **Компания:** {company}\n"
    if message:
        notification_text += f"💬 **Сообщение:**\n_{message}_\n"

    notification_text += f"\n📅 _Поступило в систему и сохранено в базе данных._"

    try:
        await bot.send_message(
            chat_id=config.ADMIN_TELEGRAM_ID,
            text=notification_text,
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Notification for lead #{lead_id} sent successfully to admin {config.ADMIN_TELEGRAM_ID}.")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification to admin for lead #{lead_id}: {e}")
