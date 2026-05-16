from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from deps import CurrentUser, DB
from models.finance import Transaction, Wallet
from schemas.finance import (
    CategoryType,
    TransactionCreate,
    TransactionOut,
    WalletCreate,
    WalletOut,
    WalletSuggestion,
)

# Wallet suggestion rules
CATEGORY_WALLET_MAP: dict[CategoryType, str] = {
    "food": "vr",
    "transport": "vr",
    "pharma": "vr",
    "health": "cash",
    "personal": "cash",
    "debt": "inflow",
    "savings": "cash",
    "other": "cash",
}

CATEGORY_REASONS: dict[CategoryType, str] = {
    "food": "Use o VR para preservar o saldo líquido.",
    "transport": "Uber e transporte saem do VR — benefício disponível.",
    "pharma": "Farmácia e remédios têm cobertura pelo VR.",
    "health": "Gasto de saúde planejado — use o saldo líquido.",
    "personal": "Personal está no orçamento da Wallet Líquida.",
    "debt": "Use o Inflow Extra para quitar dívidas sem comprometer o mensal.",
    "savings": "Reserva sai do saldo líquido.",
    "other": "Sem sugestão específica — use a Wallet Líquida.",
}

router = APIRouter(prefix="/finance/wallets", tags=["finance"])


@router.get("", response_model=list[WalletOut])
async def list_wallets(user_id: CurrentUser, db: DB):
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == UUID(user_id)).order_by(Wallet.created_at.asc())
    )
    wallets = result.scalars().all()
    # inject computed balance
    output = []
    for w in wallets:
        balance = await _compute_balance(db, w.id)
        out = WalletOut.model_validate(w)
        out.balance = balance
        output.append(out)
    return output


@router.post("", response_model=WalletOut, status_code=status.HTTP_201_CREATED)
async def create_wallet(user_id: CurrentUser, db: DB, body: WalletCreate):
    wallet = Wallet(user_id=UUID(user_id), **body.model_dump())
    db.add(wallet)
    await db.flush()
    await db.refresh(wallet)
    out = WalletOut.model_validate(wallet)
    out.balance = Decimal("0")
    return out


@router.get("/{wallet_id}/balance")
async def get_wallet_balance(user_id: CurrentUser, db: DB, wallet_id: UUID):
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == UUID(user_id))
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    balance = await _compute_balance(db, wallet_id)
    return {"wallet_id": wallet_id, "balance": balance, "currency": wallet.currency}


@router.get("/suggest", response_model=WalletSuggestion)
async def suggest_wallet(
    user_id: CurrentUser,
    db: DB,
    category: CategoryType = Query(...),
):
    suggested_type = CATEGORY_WALLET_MAP.get(category, "cash")
    reason = CATEGORY_REASONS.get(category, "Use a Wallet Líquida.")
    return WalletSuggestion(
        category=category,
        suggested_wallet_type=suggested_type,
        reason=reason,
    )


async def _compute_balance(db: DB, wallet_id: UUID) -> Decimal:
    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.wallet_id == wallet_id
        )
    )
    return result.scalar() or Decimal("0")
