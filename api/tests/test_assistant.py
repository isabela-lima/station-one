import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

import secrets_box
from assistant_llm import MODELS, cost_usd, resolve_model
from routers.assistant import _context, _pick_wallet, build_actions
from schemas.assistant import (
    ApplyRequest,
    CaptureResult,
    ProposedJournalEntry,
    ProposedTask,
    ProposedTransaction,
)


def wallet(type_: str, name: str):
    return SimpleNamespace(id=uuid.uuid4(), type=type_, name=name)


# ─── Cifra das chaves ────────────────────────────────────────────────────────


def test_secret_round_trip(monkeypatch):
    monkeypatch.setattr(secrets_box.settings, "app_encryption_key", Fernet.generate_key().decode())
    secrets_box._fernet.cache_clear()
    token = secrets_box.encrypt("sk-ant-segredo")
    assert "sk-ant" not in token
    assert secrets_box.decrypt(token) == "sk-ant-segredo"


def test_secret_from_another_server_key_is_unreadable(monkeypatch):
    monkeypatch.setattr(secrets_box.settings, "app_encryption_key", Fernet.generate_key().decode())
    secrets_box._fernet.cache_clear()
    token = secrets_box.encrypt("sk-ant-segredo")
    monkeypatch.setattr(secrets_box.settings, "app_encryption_key", Fernet.generate_key().decode())
    secrets_box._fernet.cache_clear()
    with pytest.raises(secrets_box.SecretUnreadable):
        secrets_box.decrypt(token)
    secrets_box._fernet.cache_clear()


# ─── Modelos e custo ─────────────────────────────────────────────────────────


def test_unknown_or_missing_model_falls_back_to_default():
    assert resolve_model(None).id == "claude-haiku-4-5"
    assert resolve_model("modelo-que-nao-existe").id == "claude-haiku-4-5"
    assert resolve_model("claude-opus-5-5").id == "claude-opus-5-5"


def test_cost_uses_per_million_prices():
    haiku = MODELS["claude-haiku-4-5"]  # US$ 1 entrada / 5 saída por milhão
    assert cost_usd(haiku, 3000, 400) == Decimal("0.005")


# ─── Contexto e pós-processamento ────────────────────────────────────────────


def test_context_has_weekday_and_goals():
    goal = SimpleNamespace(id=uuid.uuid4(), title="Finalizar SIAFIC")
    text = _context(date(2026, 10, 7), [goal])
    assert "2026-10-07 (quarta)" in text and "2026-10-08" in text
    assert f"{goal.id}: Finalizar SIAFIC" in text


def test_wallet_follows_category_rule():
    vr, cash, inflow = wallet("vr", "VR"), wallet("cash", "Conta"), wallet("inflow", "Extra")
    assert _pick_wallet("food", "expense", [cash, vr, inflow]) is vr
    assert _pick_wallet("health", "expense", [vr, cash]) is cash
    assert _pick_wallet("other", "income", [cash, inflow]) is inflow
    assert _pick_wallet("food", "expense", [cash]) is cash  # sem VR, cai na conta
    assert _pick_wallet("food", "expense", []) is None


def test_build_actions_drops_invented_goal_and_suggests_wallet():
    goal = SimpleNamespace(id=uuid.uuid4(), title="Estudos")
    vr = wallet("vr", "VR")
    result = CaptureResult(
        summary="ok",
        question=None,
        actions=[
            ProposedTask(type="create_task", content="Revisar anki", due_date=date(2026, 10, 9),
                         goal_id=str(goal.id), priority=False),
            ProposedTask(type="create_task", content="Outra", due_date=None,
                         goal_id="id-inventado", priority=True),
            ProposedTransaction(type="create_transaction", kind="expense", amount=45.9,
                                category="food", description="Mercado", date=None),
            ProposedJournalEntry(type="add_journal_entry", content="Dia bom"),
        ],
    )
    a = build_actions(result, [goal], [vr])
    assert a[0]["goal_id"] == str(goal.id) and a[0]["goal_title"] == "Estudos"
    assert a[0]["due_date"] == "2026-10-09"
    assert a[1]["goal_id"] is None and a[1]["goal_title"] is None
    assert a[2]["wallet_id"] == str(vr.id) and a[2]["wallet_name"] == "VR"
    assert a[3] == {"type": "add_journal_entry", "content": "Dia bom"}


# ─── Validação do que volta para aplicar ─────────────────────────────────────


def test_apply_validates_each_action():
    ok = ApplyRequest.model_validate({"actions": [
        {"type": "create_task", "content": "x", "due_date": "2026-10-10"},
        {"type": "set_checkin", "mood": 4, "energy": None},
    ]})
    assert [a.type for a in ok.actions] == ["create_task", "set_checkin"]


@pytest.mark.parametrize("bad", [
    {"type": "create_task", "content": ""},
    {"type": "set_checkin", "mood": 6},
    {"type": "create_transaction", "kind": "expense", "amount": "-10", "category": "food",
     "wallet_id": str(uuid.uuid4())},
    {"type": "create_transaction", "kind": "expense", "amount": "10", "category": "food"},  # sem carteira
    {"type": "delete_everything"},
])
def test_apply_rejects_invalid_actions(bad):
    with pytest.raises(ValidationError):
        ApplyRequest.model_validate({"actions": [bad]})


def test_apply_requires_at_least_one_action():
    with pytest.raises(ValidationError):
        ApplyRequest.model_validate({"actions": []})


# ─── Resposta da ferramenta (caminho rápido) ─────────────────────────────────

from routers.assistant import CAPTURE_TOOL, parse_tool_input  # noqa: E402


def test_tool_input_valid():
    r = parse_tool_input({
        "summary": "ok", "question": None,
        "actions": [{"type": "create_task", "content": "Pagar luz", "due_date": "2026-10-08",
                     "goal_id": None, "priority": False}],
    })
    assert r is not None and r.actions[0].content == "Pagar luz"


def test_tool_input_with_actions_as_json_text():
    # O modelo às vezes manda a lista como texto JSON
    r = parse_tool_input({
        "summary": "ok", "question": None,
        "actions": '[{"type": "add_journal_entry", "content": "Dia bom"}]',
    })
    assert r is not None and r.actions[0].type == "add_journal_entry"


def test_tool_input_broken_goes_to_fallback():
    # Caso real ("paguei o uber"): placeholder fora do JSON → None → usa o formato travado
    assert parse_tool_input({
        "summary": "Registrou um gasto com Uber.", "question": "Qual foi o valor?",
        "actions": '[{"type": "create_transaction", "kind": "expense", "amount": <UNKNOWN>}]',
    }) is None
    assert parse_tool_input({"summary": "x", "question": None, "actions": [{"type": "hack"}]}) is None
    assert parse_tool_input("not a dict") is None


def test_capture_tool_schema_describes_all_action_types():
    text = str(CAPTURE_TOOL["input_schema"])
    for t in ["create_task", "create_transaction", "add_journal_entry", "set_checkin"]:
        assert t in text
