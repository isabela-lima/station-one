from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, select, update

from deps import CurrentUser, DB
from models.items import Item
from schemas.items import ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=list[ItemOut])
async def list_items(
    user_id: CurrentUser,
    db: DB,
    type: str | None = Query(None),
    priority: bool | None = Query(None),
    completed: bool | None = Query(None),
):
    q = select(Item).where(Item.user_id == UUID(user_id)).order_by(Item.created_at.desc())
    if type:
        q = q.where(Item.type == type)
    if priority is not None:
        q = q.where(Item.priority == priority)
    if completed is not None:
        q = q.where(Item.completed == completed)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(user_id: CurrentUser, db: DB, body: ItemCreate):
    item = Item(user_id=UUID(user_id), **body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemOut)
async def update_item(user_id: CurrentUser, db: DB, item_id: UUID, body: ItemUpdate):
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.user_id == UUID(user_id))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(user_id: CurrentUser, db: DB, item_id: UUID):
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.user_id == UUID(user_id))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
