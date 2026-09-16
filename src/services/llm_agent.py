"""OpenAI-powered intent detection and entity extraction.

IMPORTANT: The LLM is used ONLY to understand/classify the customer's message and extract
structured entities. It must NEVER be used to fabricate business facts (price, stock, order
status) — those always come from src/data_access.py (hosted DB query or client API call).
"""
import json
import logging

from openai import AsyncOpenAI

from src.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Plug in your OpenAI API key via OPENAI_API_KEY env var.
_client = AsyncOpenAI(api_key=settings.openai_api_key)

VALID_INTENTS = {
    "browse_products",
    "product_issue",
    "rate_product",
    "track_order",
    "talk_to_human",
    "general_question",
}

SYSTEM_PROMPT = """You are an intent classifier for a WhatsApp customer-support and sales agent \
for a small retail business (e.g. a cloth shop). Given the latest customer message and recent \
conversation history, classify the customer's intent and extract any relevant entities.

Return ONLY a JSON object (no prose) with this shape:
{
  "intent": one of ["browse_products", "product_issue", "rate_product", "track_order", "talk_to_human", "general_question"],
  "category": string or null,        // for browse_products, e.g. "shirts"
  "order_id": string or null,        // for product_issue / track_order, if the customer gave one
  "product_name": string or null,    // for rate_product or product_issue, if mentioned
  "stars": integer or null,          // for rate_product, 1-5
  "reply_hint": string or null       // short note on what the customer seems to want, for general_question
}

Rules:
- Never invent prices, stock levels, or order statuses — you only classify and extract, you do not know real data.
- If the customer explicitly asks for a human/agent/manager, or seems frustrated/angry, use "talk_to_human".
- If unsure, prefer "general_question".
"""


async def classify_intent(message: str, history: list[dict]) -> dict:
    """Call OpenAI to classify intent + extract entities. Returns a validated dict.

    history: list of {"role": "customer"|"agent", "message": str}, most recent last.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-10:]:
        role = "user" if turn["role"] == "customer" else "assistant"
        messages.append({"role": role, "content": turn["message"]})
    messages.append({"role": "user", "content": message})

    try:
        response = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
    except Exception as exc:  # openai errors, json errors, etc.
        logger.error("LLM intent classification failed: %s", exc)
        return {"intent": "general_question", "category": None, "order_id": None, "product_name": None, "stars": None, "reply_hint": None}

    intent = parsed.get("intent")
    if intent not in VALID_INTENTS:
        intent = "general_question"

    return {
        "intent": intent,
        "category": parsed.get("category"),
        "order_id": parsed.get("order_id"),
        "product_name": parsed.get("product_name"),
        "stars": parsed.get("stars"),
        "reply_hint": parsed.get("reply_hint"),
    }
