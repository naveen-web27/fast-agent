"""Per-intent business logic. Always fetches real data via src/services/data_access.py, never the LLM."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Business, Conversation
from src.services import data_access, whatsapp_client

logger = logging.getLogger(__name__)


async def handle_intent(db: AsyncSession, business: Business, phone_number_id: str, customer_phone: str, intent_data: dict) -> str:
    if intent_data.get("reply_hint") == "python_render_goodbye":
        reply = "Goodbye!"
        await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
        return reply

    intent = intent_data["intent"]

    if intent == "browse_products":
        return await _handle_browse_products(db, business, phone_number_id, customer_phone, intent_data)
    if intent in ("product_issue", "track_order"):
        return await _handle_track_order(db, business, phone_number_id, customer_phone, intent_data)
    if intent == "rate_product":
        return await _handle_rate_product(db, business, phone_number_id, customer_phone, intent_data)
    if intent == "talk_to_human":
        return await _handle_talk_to_human(db, business, phone_number_id, customer_phone)

    reply = "Thanks for your message! Could you tell me a bit more, or ask about our products, an order, or leave a rating?"
    await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
    return reply


async def _handle_browse_products(db, business, phone_number_id, customer_phone, intent_data) -> str:
    category = intent_data.get("category")
    products = await data_access.get_products(db, business, category=category)

    if not products:
        reply = f"Sorry, we couldn't find any products{f' in {category}' if category else ''} right now."
        await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
        return reply

    rows = [
        {
            "id": f"prod_{p['id']}",
            "title": str(p["name"])[:24],
            "description": f"${p['price']} - {'In stock' if p['stock'] > 0 else 'Out of stock'}"[:72],
        }
        for p in products[:10]
    ]
    await whatsapp_client.send_interactive_list(
        phone_number_id=phone_number_id,
        to=customer_phone,
        header_text="Our Products",
        body_text=f"Here are some products{f' in {category}' if category else ''} you might like:",
        button_text="View items",
        sections=[{"title": category or "Products", "rows": rows}],
    )
    return f"Sent product list ({len(rows)} items)"


async def _handle_track_order(db, business, phone_number_id, customer_phone, intent_data) -> str:
    order_id = intent_data.get("order_id")
    order = await data_access.get_order(db, business, order_id=order_id, customer_phone=customer_phone)

    if not order:
        reply = "We couldn't find that order. Could you double check the order ID?"
    else:
        reply = f"Order {order['id']} status: {order['status']}."
    await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
    return reply


async def _handle_rate_product(db, business, phone_number_id, customer_phone, intent_data) -> str:
    product_name = intent_data.get("product_name")
    stars = intent_data.get("stars")

    if not product_name or not stars:
        reply = "Which product would you like to rate, and how many stars (1-5)?"
        await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
        return reply

    try:
        result = await data_access.rate_product(db, business, product_ref=product_name, customer_phone=customer_phone, stars=int(stars))
        reply = f"Thanks for rating {product_name} {result['stars']}\u2b50! We appreciate your feedback."
    except ValueError:
        reply = "Ratings must be between 1 and 5 stars - could you confirm your rating?"
    await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
    return reply


async def _handle_talk_to_human(db, business, phone_number_id, customer_phone) -> str:
    stmt = (
        select(Conversation)
        .where(Conversation.business_id == business.id, Conversation.customer_phone == customer_phone)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest = result.scalars().first()
    if latest:
        latest.needs_human = True
        db.add(latest)
        await db.commit()

    # TODO: notify the shop owner/staff here (e.g. send a WhatsApp/email/Slack alert to a staff number).
    logger.info("Business %s: customer %s requested a human", business.id, customer_phone)

    reply = "I've flagged this conversation for our team - a staff member will follow up with you shortly."
    await whatsapp_client.send_text_message(phone_number_id, customer_phone, reply)
    return reply
