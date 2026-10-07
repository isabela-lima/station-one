from decimal import Decimal

from pydantic import BaseModel, Field


class ModelOption(BaseModel):
    id: str
    label: str
    description: str
    input_per_mtok: Decimal
    output_per_mtok: Decimal


class SettingsOut(BaseModel):
    has_anthropic_key: bool
    anthropic_key_hint: str | None  # "…a1b2"; a chave em si nunca sai da API
    assistant_model: str
    models: list[ModelOption]


class AnthropicKeyIn(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)


class SettingsUpdate(BaseModel):
    assistant_model: str


class UsageOut(BaseModel):
    month: str  # "2026-10"
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
