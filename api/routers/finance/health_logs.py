from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import HealthLog
from schemas.finance import HealthLogCreate, HealthLogOut, PersonalROI

router = APIRouter(prefix="/finance/health-logs", tags=["finance"])

PERSONAL_MONTHLY_COST = Decimal("500.00")
TARGET_TRAININGS_PER_MONTH = 15


@router.get("", response_model=list[HealthLogOut])
async def list_health_logs(
    user_id: CurrentUser,
    db: DB,
    month: str | None = Query(None, description="Format: YYYY-MM"),
):
    uid = UUID(user_id)
    q = select(HealthLog).where(HealthLog.user_id == uid).order_by(HealthLog.date.desc())

    if month:
        try:
            year, m = int(month.split("-")[0]), int(month.split("-")[1])
            start = date(year, m, 1)
            end = (start + timedelta(days=32)).replace(day=1)
            q = q.where(HealthLog.date >= start, HealthLog.date < end)
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=HealthLogOut, status_code=status.HTTP_201_CREATED)
async def log_health(user_id: CurrentUser, db: DB, body: HealthLogCreate):
    uid = UUID(user_id)
    log_date = body.date or date.today()

    # Check for existing log on same date (upsert behavior)
    existing = await db.execute(
        select(HealthLog).where(HealthLog.user_id == uid, HealthLog.date == log_date)
    )
    log = existing.scalar_one_or_none()

    if log:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(log, field, value)
    else:
        data = body.model_dump()
        data["date"] = log_date
        log = HealthLog(user_id=uid, **data)
        db.add(log)

    await db.flush()
    await db.refresh(log)
    return log


@router.get("/roi", response_model=PersonalROI)
async def get_personal_roi(user_id: CurrentUser, db: DB):
    uid = UUID(user_id)
    today = date.today()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1)

    result = await db.execute(
        select(func.count(HealthLog.id)).where(
            HealthLog.user_id == uid,
            HealthLog.date >= start_of_month,
            HealthLog.date < end_of_month,
            HealthLog.trained == True,
        )
    )
    trainings = result.scalar() or 0

    cost_per_training = (
        PERSONAL_MONTHLY_COST / trainings if trainings > 0 else None
    )
    target_cost = PERSONAL_MONTHLY_COST / TARGET_TRAININGS_PER_MONTH

    if trainings >= TARGET_TRAININGS_PER_MONTH:
        status_val = "validated"
        message = f"🚀 Investimento validado! {trainings} treinos — R${cost_per_training:.2f}/treino."
    elif trainings >= TARGET_TRAININGS_PER_MONTH * 0.6:
        remaining = TARGET_TRAININGS_PER_MONTH - trainings
        status_val = "partial"
        message = f"🟡 Parcial — {remaining} treinos para validar o investimento."
    else:
        status_val = "at_risk"
        message = f"🔴 Em risco — apenas {trainings} treinos este mês. Custo elevado."

    return PersonalROI(
        monthly_cost=PERSONAL_MONTHLY_COST,
        trainings_this_month=trainings,
        cost_per_training=cost_per_training,
        target_trainings=TARGET_TRAININGS_PER_MONTH,
        target_cost_per_training=target_cost,
        status=status_val,
        message=message,
    )
