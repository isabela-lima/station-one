from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HabitCreate(BaseModel):
    name: str
    emoji: str = "⚡"


class HabitOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    emoji: str
    streak: int
    completed_today: bool
    created_at: datetime
