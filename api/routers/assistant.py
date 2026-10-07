"""
Assistente — captura em linguagem natural.

POST /assistant/capture  interpreta o texto e devolve *propostas* (não grava nada)
POST /assistant/apply    grava as ações que o usuário confirmou (tudo ou nada)
"""

import asyncio
import json
import logging
import re
import time
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

import anthropic
import pydantic
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy import select

from assistant_llm import ModelInfo, api_error_to_http, client_for, cost_usd, save_usage, usage_tokens
from database import AsyncSessionLocal
from deps import DB, CurrentUser, Today
from models.daily_log import DailyLog, LogEntry
from models.finance import Transaction, Wallet
from models.goals import Goal
from models.items import Item
from routers.finance.wallets import CATEGORY_WALLET_MAP
from schemas.assistant import (
    ApplyRequest,
    ApplyResponse,
    CaptureRequest,
    CaptureResponse,
    CaptureResult,
    CheckinAction,
    JournalEntryAction,
    ProposedTransaction,
    TaskAction,
    TransactionAction,
    WalletRef,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])
log = logging.getLogger("station_one.assistant")


class _Timer:
    """Mede etapas de uma requisição: `with t("llm"): ...` → log com ms por etapa."""

    def __init__(self) -> None:
        self.start = time.perf_counter()
        self.marks: dict[str, float] = {}

    @contextmanager
    def __call__(self, name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.marks[name] = (time.perf_counter() - t0) * 1000

    def summary(self) -> str:
        parts = [f"{k}={v:.0f}ms" for k, v in self.marks.items()]
        parts.append(f"total={(time.perf_counter() - self.start) * 1000:.0f}ms")
        return " ".join(parts)

WEEKDAYS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

# Estável entre chamadas (o contexto do dia vai na mensagem do usuário)
SYSTEM_PROMPT = """\
Você é o assistente do Station One, um app pessoal de produtividade em português.
A pessoa escreve o que quer registrar, do jeito que falaria. Transforme isso em ações:

- create_task: algo a fazer. `content` curto, no imperativo ("Pagar fatura do Nubank").
  `due_date` só se ela indicar quando (resolva "amanhã", "sexta", "dia 15" a partir de hoje;
  "sexta" = a próxima sexta, e se hoje for sexta, hoje). `goal_id` só se a tarefa claramente
  pertencer a uma das missões listadas. `priority` true só se ela disser que é importante/urgente.
- create_transaction: dinheiro que entrou (income) ou saiu (expense). `amount` sempre positivo,
  em reais. `category` entre: food (comida, mercado, restaurante, ifood), transport (uber,
  ônibus, gasolina), health (consulta, exame), pharma (farmácia, remédio), personal (roupas,
  lazer, assinaturas), debt (pagamento de dívida/fatura atrasada), savings (guardar/investir),
  other. `date` só se não for hoje.
- add_journal_entry: um acontecimento, ideia, reflexão ou link para guardar no diário.
  Mantenha as palavras da pessoa; não invente nada.
- set_checkin: quando ela disser como está se sentindo. mood (humor) e energy de 1 a 5
  (1 péssimo/esgotada, 3 ok, 5 ótimo/muita energia); null no que ela não mencionou.

Regras:
- Um texto pode virar várias ações. Não crie ações que ela não pediu.
- Nunca invente valores, datas ou missões. Se algo essencial faltar (ex.: valor de um gasto),
  não crie a ação e pergunte em `question`; senão, `question` = null.
- `summary`: uma frase curta em português dizendo o que você entendeu.
"""


# Caminho principal: o modelo "chama" esta ferramenta e a API entrega o JSON já
# separado. Medimos ~1,7 s contra 2,4–4,3 s do formato travado (structured outputs),
# que fica como reserva quando a resposta da ferramenta não passa na validação.
CAPTURE_TOOL = {
    "name": "registrar",
    "description": "Registra no Station One o que a pessoa escreveu, como uma lista de ações.",
    "input_schema": TypeAdapter(CaptureResult).json_schema(),
}


def parse_tool_input(data: object) -> CaptureResult | None:
    """Valida a entrada da ferramenta. O modelo às vezes manda `actions` como texto JSON."""
    if isinstance(data, dict) and isinstance(data.get("actions"), str):
        try:
            data = {**data, "actions": json.loads(data["actions"])}
        except json.JSONDecodeError:
            return None
    try:
        return CaptureResult.model_validate(data)
    except pydantic.ValidationError:
        return None


def _context(today, goals: list[Goal]) -> str:
    lines = [
        f"Hoje: {today.isoformat()} ({WEEKDAYS[today.weekday()]}).",
        f"Amanhã: {(today + timedelta(days=1)).isoformat()}.",
    ]
    if goals:
        lines.append("Missões (id: título):")
        lines += [f"- {g.id}: {g.title}" for g in goals]
    else:
        lines.append("Missões: nenhuma.")
    return "\n".join(lines)


def _pick_wallet(category: str, kind: str, wallets: list[Wallet]) -> Wallet | None:
    """Mesma regra da sugestão de carteira do app (categoria → tipo de carteira)."""
    if not wallets:
        return None
    wanted = "inflow" if kind == "income" else CATEGORY_WALLET_MAP.get(category, "cash")
    return next((w for w in wallets if w.type == wanted), None) or next(
        (w for w in wallets if w.type == "cash"), wallets[0]
    )


def build_actions(result: CaptureResult, goals: list[Goal], wallets: list[Wallet]) -> list[dict]:
    """Propostas do modelo → ações para o cliente revisar (sem gravar nada)."""
    goal_titles = {str(g.id): g.title for g in goals}
    actions: list[dict] = []
    for a in result.actions:
        data = json.loads(a.model_dump_json())
        if a.type == "create_task":
            # Missão inventada pelo modelo é descartada, não aplicada
            if data["goal_id"] not in goal_titles:
                data["goal_id"] = None
            data["goal_title"] = goal_titles.get(data["goal_id"] or "")
        elif isinstance(a, ProposedTransaction):
            wallet = _pick_wallet(a.category, a.kind, wallets)
            data["wallet_id"] = str(wallet.id) if wallet else None
            data["wallet_name"] = wallet.name if wallet else None
        actions.append(data)
    return actions


async def _load_client(uid: UUID):
    async with AsyncSessionLocal() as session:
        return await client_for(session, uid)


async def _load_context(uid: UUID) -> tuple[list[Goal], list[Wallet]]:
    async with AsyncSessionLocal() as session:
        goals = (
            await session.execute(select(Goal).where(Goal.user_id == uid).order_by(Goal.created_at))
        ).scalars().all()
        wallets = (await session.execute(select(Wallet).where(Wallet.user_id == uid))).scalars().all()
    return list(goals), list(wallets)


def _charge(background: BackgroundTasks, uid: UUID, model: ModelInfo, spent: list[tuple[int, int]]) -> Decimal:
    """Agenda a gravação do uso de cada chamada feita e devolve o custo total."""
    total = Decimal(0)
    for input_tokens, output_tokens in spent:
        total += cost_usd(model, input_tokens, output_tokens)
        background.add_task(save_usage, uid, "capture", model, input_tokens, output_tokens)
    return total


async def _charge_now(uid: UUID, model: ModelInfo, spent: list[tuple[int, int]]) -> None:
    """Nos caminhos de erro: o FastAPI não roda tarefas de fundo quando a rota falha."""
    for input_tokens, output_tokens in spent:
        await save_usage(uid, "capture", model, input_tokens, output_tokens)


@router.post("/capture", response_model=CaptureResponse)
async def capture(user_id: CurrentUser, today: Today, body: CaptureRequest, background: BackgroundTasks):
    uid = UUID(user_id)
    t = _Timer()
    # Configurações e contexto em paralelo, cada um na sua sessão (cada ida ao banco
    # custa ~140 ms). A captura não grava nada além do uso, que vai em segundo plano.
    with t("db"):
        (client, model), (goals, wallets) = await asyncio.gather(_load_client(uid), _load_context(uid))

    messages = [
        {"role": "user", "content": f"{_context(today, goals)}\n\nTexto da pessoa:\n{body.text}"}
    ]
    extra = {"output_config": {"effort": "low"}} if model.supports_effort else {}
    spent: list[tuple[int, int]] = []
    result: CaptureResult | None = None
    refused = False
    try:
        # 1) Ferramenta (rápido)
        with t("llm"):
            tool_choice = (
                {"type": "tool", "name": CAPTURE_TOOL["name"]}
                if model.supports_forced_tool
                else {"type": "auto"}
            )
            first = await client.messages.create(
                model=model.id,
                max_tokens=2048,
                system=SYSTEM_PROMPT + "\nSempre responda chamando a ferramenta `registrar`.",
                tools=[CAPTURE_TOOL],
                tool_choice=tool_choice,
                messages=messages,
                **extra,
            )
        spent.append(usage_tokens(first.usage))
        refused = first.stop_reason == "refusal"
        block = next((b for b in first.content if b.type == "tool_use"), None)
        if block is not None:
            result = parse_tool_input(block.input)

        # 2) Reserva: formato travado, sempre válido (mais lento, só quando necessário)
        if result is None and not refused:
            with t("llm_fallback"):
                second = await client.messages.parse(
                    model=model.id,
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    output_format=CaptureResult,
                    **extra,
                )
            spent.append(usage_tokens(second.usage))
            refused = second.stop_reason == "refusal"
            result = second.parsed_output
    except anthropic.APIError as exc:
        await _charge_now(uid, model, spent)
        raise api_error_to_http(exc)
    except pydantic.ValidationError:
        await _charge_now(uid, model, spent)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "O assistente devolveu algo inesperado. Tente de novo.")

    # As chamadas já custaram: o uso é gravado depois que a resposta sair
    cost = _charge(background, uid, model, spent)
    log.info(
        "capture %s calls=%s in=%s out=%s %s",
        model.id,
        len(spent),
        sum(i for i, _ in spent),
        sum(o for _, o in spent),
        t.summary(),
    )

    if refused or result is None:
        problem = (
            "O assistente não pôde processar esse texto."
            if refused
            else "A resposta veio incompleta. Tente um texto menor."
        )
        return CaptureResponse(
            summary="", question=problem, actions=[], wallets=[], model=model.id, cost_usd=cost
        )

    return CaptureResponse(
        summary=result.summary,
        question=result.question,
        actions=build_actions(result, goals, wallets),
        wallets=[WalletRef(id=w.id, name=w.name) for w in wallets],
        model=model.id,
        cost_usd=cost,
    )


@router.post("/apply", response_model=ApplyResponse)
async def apply(user_id: CurrentUser, db: DB, today: Today, body: ApplyRequest):
    """Grava as ações confirmadas. Tudo numa transação: se uma falhar, nada é gravado."""
    uid = UUID(user_id)
    created: dict[str, int] = {}

    goal_ids = {g for (g,) in (await db.execute(select(Goal.id).where(Goal.user_id == uid))).all()}
    wallet_ids = {w for (w,) in (await db.execute(select(Wallet.id).where(Wallet.user_id == uid))).all()}

    for action in body.actions:
        if isinstance(action, TaskAction):
            if action.goal_id and action.goal_id not in goal_ids:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Missão não encontrada.")
            db.add(
                Item(
                    user_id=uid,
                    type="task",
                    content=action.content.strip(),
                    due_date=action.due_date,
                    goal_id=action.goal_id,
                    priority=action.priority,
                    completed=False,
                )
            )
        elif isinstance(action, TransactionAction):
            if action.wallet_id not in wallet_ids:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Carteira não encontrada.")
            amount = action.amount if action.kind == "income" else -action.amount
            db.add(
                Transaction(
                    user_id=uid,
                    wallet_id=action.wallet_id,
                    amount=Decimal(amount),
                    currency="BRL",
                    category=action.category,
                    description=action.description,
                    date=action.date or today,
                    is_recurring=False,
                )
            )
        elif isinstance(action, JournalEntryAction):
            content = action.content.strip()
            match = URL_RE.search(content)
            db.add(LogEntry(user_id=uid, date=today, content=content, url=match.group(0) if match else None))
        elif isinstance(action, CheckinAction):
            log = (
                await db.execute(select(DailyLog).where(DailyLog.user_id == uid, DailyLog.date == today))
            ).scalar_one_or_none()
            if log is None:
                log = DailyLog(user_id=uid, date=today)
                db.add(log)
            if action.mood is not None:
                log.mood = action.mood
            if action.energy is not None:
                log.energy = action.energy
        created[action.type] = created.get(action.type, 0) + 1

    await db.flush()  # erros de banco aparecem aqui e o get_db faz rollback de tudo
    return ApplyResponse(created=created)
