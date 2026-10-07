from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from deps import CurrentUser, DB
from models.goals import Goal
from schemas.goals import GoalCreate, GoalOut

# Missões. As tarefas de uma missão são items com goal_id (os antigos
# "marcos" foram migrados para isso — ver migração tasks_missions_journal).
goals_router = APIRouter(prefix="/goals", tags=["goals"])


@goals_router.get("", response_model=list[GoalOut])
async def list_goals(user_id: CurrentUser, db: DB):
    result = await db.execute(
        select(Goal).where(Goal.user_id == UUID(user_id)).order_by(Goal.created_at.asc())
    )
    return result.scalars().all()


@goals_router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(user_id: CurrentUser, db: DB, body: GoalCreate):
    goal = Goal(user_id=UUID(user_id), **body.model_dump())
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return goal


@goals_router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(user_id: CurrentUser, db: DB, goal_id: UUID):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == UUID(user_id))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)
