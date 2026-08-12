import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import config

logger = logging.getLogger(__name__)

# Async Engine for SQLite
engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    future=True
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Initializes database tables and updates prompt & default admin user."""
    from database.models import User, SystemPromptConfig
    from services.auth_service import hash_password

    UZS_SYSTEM_PROMPT = """Ты — высококлассный AI-консультант по продажам B2B-компании.
Твоя главная цель — выявлять потребности клиентов, профессионально презентовать продукты/услуги компании, выявлять боли бизнеса, обрабатывать возражения и побуждать к оставлению заявки на консультацию или покупку.

СТРОГИЕ ЯЗЫКОВЫЕ ПРАВИЛА:
1. Отвечай ИСКЛЮЧИТЕЛЬНО на чистом, грамотном и естественном русском языке.
2. Категорически ЗАПРЕЩЕНО использовать любые китайские иероглифы (например, 客户), слова или гибриды вроде «客户ский»! Всегда используй исключительно чистое русское слово «клиентский» (например: «клиентский опыт», «клиентский сервис», «клиентская база»).

ВАЖНЕЙШЕЕ ПРАВИЛО ПО ВАЛЮТЕ И ЦЕНАМ:
1. Все цены, стоимости тарифов и финансовых условий ты обязан указывать ИСКЛЮЧИТЕЛЬНО в узбекских сумах (UZS).
2. Наша тарифная сетка:
   - Тариф «Старт»: 650 000 UZS / мес (до 1 000 чат-сессий, Telegram-бот).
   - Тариф «Бизнес Pro»: 1 700 000 UZS / мес (безлимитные сессии, веб-виджет + Telegram бот, защищенная админка).
   - Тариф «Enterprise»: Индивидуальный расчет под задачи клиента.
3. Категорически запрещено указывать рубли (руб, ₽) или любые другие валюты!

Правила работы:
1. Будь вежливым, деловым, позитивным и эмпатичным.
2. Задавай 1-2 уточняющих вопроса для погружения в сферу деятельности клиента.
3. Фокусируйся на выгодах, ROI и ценности для бизнеса.
4. Отвечай кратко, структурированно и с понятным призывом к действию (CTA).
5. При предложении оставить заявку напоминай про удобную форму на сайте!
"""


    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

    # Auto-create default admin user from .env
    admin_username = config.ADMIN_USERNAME
    admin_password = config.ADMIN_PASSWORD
    if admin_username and admin_password:
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.username == admin_username))
                admin = result.scalar_one_or_none()
                if not admin:
                    new_admin = User(
                        username=admin_username,
                        hashed_password=hash_password(admin_password),
                        role="admin"
                    )
                    db.add(new_admin)
                    await db.commit()
                    logger.info(f"🔑 Default admin user '{admin_username}' created successfully!")
                else:
                    if admin.role != "admin":
                        admin.role = "admin"
                        await db.commit()

                # Always sync system prompt to UZS currency
                prompt_res = await db.execute(select(SystemPromptConfig).where(SystemPromptConfig.key == "sales_consultant"))
                prompt_entry = prompt_res.scalar_one_or_none()
                if not prompt_entry:
                    prompt_entry = SystemPromptConfig(key="sales_consultant", prompt_text=UZS_SYSTEM_PROMPT)
                    db.add(prompt_entry)
                    await db.commit()
                else:
                    prompt_entry.prompt_text = UZS_SYSTEM_PROMPT
                    await db.commit()
                    logger.info("Updated SystemPromptConfig in DB to UZS currency.")

        except Exception as e:
            logger.error(f"Error checking/creating default admin user or system prompt: {e}", exc_info=True)

async def get_db():
    """Dependency helper for acquiring async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
