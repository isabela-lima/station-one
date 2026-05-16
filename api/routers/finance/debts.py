from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import Debt, Transaction
from schemas.finance import DebtCreate, DebtOut, DebtPayment, DebtProjection

router = APIRouter(prefix="/finance/debts", tags=["finance"])


@router.get("", response_model=list[DebtOut])
async def list_debts(user_id: CurrentUser, db: DB):
    result = await db.execute(
        select(Debt).where(Debt.user_id == UUID(user_id)).order_by(Debt.created_at.asc())
    )
    return result.scalars().all()


@router.post("", response_model=DebtOut, status_code=status.HTTP_201_CREATED)
async def create_debt(user_id: CurrentUser, db: DB, body: DebtCreate):
    debt = Debt(user_id=UUID(user_id), **body.model_dump())
    db.add(debt)
    await db.flush()
    await db.refresh(debt)
    return debt


@router.patch("/{debt_id}/payment", response_model=DebtOut)
async def register_payment(user_id: CurrentUser, db: DB, debt_id: UUID, body: DebtPayment):
    result = await db.execute(
        select(Debt).where(Debt.id == debt_id, Debt.user_id == UUID(user_id))
    )
    debt = result.scalar_one_or_none()
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    debt.current_amount = max(Decimal("0"), debt.current_amount - body.amount)
    await db.flush()
    await db.refresh(debt)
    return debt


@router.get("/{debt_id}/projection", response_model=DebtProjection)
async def get_projection(user_id: CurrentUser, db: DB, debt_id: UUID):
    result = await db.execute(
        select(Debt).where(Debt.id == debt_id, Debt.user_id == UUID(user_id))
    )
    debt = result.scalar_one_or_none()
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    if debt.monthly_payment <= 0:
        raise HTTPException(status_code=400, detail="Monthly payment must be greater than zero")

    remaining = debt.current_amount
    months = 0
    timeline = []
    today = date.today()

    while remaining > 0 and months < 120:  # cap at 10 years
        remaining = max(Decimal("0"), remaining - debt.monthly_payment)
        months += 1
        projected_date = today + timedelta(days=30 * months)
        timeline.append({"month": projected_date.strftime("%Y-%m"), "remaining_amount": float(remaining)})

    estimated_end = today + timedelta(days=30 * months)
    return DebtProjection(
        debt_id=debt_id,
        current_amount=debt.current_amount,
        monthly_payment=debt.monthly_payment,
        estimated_end_date=estimated_end,
        months_remaining=months,
        timeline=timeline,
    )
