from datetime import date as Date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

WalletType = Literal["cash", "vr", "inflow"]
CategoryType = Literal["food", "transport", "health", "personal", "debt", "savings", "pharma", "other"]

# ─── Wallets ────────────────────────────────────────────

class WalletCreate(BaseModel):
    name: str
    type: WalletType
    emoji: str = "💵"
    currency: str = "BRL"


class WalletOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    type: str
    emoji: str
    currency: str
    created_at: datetime
    balance: Decimal = Decimal("0")  # computed field, injected by router


class WalletBalance(BaseModel):
    wallet_id: UUID
    balance: Decimal
    currency: str


# ─── Transactions ────────────────────────────────────────

class TransactionCreate(BaseModel):
    wallet_id: UUID
    amount: Decimal  # positive = income, negative = expense
    currency: str = "BRL"
    category: CategoryType
    description: str | None = None
    date: Date | None = None
    is_recurring: bool = False
    installment_num: int | None = None
    total_installments: int | None = None


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    wallet_id: UUID | None
    amount: Decimal
    currency: str
    category: str
    description: str | None
    suggested_wallet_id: UUID | None
    date: Date
    is_recurring: bool
    installment_num: int | None
    total_installments: int | None
    created_at: datetime


class WalletSuggestion(BaseModel):
    category: CategoryType
    suggested_wallet_type: WalletType
    reason: str


# ─── Budgets ─────────────────────────────────────────────

class BudgetCreate(BaseModel):
    wallet_id: UUID | None = None
    category: CategoryType
    limit_amount: Decimal
    currency: str = "BRL"


class BudgetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    wallet_id: UUID | None
    category: str
    limit_amount: Decimal
    currency: str
    period: str
    spent: Decimal = Decimal("0")  # injected by router


# ─── Debts ───────────────────────────────────────────────

class DebtCreate(BaseModel):
    name: str
    original_amount: Decimal
    current_amount: Decimal
    monthly_payment: Decimal
    currency: str = "BRL"
    start_date: Date


class DebtPayment(BaseModel):
    amount: Decimal


class DebtProjection(BaseModel):
    debt_id: UUID
    current_amount: Decimal
    monthly_payment: Decimal
    estimated_end_date: Date
    months_remaining: int
    timeline: list[dict]  # [{month, remaining_amount}]


class DebtOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    original_amount: Decimal
    current_amount: Decimal
    monthly_payment: Decimal
    currency: str
    start_date: Date
    created_at: datetime


# ─── Health Logs ─────────────────────────────────────────

class HealthLogCreate(BaseModel):
    date: Date | None = None
    trained: bool = False
    hrv_score: int | None = None      # futuro: Apple Watch
    energy_level: int | None = None   # 1-5
    notes: str | None = None


class HealthLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    date: Date
    trained: bool
    hrv_score: int | None
    energy_level: int | None
    notes: str | None
    created_at: datetime


class PersonalROI(BaseModel):
    monthly_cost: Decimal
    trainings_this_month: int
    cost_per_training: Decimal | None
    target_trainings: int
    target_cost_per_training: Decimal
    status: Literal["validated", "partial", "at_risk"]
    message: str


# ─── Finance Overview ─────────────────────────────────────

class AutonomyIndicator(BaseModel):
    days_of_runway: float
    avg_daily_expense: Decimal
    free_balance: Decimal
    currency: str


class FinanceOverview(BaseModel):
    wallets: list[WalletOut]
    total_debt: Decimal
    autonomy: AutonomyIndicator
    alerts: list[str]


# ─── Simulator ───────────────────────────────────────────

class SimulatorRequest(BaseModel):
    amount: Decimal
    installments: int = 1
    currency: str = "BRL"


class MonthImpact(BaseModel):
    month: str  # "2025-05"
    installment_amount: Decimal
    projected_free_balance: Decimal
    debt_impact: int  # extra months added to debt payoff


class SimulatorResponse(BaseModel):
    purchase_amount: Decimal
    installments: int
    monthly_impact: Decimal
    three_month_projection: list[MonthImpact]
    debt_payoff_delay_months: int
    recommendation: Literal["go", "caution", "avoid"]
    reason: str
