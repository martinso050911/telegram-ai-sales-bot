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
    """Initializes database tables and creates default admin user from .env if absent."""
    from database.models import User
    from services.auth_service import hash_password

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

    # Auto-create default admin user from .env if not exists
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
                    # Ensure existing admin has role='admin'
                    if admin.role != "admin":
                        admin.role = "admin"
                        await db.commit()
                        logger.info(f"Updated user '{admin_username}' role to 'admin'.")
        except Exception as e:
            logger.error(f"Error checking/creating default admin user: {e}", exc_info=True)

async def get_db():
    """Dependency helper for acquiring async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
