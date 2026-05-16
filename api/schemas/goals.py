from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GoalCreate(BaseModel):
    title: str


class GoalOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime


class MilestoneCreate(BaseModel):
    goal_id: UUID
    title: str
    completed: bool = False


class MilestoneUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


class MilestoneOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    goal_id: UUID
    title: str
    completed: bool
    created_at: datetime
