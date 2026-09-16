"""Functions to call the Meta WhatsApp Cloud API (send text, send interactive list, mark read)."""
import logging

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

GRAPH_BASE_URL = "https://graph.facebook.com"


def _messages_url(phone_number_id: str) -> str:
    return f"{GRAPH_BASE_URL}/{settings.whatsapp_api_version}/{phone_number_id}/messages"


def _headers() -> dict:
    # Plug in your Meta WhatsApp Cloud API access token via WHATSAPP_TOKEN env var.
    return {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }


async def send_text_message(phone_number_id: str, to: str, body: str) -> dict:
    """Send a plain text WhatsApp message."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    return await _post(phone_number_id, payload)


async def send_interactive_list(
    phone_number_id: str,
    to: str,
    header_text: str,
    body_text: str,
    button_text: str,
    sections: list[dict],
) -> dict:
    """Send a WhatsApp interactive list message.

    sections example:
    [{"title": "Shirts", "rows": [{"id": "prod_1", "title": "Blue Shirt", "description": "$20 - In stock"}]}]
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header_text},
            "body": {"text": body_text},
            "action": {"button": button_text, "sections": sections},
        },
    }
    return await _post(phone_number_id, payload)


async def send_interactive_buttons(
    phone_number_id: str,
    to: str,
    body_text: str,
    buttons: list[dict],
) -> dict:
    """Send a WhatsApp interactive reply-buttons message (max 3 buttons).

    buttons example: [{"id": "talk_to_human", "title": "Talk to a person"}]
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}} for b in buttons
                ]
            },
        },
    }
    return await _post(phone_number_id, payload)


async def mark_message_read(phone_number_id: str, message_id: str) -> dict:
    """Mark an incoming message as read (blue ticks)."""
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    return await _post(phone_number_id, payload)


async def send_template_message(phone_number_id: str, to: str, template_name: str, language_code: str = "en_US", components: list | None = None) -> dict:
    """Send a template message (used for proactive notifications outside the 24hr window)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            **({"components": components} if components else {}),
        },
    }
    return await _post(phone_number_id, payload)


async def _post(phone_number_id: str, payload: dict) -> dict:
    url = _messages_url(phone_number_id)
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, headers=_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("WhatsApp API error %s: %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.HTTPError as exc:
            logger.error("WhatsApp API request failed: %s", exc)
            raise
