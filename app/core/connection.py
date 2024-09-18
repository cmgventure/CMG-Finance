from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.database.models import Base

engine = create_async_engine(
    settings.postgres_url,
    future=True,
    echo=False,
    pool_recycle=1800,
    pool_pre_ping=True,
    pool_size=100,
    max_overflow=10
)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        logger.critical("Opening session")
        yield session
        logger.critical("Closing session")


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
