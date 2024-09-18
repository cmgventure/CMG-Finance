from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.database.models import Base

engine = create_async_engine(
    settings.postgres_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=60
)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# import asyncio
# asyncio.run(create_all())
