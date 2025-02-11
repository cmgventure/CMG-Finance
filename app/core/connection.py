from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.postgres_url,
    future=True,
    echo=False,
    pool_recycle=settings.POOL_RECYCLE,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
