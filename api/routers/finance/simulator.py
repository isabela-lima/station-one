from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import Transaction, Wallet
from schemas.finance import MonthImpact, SimulatorRequest, SimulatorResponse

router = APIRouter(prefix="/finance/simulator", tags=["finance"])


@router.post("", response_model=SimulatorResponse)
async def simulate_purchase(user_id: CurrentUser, db: DB, body: SimulatorRequest):
    uid = UUID(user_id)

    # Get current total free balance across all wallets
    balance_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == uid
        )
    )
    total_balance = balance_result.scalar() or Decimal("0")

    # Average daily expense over last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == uid,
            Transaction.amount < 0,
            Transaction.date >= thirty_days_ago,
        )
    )
    total_recent_expense = abs(expense_result.scalar() or Decimal("0"))
    avg_daily = total_recent_expense / 30 if total_recent_expense else Decimal("50")

    monthly_installment = body.amount / body.installments
    today = date.today()
    projection = []
    running_balance = total_balance

    for i in range(min(3, body.installments)):
        month_date = today + timedelta(days=30 * (i + 1))
        running_balance = running_balance - (avg_daily * 30) - monthly_installment
        projection.append(
            MonthImpact(
                month=month_date.strftime("%Y-%m"),
                installment_amount=monthly_installment,
                projected_free_balance=max(running_balance, Decimal("0")),
                debt_impact=0,
            )
        )

    # Recommendation logic
    impact_ratio = monthly_installment / (avg_daily * 30) if avg_daily > 0 else Decimal("0")
    if impact_ratio < Decimal("0.15"):
        recommendation = "go"
        reason = "Impacto baixo no orçamento mensal. Compra segura."
    elif impact_ratio < Decimal("0.30"):
        recommendation = "caution"
        reason = "Impacto moderado. Considere se há dívidas ativas."
    else:
        recommendation = "avoid"
        reason = "Impacto alto no orçamento. Com dívidas ativas, não recomendado."

    return SimulatorResponse(
        purchase_amount=body.amount,
        installments=body.installments,
        monthly_impact=monthly_installment,
        three_month_projection=projection,
        debt_payoff_delay_months=int(impact_ratio * body.installments),
        recommendation=recommendation,
        reason=reason,
    )
