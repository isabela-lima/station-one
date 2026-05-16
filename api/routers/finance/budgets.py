from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import Budget, Transaction
from schemas.finance import BudgetCreate, BudgetOut

router = APIRouter(prefix="/finance/budgets", tags=["finance"])


@router.get("", response_model=list[BudgetOut])
async def list_budgets(user_id: CurrentUser, db: DB):
    """List all budgets for the current user, with spent amount for the current month."""
    result = await db.execute(
        select(Budget).where(Budget.user_id == UUID(user_id))
    )
    budgets = result.scalars().all()

    budget_outs = []
    for b in budgets:
        # Calculate spent amount for this category this month
        from datetime import date
        today = date.today()
        month_start = today.replace(day=1)

        q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == UUID(user_id),
            Transaction.category == b.category,
            Transaction.amount < 0,
            Transaction.date >= month_start,
        )
        if b.wallet_id:
            q = q.where(Transaction.wallet_id == b.wallet_id)

        spent_result = await db.execute(q)
        spent = abs(spent_result.scalar() or Decimal("0"))

        out = BudgetOut.model_validate(b)
        out.spent = spent
        budget_outs.append(out)

    return budget_outs


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(user_id: CurrentUser, db: DB, body: BudgetCreate):
    """Create a budget limit for a category (optionally scoped to a wallet)."""
    budget = Budget(user_id=UUID(user_id), **body.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    out = BudgetOut.model_validate(budget)
    out.spent = Decimal("0")
    return out


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(user_id: CurrentUser, db: DB, budget_id: UUID):
    """Delete a budget."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == UUID(user_id))
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    await db.delete(budget)
