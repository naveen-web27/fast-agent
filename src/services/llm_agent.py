"""Local rule-based intent detection and entity extraction.

This module does not call an external LLM. It classifies common customer-support messages,
tolerates small spelling mistakes, and extracts entities without inventing business data.
"""
import re
from difflib import SequenceMatcher

VALID_INTENTS = {
    "browse_products",
    "product_issue",
    "rate_product",
    "track_order",
    "talk_to_human",
    "general_question",
}

_KEYWORDS = {
    "talk_to_human": ("human", "person", "agent", "manager", "staff", "representative", "complaint"),
    "product_issue": ("broken", "damaged", "wrong", "return", "refund", "exchange", "issue", "problem", "defect"),
    "track_order": ("order", "track", "tracking", "delivery", "delivered", "shipping", "where", "arrive"),
    "rate_product": ("rate", "rating", "review", "stars", "feedback"),
    "browse_products": ("product", "products", "buy", "price", "cost", "available", "stock", "show", "shirt", "dress", "jeans"),
}

_CATEGORIES = ("shirts", "t-shirts", "dresses", "jeans", "trousers", "jackets", "shoes", "sarees")
_WORD_PATTERN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)?")
_ORDER_PATTERN = re.compile(r"\b(?:order\s*(?:id|no|number)?\s*[:#-]?\s*)?([a-z0-9][a-z0-9-]{3,})\b", re.IGNORECASE)
_STAR_PATTERN = re.compile(r"\b([1-5])\s*(?:star|stars|/\s*5)\b|\b([1-5])\s*/\s*5\b", re.IGNORECASE)


async def classify_intent(message: str, history: list[dict]) -> dict:
    """Classify a message locally; history is used for short follow-up messages."""
    text = _normalize(message)
    if "python render" in text:
        return {
            "intent": "general_question",
            "category": None,
            "order_id": None,
            "product_name": None,
            "stars": None,
            "reply_hint": "python_render_goodbye",
        }
    scores = {intent: _keyword_score(text, keywords) for intent, keywords in _KEYWORDS.items()}

    if _has_keyword(text, _KEYWORDS["talk_to_human"]):
        intent = "talk_to_human"
    elif _has_keyword(text, _KEYWORDS["product_issue"]):
        intent = "product_issue"
    elif scores["track_order"] > 0:
        intent = "track_order"
    elif scores["rate_product"] > 0:
        intent = "rate_product"
    elif scores["browse_products"] > 0:
        intent = "browse_products"
    else:
        intent = _intent_from_history(text, history)

    order_id = _extract_order_id(message) if intent in {"track_order", "product_issue"} else None
    stars = _extract_stars(message) if intent == "rate_product" else None
    category = _extract_category(text) if intent == "browse_products" else None
    product_name = _extract_product_name(message) if intent in {"rate_product", "product_issue"} else None

    return {
        "intent": intent,
        "category": category,
        "order_id": order_id,
        "product_name": product_name,
        "stars": stars,
        "reply_hint": None,
    }


def _normalize(value: str) -> str:
    return " ".join(_WORD_PATTERN.findall(value.lower()))


def _similar(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _has_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    words = text.split()
    return any(word == keyword or _similar(word, keyword) >= 0.78 for word in words for keyword in keywords)


def _keyword_score(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if _has_keyword(text, (keyword,)))


def _intent_from_history(text: str, history: list[dict]) -> str:
    if len(text.split()) <= 5:
        previous_customer_messages = [turn["message"] for turn in history if turn.get("role") == "customer"]
        if previous_customer_messages:
            previous = classify_message_sync(previous_customer_messages[-1])
            if previous["intent"] in {"track_order", "product_issue", "rate_product", "browse_products"}:
                return previous["intent"]
    return "general_question"


def classify_message_sync(message: str) -> dict:
    """Classify a previous message without entering the async public API."""
    text = _normalize(message)
    scores = {intent: _keyword_score(text, keywords) for intent, keywords in _KEYWORDS.items()}
    if scores["talk_to_human"]:
        intent = "talk_to_human"
    elif scores["product_issue"]:
        intent = "product_issue"
    elif scores["track_order"]:
        intent = "track_order"
    elif scores["rate_product"]:
        intent = "rate_product"
    elif scores["browse_products"]:
        intent = "browse_products"
    else:
        intent = "general_question"
    return {"intent": intent}


def _extract_order_id(message: str) -> str | None:
    match = _ORDER_PATTERN.search(message)
    if not match:
        return None
    value = match.group(1)
    if value.lower() in {"last", "week", "where", "is", "it", "status", "please"}:
        return None
    return value


def _extract_stars(message: str) -> int | None:
    match = _STAR_PATTERN.search(message)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _extract_category(text: str) -> str | None:
    for category in _CATEGORIES:
        if _has_keyword(text, (category.strip(),)):
            return category.strip()
    return None


def _extract_product_name(message: str) -> str | None:
    match = re.search(r"(?:rate|review|return|exchange|problem with|issue with)\s+(?:the\s+)?([a-z0-9][a-z0-9 -]{1,40})", message, re.IGNORECASE)
    return match.group(1).strip(" .,!?\n") if match else None
