from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ItemCreate(BaseModel):
    type: Literal["task"] = "task"
    content: str
    title: str | None = None
    completed: bool = False
    priority: bool = False
    due_date: datetime | None = None
    goal_id: UUID | None = None


class ItemUpdate(BaseModel):
    """Só os campos enviados são alterados; `goal_id: null` desvincula da missão."""

    content: str | None = None
    title: str | None = None
    completed: bool | None = None
    priority: bool | None = None
    due_date: datetime | None = None
    goal_id: UUID | None = None


class ItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    type: str
    content: str
    title: str | None
    completed: bool
    priority: bool
    due_date: datetime | None
    goal_id: UUID | None
    completed_at: datetime | None
    created_at: datetime
