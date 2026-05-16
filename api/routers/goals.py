from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from deps import CurrentUser, DB
from models.goals import Goal, Milestone
from schemas.goals import GoalCreate, GoalOut, MilestoneCreate, MilestoneOut, MilestoneUpdate

router = APIRouter(tags=["goals"])

# ─── Goals ────────────────────────────────────────────────

goals_router = APIRouter(prefix="/goals")


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


# ─── Milestones ───────────────────────────────────────────

milestones_router = APIRouter(prefix="/milestones")


@milestones_router.get("", response_model=list[MilestoneOut])
async def list_milestones(user_id: CurrentUser, db: DB, goal_id: UUID | None = None):
    q = select(Milestone).where(Milestone.user_id == UUID(user_id))
    if goal_id:
        q = q.where(Milestone.goal_id == goal_id)
    result = await db.execute(q)
    return result.scalars().all()


@milestones_router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
async def create_milestone(user_id: CurrentUser, db: DB, body: MilestoneCreate):
    # verify the goal belongs to the user
    result = await db.execute(
        select(Goal).where(Goal.id == body.goal_id, Goal.user_id == UUID(user_id))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Goal not found")

    milestone = Milestone(user_id=UUID(user_id), **body.model_dump())
    db.add(milestone)
    await db.flush()
    await db.refresh(milestone)
    return milestone


@milestones_router.patch("/{milestone_id}", response_model=MilestoneOut)
async def update_milestone(user_id: CurrentUser, db: DB, milestone_id: UUID, body: MilestoneUpdate):
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == UUID(user_id))
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(milestone, field, value)
    await db.flush()
    await db.refresh(milestone)
    return milestone


@milestones_router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(user_id: CurrentUser, db: DB, milestone_id: UUID):
    result = await db.execute(
        select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == UUID(user_id))
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    await db.delete(milestone)
