"""Ingests an incoming WhatsApp message: persists history, checks human handoff, dispatches intent."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.handlers.intent_handler import handle_intent
from src.models import Business, Conversation
from src.services.client_registry import get_business_by_phone_number_id as get_csv_business
from src.services import llm_agent, whatsapp_client

logger = logging.getLogger(__name__)


async def get_business_by_phone_number_id(db: AsyncSession, phone_number_id: str) -> Business | None:
    return get_csv_business(phone_number_id)


async def handle_incoming_message(db: AsyncSession, business: Business, phone_number_id: str, message: dict) -> None:
    from_number = message.get("from")
    message_id = message.get("id")
    text_body = _extract_text(message)

    if message_id:
        try:
            await whatsapp_client.mark_message_read(phone_number_id, message_id)
        except Exception:
            logger.warning("Failed to mark message %s as read", message_id)

    if not text_body:
        return

    # Persist the customer's message in conversation history (always ours).
    db.add(Conversation(business_id=business.id, customer_phone=from_number, role="customer", message=text_body))
    await db.commit()

    # If a human has taken over this conversation, stop auto-replying.
    if await _conversation_needs_human(db, business, from_number):
        logger.info("Conversation for %s/%s needs human - skipping auto-reply", business.id, from_number)
        return

    history = await _load_recent_history(db, business, from_number)
    intent_data = await llm_agent.classify_intent(text_body, history)

    reply_text = await handle_intent(db, business, phone_number_id, from_number, intent_data)

    if reply_text:
        db.add(Conversation(business_id=business.id, customer_phone=from_number, role="agent", message=reply_text))
        await db.commit()


def _extract_text(message: dict) -> str | None:
    if message.get("type") == "text":
        return message.get("text", {}).get("body")
    if message.get("type") == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "list_reply":
            return interactive["list_reply"].get("title")
        if interactive.get("type") == "button_reply":
            return interactive["button_reply"].get("title")
    return None


async def _conversation_needs_human(db: AsyncSession, business: Business, customer_phone: str) -> bool:
    stmt = (
        select(Conversation.needs_human)
        .where(Conversation.business_id == business.id, Conversation.customer_phone == customer_phone)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    needs_human = result.scalars().first()
    return bool(needs_human)


async def _load_recent_history(db: AsyncSession, business: Business, customer_phone: str, limit: int = 10) -> list[dict]:
    stmt = (
        select(Conversation)
        .where(Conversation.business_id == business.id, Conversation.customer_phone == customer_phone)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(reversed(result.scalars().all()))
    return [{"role": r.role, "message": r.message} for r in rows]
