import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine
from routers.items import router as items_router
from routers.goals import goals_router
from routers.wishlist import router as wishlist_router
from routers.journal import router as journal_router
from routers.habits import router as habits_router
from routers.settings import router as settings_router
from routers.assistant import router as assistant_router
from routers.finance.wallets import router as wallets_router
from routers.finance.transactions import router as transactions_router, overview_router
from routers.finance.debts import router as debts_router
from routers.finance.simulator import router as simulator_router
from routers.finance.health_logs import router as health_logs_router
from routers.finance.budgets import router as budgets_router

# Logs do próprio app (ex.: tempos do assistente) no terminal, independentes do
# nível do uvicorn. SQL continua de fora (ver SQL_ECHO em config.py).
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(name)s: %(message)s", "%H:%M:%S"))
_app_log = logging.getLogger("station_one")
_app_log.setLevel(logging.INFO)
_app_log.addHandler(_handler)
_app_log.propagate = False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Abre conexões com o banco já na subida: a primeira requisição do dia não
    # paga os ~2,5 s de abrir conexão TLS até o pooler da Supabase.
    try:
        await asyncio.gather(*(_warm_connection() for _ in range(2)))
    except Exception:  # sem banco na subida (ex.: testes/CI): segue, conecta sob demanda
        pass
    yield


async def _warm_connection() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("select 1"))


app = FastAPI(
    lifespan=lifespan,
    title="Station One API",
    description="Backend unificado para o Station One — operações, missões, diário, wishlist e financial core.",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

# ─── CORS ─────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers: Station One core ────────────────────────────────────────
app.include_router(items_router)
app.include_router(goals_router)
app.include_router(wishlist_router)
app.include_router(journal_router)
app.include_router(habits_router)
app.include_router(settings_router)
app.include_router(assistant_router)

# ─── Routers: Financial Core ──────────────────────────────
app.include_router(wallets_router)
app.include_router(transactions_router)
app.include_router(overview_router)
app.include_router(debts_router)
app.include_router(simulator_router)
app.include_router(health_logs_router)
app.include_router(budgets_router)


@app.get("/health")
async def health_check():
    return {"status": "online", "service": "station-one-api"}
