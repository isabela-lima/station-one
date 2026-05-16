from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from deps import CurrentUser, DB
from models.wishlist import WishlistItem
from schemas.wishlist import WishlistCreate, WishlistOut

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=list[WishlistOut])
async def list_wishlist(user_id: CurrentUser, db: DB):
    result = await db.execute(
        select(WishlistItem)
        .where(WishlistItem.user_id == UUID(user_id))
        .order_by(WishlistItem.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=WishlistOut, status_code=status.HTTP_201_CREATED)
async def create_wishlist_item(user_id: CurrentUser, db: DB, body: WishlistCreate):
    item = WishlistItem(user_id=UUID(user_id), **body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(user_id: CurrentUser, db: DB, item_id: UUID):
    result = await db.execute(
        select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.user_id == UUID(user_id))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    await db.delete(item)
