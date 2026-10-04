from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    """
    Engine com pool de conexões reaproveitadas.

    Abrir uma conexão nova (TLS até o pooler da Supabase) custa ~1.3 s; com o
    pool isso acontece só na primeira requisição. Compatível com o pooler em
    modo transaction (porta 6543): o PgBouncer pode trocar a conexão do
    servidor entre transações, então desligamos o cache de prepared statements
    e damos um nome único a cada um para não colidirem.
    """
    url = str(settings.database_url)  # explicit str() — pydantic v2 safety
    return create_async_engine(
        url,
        echo=settings.environment == "development",
        pool_size=5,
        max_overflow=5,
        # Sem pre-ping: ele custa ~0.5 s por requisição (ida e volta até us-east-1).
        # Em vez disso, renovamos conexões antes que o pooler as derrube por ociosidade.
        pool_pre_ping=False,
        pool_recycle=180,
        connect_args={
            "statement_cache_size": 0,  # required for PgBouncer/Supabase pooler
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
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
