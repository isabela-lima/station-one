"""Configurações do usuário: chave da Anthropic (cifrada), modelo e uso."""

from datetime import datetime, time
from uuid import UUID

import anthropic
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from assistant_llm import MODELS, api_error_to_http, get_user_settings, resolve_model
from deps import DB, CurrentUser, Today, UserTZ
from models.assistant import AssistantUsage, UserSettings
from schemas.settings import AnthropicKeyIn, ModelOption, SettingsOut, SettingsUpdate, UsageOut
from secrets_box import encrypt

router = APIRouter(prefix="/settings", tags=["settings"])


def _out(prefs: UserSettings | None) -> SettingsOut:
    return SettingsOut(
        has_anthropic_key=bool(prefs and prefs.anthropic_key_ciphertext),
        anthropic_key_hint=f"…{prefs.anthropic_key_hint}" if prefs and prefs.anthropic_key_hint else None,
        assistant_model=resolve_model(prefs.assistant_model if prefs else None).id,
        models=[
            ModelOption(
                id=m.id,
                label=m.label,
                description=m.description,
                input_per_mtok=m.input_per_mtok,
                output_per_mtok=m.output_per_mtok,
            )
            for m in MODELS.values()
        ],
    )


async def _get_or_create(db: DB, uid: UUID) -> UserSettings:
    prefs = await get_user_settings(db, uid)
    if prefs is None:
        prefs = UserSettings(user_id=uid)
        db.add(prefs)
    return prefs


@router.get("", response_model=SettingsOut)
async def get_settings(user_id: CurrentUser, db: DB):
    return _out(await get_user_settings(db, UUID(user_id)))


@router.put("/anthropic-key", response_model=SettingsOut)
async def set_anthropic_key(user_id: CurrentUser, db: DB, body: AnthropicKeyIn):
    key = body.api_key.strip()
    if not key.startswith("sk-ant-"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Isso não parece uma chave da Anthropic (começa com sk-ant-).")

    # Confere a chave com uma chamada que não custa nada (lista de modelos)
    client = anthropic.AsyncAnthropic(api_key=key, timeout=15.0, max_retries=1)
    try:
        await client.models.list(limit=1)
    except anthropic.APIError as exc:
        raise api_error_to_http(exc)
    finally:
        await client.close()

    prefs = await _get_or_create(db, UUID(user_id))
    prefs.anthropic_key_ciphertext = encrypt(key)
    prefs.anthropic_key_hint = key[-4:]
    await db.flush()
    return _out(prefs)


@router.delete("/anthropic-key", response_model=SettingsOut)
async def delete_anthropic_key(user_id: CurrentUser, db: DB):
    prefs = await get_user_settings(db, UUID(user_id))
    if prefs:
        prefs.anthropic_key_ciphertext = None
        prefs.anthropic_key_hint = None
        await db.flush()
    return _out(prefs)


@router.patch("", response_model=SettingsOut)
async def update_settings(user_id: CurrentUser, db: DB, body: SettingsUpdate):
    if body.assistant_model not in MODELS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Modelo desconhecido.")
    prefs = await _get_or_create(db, UUID(user_id))
    prefs.assistant_model = body.assistant_model
    await db.flush()
    return _out(prefs)


@router.get("/usage", response_model=UsageOut)
async def get_usage(user_id: CurrentUser, db: DB, today: Today, tz: UserTZ):
    """Uso do assistente no mês corrente (no fuso do usuário)."""
    first = today.replace(day=1)
    start = datetime.combine(first, time.min)
    start = start.replace(tzinfo=tz) if tz else start.astimezone()
    row = (
        await db.execute(
            select(
                func.count(AssistantUsage.id),
                func.coalesce(func.sum(AssistantUsage.input_tokens), 0),
                func.coalesce(func.sum(AssistantUsage.output_tokens), 0),
                func.coalesce(func.sum(AssistantUsage.cost_usd), 0),
            ).where(AssistantUsage.user_id == UUID(user_id), AssistantUsage.created_at >= start)
        )
    ).one()
    return UsageOut(
        month=first.strftime("%Y-%m"),
        calls=row[0],
        input_tokens=row[1],
        output_tokens=row[2],
        cost_usd=row[3],
    )
