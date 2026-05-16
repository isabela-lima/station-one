from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class DailyLogUpdate(BaseModel):
    content: str


class DailyLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    date: date
    content: str
    created_at: datetime
    updated_at: datetime
