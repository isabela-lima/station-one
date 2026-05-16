from datetime import date
from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select

from deps import CurrentUser, DB
from models.daily_log import DailyLog
from schemas.daily_log import DailyLogOut, DailyLogUpdate

router = APIRouter(prefix="/daily-logs", tags=["daily-logs"])


@router.get("/today", response_model=DailyLogOut)
async def get_today_log(user_id: CurrentUser, db: DB):
    """Retorna o log de hoje, criando um vazio se não existir."""
    uid = UUID(user_id)
    today = date.today()

    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == uid, DailyLog.date == today)
    )
    log = result.scalar_one_or_none()

    if not log:
        log = DailyLog(user_id=uid, date=today, content="")
        db.add(log)
        await db.flush()
        await db.refresh(log)

    return log


@router.patch("/today", response_model=DailyLogOut)
async def update_today_log(user_id: CurrentUser, db: DB, body: DailyLogUpdate):
    """Atualiza (ou cria) o log de hoje com o novo conteúdo."""
    uid = UUID(user_id)
    today = date.today()

    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == uid, DailyLog.date == today)
    )
    log = result.scalar_one_or_none()

    if log:
        log.content = body.content
    else:
        log = DailyLog(user_id=uid, date=today, content=body.content)
        db.add(log)

    await db.flush()
    await db.refresh(log)
    return log
