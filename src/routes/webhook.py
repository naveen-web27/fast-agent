"""Webhook endpoints: Meta verification handshake + incoming customer message receiver."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import get_db
from src.handlers.message_handler import get_business_by_phone_number_id, handle_incoming_message

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # WHATSAPP_VERIFY_TOKEN must match the value you configure in the Meta App dashboard.
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    logger.info("Incoming webhook: %s", payload)

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        phone_number_id = value["metadata"]["phone_number_id"]
    except (KeyError, IndexError):
        # Not a customer message (e.g. status update entry with no messages) - ack and ignore.
        return {"status": "ignored"}

    messages = value.get("messages")
    if not messages:
        # Could be a status callback (sent/delivered/read) - nothing to do.
        return {"status": "ignored"}

    business = await get_business_by_phone_number_id(db, phone_number_id)
    if not business:
        logger.warning("No business registered for phone_number_id=%s", phone_number_id)
        return {"status": "ignored"}

    for message in messages:
        await handle_incoming_message(db, business, phone_number_id, message)

    return {"status": "received"}
