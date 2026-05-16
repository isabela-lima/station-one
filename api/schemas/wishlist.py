from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class WishlistCreate(BaseModel):
    title: str
    url: str
    image_url: str | None = None
    description: str | None = None
    current_price: Decimal = Decimal("0")
    target_price: Decimal = Decimal("0")
    currency: str = "BRL"


class WishlistOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    title: str
    url: str
    image_url: str | None
    description: str | None
    current_price: Decimal
    target_price: Decimal
    currency: str
    created_at: datetime
