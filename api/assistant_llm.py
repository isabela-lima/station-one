"""
Acesso ao Claude para o assistente: catálogo de modelos, cliente com a chave
de cada usuário, registro de uso e tradução de erros da API.

Cada pessoa usa a própria chave da Anthropic (salva cifrada em user_settings)
e escolhe o próprio modelo; o custo é dela.
"""

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import anthropic
from fastapi import HTTPException, status
from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
from deps import DB
from models.assistant import AssistantUsage, UserSettings
from secrets_box import SecretUnreadable, decrypt


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    description: str
    input_per_mtok: Decimal  # US$ por milhão de tokens
    output_per_mtok: Decimal
    supports_effort: bool  # `output_config.effort` (o Haiku 4.5 rejeita)
    # tool_choice forçado ({"type": "tool"}); os modelos 5.5 só aceitam "auto"
    supports_forced_tool: bool


# Ordem = ordem no seletor das Configurações
MODELS: dict[str, ModelInfo] = {
    m.id: m
    for m in [
        ModelInfo(
            "claude-haiku-4-5",
            "Claude Haiku 4.5",
            "Mais barato e rápido. Bom para registros simples.",
            Decimal("1"),
            Decimal("5"),
            supports_effort=False,
            supports_forced_tool=True,
        ),
        ModelInfo(
            "claude-sonnet-5-5",
            "Claude Sonnet 5.5",
            "Equilíbrio: entende pedidos mais ambíguos.",
            Decimal("2"),
            Decimal("10"),
            supports_effort=True,
            supports_forced_tool=False,
        ),
        ModelInfo(
            "claude-opus-5-5",
            "Claude Opus 5.5",
            "O mais capaz, e o mais caro.",
            Decimal("4"),
            Decimal("20"),
            supports_effort=True,
            supports_forced_tool=False,
        ),
    ]
}


def resolve_model(choice: str | None) -> ModelInfo:
    return MODELS.get(choice or "") or MODELS.get(settings.assistant_default_model) or MODELS["claude-haiku-4-5"]


def cost_usd(model: ModelInfo, input_tokens: int, output_tokens: int) -> Decimal:
    return (
        model.input_per_mtok * input_tokens + model.output_per_mtok * output_tokens
    ) / Decimal(1_000_000)


# Um cliente por chave, reaproveitado entre chamadas: mantém a conexão HTTPS com a
# Anthropic aberta (abrir uma nova a cada pedido custa ~0,5 s daqui do Brasil).
# A chave entra no dicionário só como hash; LRU para não crescer sem limite.
_CLIENTS: "OrderedDict[str, anthropic.AsyncAnthropic]" = OrderedDict()
_MAX_CLIENTS = 32


def _cached_client(api_key: str) -> anthropic.AsyncAnthropic:
    key_id = hashlib.sha256(api_key.encode()).hexdigest()
    client = _CLIENTS.get(key_id)
    if client is None:
        client = anthropic.AsyncAnthropic(api_key=api_key, timeout=60.0, max_retries=2)
        _CLIENTS[key_id] = client
        if len(_CLIENTS) > _MAX_CLIENTS:
            _CLIENTS.popitem(last=False)  # o mais antigo; o GC fecha as conexões
    else:
        _CLIENTS.move_to_end(key_id)
    return client


async def get_user_settings(db: DB, uid: UUID) -> UserSettings | None:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == uid))
    return result.scalar_one_or_none()


async def client_for(db: DB, uid: UUID) -> tuple[anthropic.AsyncAnthropic, ModelInfo]:
    """Cliente com a chave do usuário e o modelo escolhido por ele."""
    prefs = await get_user_settings(db, uid)
    if not prefs or not prefs.anthropic_key_ciphertext:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configure sua chave da API da Anthropic em Configurações para usar o assistente.",
        )
    try:
        api_key = decrypt(prefs.anthropic_key_ciphertext)
    except SecretUnreadable:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível ler sua chave salva. Cole a chave de novo em Configurações.",
        )
    # Sem leitura de ANTHROPIC_API_KEY do ambiente: sempre a chave da pessoa
    return _cached_client(api_key), resolve_model(prefs.assistant_model)


def usage_tokens(usage) -> tuple[int, int]:
    """(entrada, saída) contando também os tokens de cache."""
    input_tokens = (
        (usage.input_tokens or 0)
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
        + (getattr(usage, "cache_read_input_tokens", 0) or 0)
    )
    return input_tokens, usage.output_tokens or 0


async def save_usage(uid: UUID, kind: str, model: ModelInfo, input_tokens: int, output_tokens: int) -> None:
    """
    Grava o uso numa sessão própria. Roda como tarefa de fundo, depois que a
    resposta já foi enviada — e por isso também não é desfeito se a requisição
    falhar depois da chamada à IA (a chamada já foi cobrada).
    """
    async with AsyncSessionLocal() as session:
        session.add(
            AssistantUsage(
                user_id=uid,
                kind=kind,
                model=model.id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd(model, input_tokens, output_tokens),
            )
        )
        await session.commit()


def api_error_to_http(exc: anthropic.APIError) -> HTTPException:
    """Erros da Anthropic viram mensagens que fazem sentido para o usuário."""
    if isinstance(exc, anthropic.AuthenticationError):
        return HTTPException(400, "Sua chave da API foi recusada pela Anthropic. Confira em Configurações.")
    if isinstance(exc, anthropic.PermissionDeniedError):
        return HTTPException(400, "Sua chave não tem permissão para usar este modelo.")
    if isinstance(exc, anthropic.NotFoundError):
        return HTTPException(400, "Modelo indisponível para a sua conta. Escolha outro em Configurações.")
    if isinstance(exc, anthropic.RateLimitError):
        return HTTPException(429, "Limite de uso da sua conta Anthropic atingido. Tente de novo em instantes.")
    if isinstance(exc, anthropic.BadRequestError):
        msg = str(getattr(exc, "message", "") or "")
        if "credit" in msg.lower() or "billing" in msg.lower():
            return HTTPException(402, "Sua conta Anthropic está sem créditos.")
        return HTTPException(502, "O assistente não entendeu o pedido. Tente reformular.")
    if isinstance(exc, anthropic.APIConnectionError):
        return HTTPException(502, "Não foi possível falar com a Anthropic. Verifique a conexão.")
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
        return HTTPException(502, "A Anthropic está instável agora. Tente de novo em instantes.")
    return HTTPException(502, "Erro ao falar com o assistente.")
