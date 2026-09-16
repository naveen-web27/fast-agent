"""Admin endpoints for staff to manage the human-handoff flow."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import get_db
from src.models import Conversation

settings = get_settings()

router = APIRouter(prefix="/admin")


def require_admin(x_admin_key: str = Header(default="")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.post("/resolve")
async def resolve_conversation(
    business_id: str,
    customer_phone: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Mark a conversation as resolved so the agent resumes auto-replying (send X-Admin-Key header)."""
    stmt = (
        select(Conversation)
        .where(Conversation.business_id == business_id, Conversation.customer_phone == customer_phone)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest = result.scalars().first()
    if not latest:
        raise HTTPException(status_code=404, detail="Conversation not found")

    latest.needs_human = False
    db.add(latest)
    await db.commit()
    return {"status": "resolved"}
