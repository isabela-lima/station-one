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
