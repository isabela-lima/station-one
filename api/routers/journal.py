"""
Diário de bordo: entradas curtas com hora, check-in de humor/energia e um
resumo automático do dia (tarefas concluídas, hábitos feitos, gastos).
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from deps import DB, CurrentUser, Today, UserTZ
from models.daily_log import DailyLog, LogEntry
from models.finance import Transaction
from models.habits import Habit, HabitCompletion
from models.items import Item
from schemas.journal import (
    CategorySpend,
    CheckinOut,
    CheckinUpdate,
    DaySummary,
    HabitDone,
    JournalDay,
    LogEntryCreate,
    LogEntryOut,
    Recap,
)

router = APIRouter(prefix="/journal", tags=["journal"])

MAX_HISTORY_DAYS = 60


# ─── Coleta ──────────────────────────────────────────────────────────────────


@dataclass
class _Day:
    mood: int | None = None
    energy: int | None = None
    entries: list[LogEntry] = field(default_factory=list)
    tasks_done: list[str] = field(default_factory=list)
    habits_done: list[HabitDone] = field(default_factory=list)
    spent: float = 0.0
    income: float = 0.0
    by_category: dict[str, float] = field(default_factory=lambda: defaultdict(float))


def _local_midnight(d: date, tz: Optional[ZoneInfo]) -> datetime:
    """Meia-noite do dia `d` no fuso do usuário (ou do servidor)."""
    naive = datetime.combine(d, time.min)
    return naive.replace(tzinfo=tz) if tz else naive.astimezone()


async def _collect(db: DB, uid: UUID, tz: Optional[ZoneInfo], start: date, end: date) -> dict[date, _Day]:
    """Junta tudo que aconteceu entre `start` e `end` (inclusive), por dia."""
    days: dict[date, _Day] = defaultdict(_Day)

    # Check-ins
    rows = await db.execute(
        select(DailyLog.date, DailyLog.mood, DailyLog.energy).where(
            DailyLog.user_id == uid, DailyLog.date.between(start, end)
        )
    )
    for d, mood, energy in rows.all():
        days[d].mood, days[d].energy = mood, energy

    # Entradas
    rows = await db.execute(
        select(LogEntry)
        .where(LogEntry.user_id == uid, LogEntry.date.between(start, end))
        .order_by(LogEntry.created_at.desc())
    )
    for e in rows.scalars().all():
        days[e.date].entries.append(e)

    # Tarefas concluídas (completed_at é timestamp → converte para o dia local)
    rows = await db.execute(
        select(Item.content, Item.completed_at).where(
            Item.user_id == uid,
            Item.type == "task",
            Item.completed.is_(True),
            Item.completed_at >= _local_midnight(start, tz),
            Item.completed_at < _local_midnight(end + timedelta(days=1), tz),
        )
    )
    for content, done_at in rows.all():
        local = done_at.astimezone(tz) if tz else done_at.astimezone()
        days[local.date()].tasks_done.append(content)

    # Hábitos feitos
    rows = await db.execute(
        select(HabitCompletion.date, Habit.name, Habit.emoji)
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .where(HabitCompletion.user_id == uid, HabitCompletion.date.between(start, end))
    )
    for d, name, emoji in rows.all():
        days[d].habits_done.append(HabitDone(name=name, emoji=emoji))

    # Dinheiro (amount < 0 = gasto)
    rows = await db.execute(
        select(Transaction.date, Transaction.amount, Transaction.category).where(
            Transaction.user_id == uid, Transaction.date.between(start, end)
        )
    )
    for d, amount, category in rows.all():
        value = float(amount)
        if value < 0:
            days[d].spent += -value
            days[d].by_category[category] += -value
        else:
            days[d].income += value

    return days


def _to_journal_day(d: date, day: _Day) -> JournalDay:
    top = sorted(day.by_category.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return JournalDay(
        date=d,
        mood=day.mood,
        energy=day.energy,
        entries=[LogEntryOut.model_validate(e) for e in day.entries],
        recap=Recap(
            tasks_done=day.tasks_done,
            habits_done=day.habits_done,
            spent=round(day.spent, 2),
            income=round(day.income, 2),
            top_categories=[CategorySpend(category=c, amount=round(v, 2)) for c, v in top],
        ),
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/today", response_model=JournalDay)
async def get_today(user_id: CurrentUser, db: DB, today: Today, tz: UserTZ):
    days = await _collect(db, UUID(user_id), tz, today, today)
    return _to_journal_day(today, days[today])


@router.get("/days/{day}", response_model=JournalDay)
async def get_day(user_id: CurrentUser, db: DB, tz: UserTZ, day: date):
    days = await _collect(db, UUID(user_id), tz, day, day)
    return _to_journal_day(day, days[day])


@router.get("/history", response_model=list[DaySummary])
async def get_history(
    user_id: CurrentUser,
    db: DB,
    today: Today,
    tz: UserTZ,
    before: date | None = Query(None, description="Dias anteriores a esta data (padrão: hoje)"),
    days: int = Query(14, ge=1, le=MAX_HISTORY_DAYS),
):
    """Os `days` dias anteriores a `before`, do mais recente ao mais antigo."""
    end = (before or today) - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    collected = await _collect(db, UUID(user_id), tz, start, end)
    out: list[DaySummary] = []
    for i in range(days):
        d = end - timedelta(days=i)
        day = collected.get(d, _Day())
        out.append(
            DaySummary(
                date=d,
                mood=day.mood,
                energy=day.energy,
                entries_count=len(day.entries),
                first_entry=day.entries[-1].content if day.entries else None,
                tasks_done=len(day.tasks_done),
                habits_done=len(day.habits_done),
                spent=round(day.spent, 2),
            )
        )
    return out


@router.put("/days/{day}/checkin", response_model=CheckinOut)
async def set_checkin(user_id: CurrentUser, db: DB, day: date, body: CheckinUpdate):
    uid = UUID(user_id)
    result = await db.execute(select(DailyLog).where(DailyLog.user_id == uid, DailyLog.date == day))
    log = result.scalar_one_or_none()
    if not log:
        log = DailyLog(user_id=uid, date=day, content="")
        db.add(log)
    for field_name, value in body.model_dump(exclude_unset=True).items():
        setattr(log, field_name, value)
    await db.flush()
    return CheckinOut(date=day, mood=log.mood, energy=log.energy)


@router.post("/entries", response_model=LogEntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(user_id: CurrentUser, db: DB, today: Today, body: LogEntryCreate):
    entry = LogEntry(user_id=UUID(user_id), date=today, content=body.content.strip(), url=body.url)
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(user_id: CurrentUser, db: DB, entry_id: UUID):
    result = await db.execute(
        select(LogEntry).where(LogEntry.id == entry_id, LogEntry.user_id == UUID(user_id))
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
