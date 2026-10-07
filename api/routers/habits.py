from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from deps import CurrentUser, DB, Today
from models.habits import Habit, HabitCompletion
from schemas.habits import HabitCreate, HabitOut

router = APIRouter(prefix="/habits", tags=["habits"])


def _calc_streak(completion_dates: set[date], today: date) -> int:
    """
    Conta dias consecutivos terminando hoje — ou ontem, se hoje ainda não foi
    feito. Assim o streak não zera à meia-noite; só quebra se um dia passar
    inteiro sem check-in (igual ao Duolingo).
    """
    current = today if today in completion_dates else today - timedelta(days=1)
    streak = 0
    while current in completion_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def _to_out(habit: Habit, completion_dates: set[date], today: date) -> HabitOut:
    return HabitOut(
        id=habit.id,
        user_id=habit.user_id,
        name=habit.name,
        emoji=habit.emoji,
        created_at=habit.created_at,
        streak=_calc_streak(completion_dates, today),
        completed_today=today in completion_dates,
    )


async def _completion_dates(
    db: DB, uid: UUID, habit_ids: list[UUID]
) -> dict[UUID, set[date]]:
    """Busca as datas de completion de vários hábitos numa query só."""
    by_habit: dict[UUID, set[date]] = defaultdict(set)
    if not habit_ids:
        return by_habit
    result = await db.execute(
        select(HabitCompletion.habit_id, HabitCompletion.date).where(
            HabitCompletion.user_id == uid, HabitCompletion.habit_id.in_(habit_ids)
        )
    )
    for habit_id, d in result.all():
        by_habit[habit_id].add(d)
    return by_habit


async def _build_habit_out(habit: Habit, uid: UUID, db: DB, today: date) -> HabitOut:
    dates = await _completion_dates(db, uid, [habit.id])
    return _to_out(habit, dates[habit.id], today)


@router.get("", response_model=list[HabitOut])
async def list_habits(user_id: CurrentUser, db: DB, today: Today):
    uid = UUID(user_id)
    result = await db.execute(
        select(Habit).where(Habit.user_id == uid).order_by(Habit.created_at.asc())
    )
    habits = result.scalars().all()
    dates = await _completion_dates(db, uid, [h.id for h in habits])
    return [_to_out(h, dates[h.id], today) for h in habits]


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
async def create_habit(user_id: CurrentUser, db: DB, today: Today, body: HabitCreate):
    uid = UUID(user_id)
    habit = Habit(user_id=uid, name=body.name, emoji=body.emoji)
    db.add(habit)
    await db.flush()
    await db.refresh(habit)
    return _to_out(habit, set(), today)


@router.post("/{habit_id}/toggle-today", response_model=HabitOut)
async def toggle_habit_today(user_id: CurrentUser, db: DB, today: Today, habit_id: UUID):
    uid = UUID(user_id)

    # Verify ownership
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == uid)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Check if already completed today
    existing = await db.execute(
        select(HabitCompletion).where(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == uid,
            HabitCompletion.date == today,
        )
    )
    completion = existing.scalar_one_or_none()

    if completion:
        # Already done today — un-toggle
        await db.delete(completion)
    else:
        # Mark as done today
        db.add(HabitCompletion(user_id=uid, habit_id=habit_id, date=today))

    await db.flush()
    return await _build_habit_out(habit, uid, db, today)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(user_id: CurrentUser, db: DB, habit_id: UUID):
    uid = UUID(user_id)
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == uid)
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    await db.delete(habit)
