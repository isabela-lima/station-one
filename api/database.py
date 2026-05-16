from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    """Lazy engine factory — avoids import-time failures and works with NullPool."""
    url = str(settings.database_url)  # explicit str() — pydantic v2 safety
    return create_async_engine(
        url,
        echo=settings.environment == "development",
        poolclass=NullPool,  # required for Supabase pooler (transaction mode)
        connect_args={
            "statement_cache_size": 0,  # required for PgBouncer/Supabase pooler
            "ssl": "require",            # required for Supabase (all connection types)
        },
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
