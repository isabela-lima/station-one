from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LogEntryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    url: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def only_http_urls(cls, v: str | None) -> str | None:
        # O frontend renderiza como <a href>: nada de javascript:, data: etc.
        if v is not None and not v.lower().startswith(("http://", "https://")):
            raise ValueError("url deve começar com http:// ou https://")
        return v


class LogEntryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    date: date
    content: str
    url: str | None
    created_at: datetime


class CheckinUpdate(BaseModel):
    """Só os campos enviados mudam; null limpa."""

    mood: int | None = Field(default=None, ge=1, le=5)
    energy: int | None = Field(default=None, ge=1, le=5)


class CheckinOut(BaseModel):
    date: date
    mood: int | None
    energy: int | None


class HabitDone(BaseModel):
    name: str
    emoji: str


class CategorySpend(BaseModel):
    category: str
    amount: float


class Recap(BaseModel):
    """O que aconteceu no dia, montado a partir do resto do app."""

    tasks_done: list[str]
    habits_done: list[HabitDone]
    spent: float
    income: float
    top_categories: list[CategorySpend]


class JournalDay(BaseModel):
    date: date
    mood: int | None
    energy: int | None
    entries: list[LogEntryOut]
    recap: Recap


class DaySummary(BaseModel):
    """Versão compacta de um dia para o histórico."""

    date: date
    mood: int | None
    energy: int | None
    entries_count: int
    first_entry: str | None
    tasks_done: int
    habits_done: int
    spent: float
