from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import Debt, Transaction, Wallet
from schemas.finance import AutonomyIndicator, FinanceOverview, TransactionCreate, TransactionOut, WalletOut

router = APIRouter(prefix="/finance/transactions", tags=["finance"])


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    user_id: CurrentUser,
    db: DB,
    wallet_id: UUID | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    q = (
        select(Transaction)
        .where(Transaction.user_id == UUID(user_id))
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
    )
    if wallet_id:
        q = q.where(Transaction.wallet_id == wallet_id)
    if category:
        q = q.where(Transaction.category == category)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(user_id: CurrentUser, db: DB, body: TransactionCreate):
    data = body.model_dump()
    if not data.get("date"):
        data["date"] = date.today()
    txn = Transaction(user_id=UUID(user_id), **data)
    db.add(txn)
    await db.flush()
    await db.refresh(txn)
    return txn


# ─── Finance Overview (aggregated) ───────────────────────

overview_router = APIRouter(prefix="/finance/overview", tags=["finance"])


@overview_router.get("", response_model=FinanceOverview)
async def get_overview(user_id: CurrentUser, db: DB):
    uid = UUID(user_id)

    # Wallets with balances
    wallets_result = await db.execute(select(Wallet).where(Wallet.user_id == uid))
    wallets = wallets_result.scalars().all()

    wallet_outs = []
    total_balance = Decimal("0")
    for w in wallets:
        bal_result = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.wallet_id == w.id
            )
        )
        balance = bal_result.scalar() or Decimal("0")
        out = WalletOut.model_validate(w)
        out.balance = balance
        wallet_outs.append(out)
        if w.type == "cash":
            total_balance += balance  # only liquid balance for autonomy calc

    # Debt total
    debt_result = await db.execute(
        select(func.coalesce(func.sum(Debt.current_amount), 0)).where(Debt.user_id == uid)
    )
    total_debt = debt_result.scalar() or Decimal("0")

    # Average daily expense (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == uid,
            Transaction.amount < 0,
            Transaction.date >= thirty_days_ago,
        )
    )
    recent_expense = abs(expense_result.scalar() or Decimal("0"))
    avg_daily = recent_expense / 30 if recent_expense else Decimal("50")

    # Autonomy: days of runway based on liquid wallet
    days_of_runway = float(total_balance / avg_daily) if avg_daily > 0 else 0.0

    # Alerts
    alerts = []
    if total_debt > 0:
        alerts.append(f"Dívida ativa de R${total_debt:,.2f}. Priorize o Inflow Extra para quitação.")
    if days_of_runway < 7:
        alerts.append("⚠️ Menos de 7 dias de fôlego disponível.")

    return FinanceOverview(
        wallets=wallet_outs,
        total_debt=total_debt,
        autonomy=AutonomyIndicator(
            days_of_runway=round(days_of_runway, 1),
            avg_daily_expense=avg_daily,
            free_balance=total_balance,
            currency="BRL",
        ),
        alerts=alerts,
    )
