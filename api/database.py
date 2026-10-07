import logging
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    """
    Engine com pool de conexões reaproveitadas (abrir uma conexão TLS até o pooler
    da Supabase custa ~1-2 s; com o pool isso acontece só na subida).

    Use o pooler em **modo session** (porta 5432). No modo transaction (6543) o
    PgBouncer/Supavisor pode trocar a conexão do servidor entre um PREPARE e o
    EXECUTE quando há consultas em paralelo — medimos 36 de 60 sessões falhando
    com "prepared statement does not exist". Se a URL ainda usar a 6543, mantemos
    o paliativo (sem cache de statements, nomes únicos) e avisamos no log.
    """
    url = str(settings.database_url)  # explicit str() — pydantic v2 safety
    connect_args: dict = {"ssl": "require"}  # required for Supabase (all connection types)
    if urlsplit(url).port == 6543:
        logging.getLogger("station_one").warning(
            "DATABASE_URL usa o pooler em modo transaction (porta 6543): consultas em paralelo "
            "podem falhar. Troque para o modo session (porta 5432)."
        )
        connect_args |= {
            "statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        }
    return create_async_engine(
        url,
        echo=settings.sql_echo,
        pool_size=5,
        max_overflow=5,
        # Sem pre-ping: ele custa uma ida e volta até us-east-1 por requisição.
        # Em vez disso, renovamos conexões antes que o pooler as derrube por ociosidade.
        pool_pre_ping=False,
        pool_recycle=180,
        connect_args=connect_args,
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
