"""
FastAPI dependencies — JWT authentication via Supabase.

Strategy:
  • Inspect the JWT header's `alg` field.
  • RS256 / ES256  → verify with Supabase JWKS (new projects, asymmetric keys).
  • HS256          → verify with the static `supabase_jwt_secret` (legacy projects).

JWKS are fetched lazily and cached for 1 hour. On key-rotation, a single retry
is performed with freshly fetched keys before returning 401.
"""

import time
from datetime import date, datetime
from typing import Annotated, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db

security = HTTPBearer()

# ─── JWKS cache ──────────────────────────────────────────────────────────────

_jwks_cache: Optional[dict] = None
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600  # seconds — refresh public keys every hour


def _jwks_url() -> str:
    return f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


def _fetch_jwks() -> dict:
    """Synchronously fetch JWKS from Supabase and update the module-level cache."""
    global _jwks_cache, _jwks_fetched_at
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(_jwks_url())
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = time.monotonic()
        return _jwks_cache


def _get_jwks() -> dict:
    """Return cached JWKS, refreshing if stale."""
    if _jwks_cache is None or time.monotonic() - _jwks_fetched_at > _JWKS_TTL:
        return _fetch_jwks()
    return _jwks_cache


# ─── JWT verification ─────────────────────────────────────────────────────────

def _decode_asymmetric(token: str, jwks: dict) -> dict:
    """Decode an RS256/ES256 JWT using the provided JWKS."""
    return jwt.decode(
        token,
        jwks,
        algorithms=["RS256", "ES256"],
        options={"verify_aud": False},
    )


def _decode_symmetric(token: str) -> dict:
    """Decode a legacy HS256 JWT using the static secret."""
    if not settings.supabase_jwt_secret:
        raise JWTError("No JWT secret configured for HS256 verification")
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Validate a Supabase JWT and return the user ID (sub claim)."""
    token = credentials.credentials

    # ── Step 1: read the algorithm from the unverified header ────────────────
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed header",
        )

    algorithm: str = header.get("alg", "HS256")

    # ── Step 2: verify according to algorithm ────────────────────────────────
    try:
        if algorithm == "HS256":
            payload = _decode_symmetric(token)
        else:
            # RS256 / ES256 — try with cached JWKS first
            try:
                payload = _decode_asymmetric(token, _get_jwks())
            except JWTError:
                # One retry with freshly fetched keys (handles key rotation)
                payload = _decode_asymmetric(token, _fetch_jwks())

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )

    # ── Step 3: extract user ID ───────────────────────────────────────────────
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
        )
    return user_id


# ─── User's timezone / local date ─────────────────────────────────────────────

def get_user_tz(
    x_timezone: Annotated[Optional[str], Header()] = None,
) -> Optional[ZoneInfo]:
    """
    Fuso do usuário (header X-Timezone, ex: "America/Sao_Paulo").
    None quando ausente ou inválido — aí vale o relógio do servidor.
    """
    if x_timezone:
        try:
            return ZoneInfo(x_timezone)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return None


def get_user_today(
    tz: Annotated[Optional[ZoneInfo], Depends(get_user_tz)],
) -> date:
    """"Hoje" no fuso do usuário."""
    return datetime.now(tz).date() if tz else date.today()


# ─── Convenience type aliases ─────────────────────────────────────────────────

CurrentUser = Annotated[str, Depends(get_current_user_id)]
DB = Annotated[AsyncSession, Depends(get_db)]
Today = Annotated[date, Depends(get_user_today)]
UserTZ = Annotated[Optional[ZoneInfo], Depends(get_user_tz)]
