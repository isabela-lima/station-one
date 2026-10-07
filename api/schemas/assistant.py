"""
Schemas do assistente.

`Proposed*` é o formato que o modelo devolve (structured outputs): sem
restrições numéricas/de tamanho, que a API não suporta no schema. `*Action`
é o que o cliente manda de volta para aplicar — aqui sim tudo é validado,
porque o usuário pode ter editado a proposta.
"""

from datetime import date as Date  # o campo "date" esconderia o tipo
from decimal import Decimal
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from schemas.finance import CategoryType

# ─── Saída do modelo ──────────────────────────────────────────────────────────


class ProposedTask(BaseModel):
    type: Literal["create_task"]
    content: str
    due_date: Date | None
    goal_id: str | None
    priority: bool


class ProposedTransaction(BaseModel):
    type: Literal["create_transaction"]
    kind: Literal["expense", "income"]
    amount: float
    category: CategoryType
    description: str | None
    date: Date | None


class ProposedJournalEntry(BaseModel):
    type: Literal["add_journal_entry"]
    content: str


class ProposedCheckin(BaseModel):
    type: Literal["set_checkin"]
    mood: int | None
    energy: int | None


class CaptureResult(BaseModel):
    summary: str
    actions: list[Union[ProposedTask, ProposedTransaction, ProposedJournalEntry, ProposedCheckin]]
    question: str | None


# ─── Ações enviadas para aplicar (validadas) ─────────────────────────────────


class TaskAction(BaseModel):
    type: Literal["create_task"]
    content: str = Field(min_length=1, max_length=500)
    due_date: Date | None = None
    goal_id: UUID | None = None
    priority: bool = False


class TransactionAction(BaseModel):
    type: Literal["create_transaction"]
    kind: Literal["expense", "income"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: CategoryType
    description: str | None = Field(default=None, max_length=300)
    date: Date | None = None
    wallet_id: UUID


class JournalEntryAction(BaseModel):
    type: Literal["add_journal_entry"]
    content: str = Field(min_length=1, max_length=2000)


class CheckinAction(BaseModel):
    type: Literal["set_checkin"]
    mood: int | None = Field(default=None, ge=1, le=5)
    energy: int | None = Field(default=None, ge=1, le=5)


Action = Annotated[
    Union[TaskAction, TransactionAction, JournalEntryAction, CheckinAction],
    Field(discriminator="type"),
]

# ─── API ──────────────────────────────────────────────────────────────────────


class CaptureRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class WalletRef(BaseModel):
    id: UUID
    name: str


class CaptureResponse(BaseModel):
    summary: str
    question: str | None
    # Ações já no formato de TaskAction/... (com wallet_id sugerido); `goal_title`
    # e `wallet_name` só para exibir
    actions: list[dict]
    wallets: list[WalletRef]
    model: str
    cost_usd: Decimal


class ApplyRequest(BaseModel):
    actions: list[Action] = Field(min_length=1, max_length=20)


class ApplyResponse(BaseModel):
    created: dict[str, int]  # tipo de ação → quantas foram aplicadas
