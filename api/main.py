from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.items import router as items_router
from routers.goals import goals_router, milestones_router
from routers.wishlist import router as wishlist_router
from routers.daily_logs import router as daily_logs_router
from routers.habits import router as habits_router
from routers.finance.wallets import router as wallets_router
from routers.finance.transactions import router as transactions_router, overview_router
from routers.finance.debts import router as debts_router
from routers.finance.simulator import router as simulator_router
from routers.finance.health_logs import router as health_logs_router
from routers.finance.budgets import router as budgets_router

app = FastAPI(
    title="Station One API",
    description="Backend unificado para o Station One — operações, missões, wishlist e financial core.",
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
app.include_router(milestones_router)
app.include_router(wishlist_router)
app.include_router(daily_logs_router)
app.include_router(habits_router)

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
