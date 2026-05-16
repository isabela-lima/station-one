from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from deps import CurrentUser, DB
from models.habits import Habit, HabitCompletion
from schemas.habits import HabitCreate, HabitOut

router = APIRouter(prefix="/habits", tags=["habits"])


def _calc_streak(completion_dates: list[date]) -> int:
    """Conta quantos dias consecutivos a partir de hoje têm completion."""
    if not completion_dates:
        return 0
    dates_set = set(completion_dates)
    streak = 0
    current = date.today()
    while current in dates_set:
        streak += 1
        current -= timedelta(days=1)
    return streak


async def _build_habit_out(habit: Habit, uid: UUID, db: DB) -> HabitOut:
    """Calcula streak e completed_today e retorna HabitOut."""
    result = await db.execute(
        select(HabitCompletion.date)
        .where(HabitCompletion.habit_id == habit.id, HabitCompletion.user_id == uid)
        .order_by(HabitCompletion.date.desc())
    )
    completion_dates: list[date] = list(result.scalars().all())
    today = date.today()
    return HabitOut(
        id=habit.id,
        user_id=habit.user_id,
        name=habit.name,
        emoji=habit.emoji,
        created_at=habit.created_at,
        streak=_calc_streak(completion_dates),
        completed_today=today in completion_dates,
    )


@router.get("", response_model=list[HabitOut])
async def list_habits(user_id: CurrentUser, db: DB):
    uid = UUID(user_id)
    result = await db.execute(
        select(Habit).where(Habit.user_id == uid).order_by(Habit.created_at.asc())
    )
    habits = result.scalars().all()
    return [await _build_habit_out(h, uid, db) for h in habits]


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
async def create_habit(user_id: CurrentUser, db: DB, body: HabitCreate):
    uid = UUID(user_id)
    habit = Habit(user_id=uid, name=body.name, emoji=body.emoji)
    db.add(habit)
    await db.flush()
    await db.refresh(habit)
    return await _build_habit_out(habit, uid, db)


@router.post("/{habit_id}/toggle-today", response_model=HabitOut)
async def toggle_habit_today(user_id: CurrentUser, db: DB, habit_id: UUID):
    uid = UUID(user_id)
    today = date.today()

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
    return await _build_habit_out(habit, uid, db)


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
