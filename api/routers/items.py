from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from deps import CurrentUser, DB
from models.goals import Goal
from models.items import Item
from schemas.items import ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

# Campos que podem ser limpos com null num PATCH
_NULLABLE = {"goal_id", "due_date", "title"}


@router.get("", response_model=list[ItemOut])
async def list_items(
    user_id: CurrentUser,
    db: DB,
    type: str | None = Query("task"),
    goal_id: UUID | None = Query(None),
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
    if goal_id:
        q = q.where(Item.goal_id == goal_id)
    result = await db.execute(q)
    return result.scalars().all()


async def _check_goal(db: DB, uid: UUID, goal_id: UUID | None) -> None:
    """A missão precisa existir e ser do usuário."""
    if goal_id is None:
        return
    result = await db.execute(select(Goal.id).where(Goal.id == goal_id, Goal.user_id == uid))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Goal not found")


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(user_id: CurrentUser, db: DB, body: ItemCreate):
    uid = UUID(user_id)
    await _check_goal(db, uid, body.goal_id)
    item = Item(user_id=uid, **body.model_dump())
    if item.completed:
        item.completed_at = datetime.now(timezone.utc)
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

    changes = body.model_dump(exclude_unset=True)
    if "goal_id" in changes:
        await _check_goal(db, UUID(user_id), changes["goal_id"])
    if changes.get("completed") is not None and changes["completed"] != item.completed:
        item.completed_at = datetime.now(timezone.utc) if changes["completed"] else None

    for field, value in changes.items():
        if value is None and field not in _NULLABLE:
            continue  # campos obrigatórios não aceitam null
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
