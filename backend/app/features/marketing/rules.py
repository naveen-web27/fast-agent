"""Pure pipeline rules for RightConnect Marketing leads (no database), shared by the service and tests."""
from datetime import date

STATUSES = ("new", "called", "interested", "converted", "in_progress", "completed", "lost")
STATUS_LABELS = {
    "new": "New",
    "called": "Called",
    "interested": "Interested",
    "converted": "Converted",
    "in_progress": "Work in progress",
    "completed": "Completed",
    "lost": "Lost",
}
# No follow-up is due once the work is delivered or the lead is lost.
CLOSED = ("completed", "lost")


def status_change_text(old: str, new: str) -> str:
    return f"{STATUS_LABELS.get(old, old)} → {STATUS_LABELS.get(new, new)}"


def status_after_activity(current: str, kind: str) -> str | None:
    """New status implied by logging an activity, or None to keep the current one.
    Calling, messaging or meeting a New lead means it has been called; a payment confirms the deal."""
    if current == "new" and kind in ("call", "whatsapp", "meeting"):
        return "called"
    if kind == "payment" and current in ("new", "called", "interested", "lost"):
        return "converted"
    return None


def payment_state(deal_amount: int | None, paid: int) -> str:
    """'paid', 'partial', 'due' (deal agreed, nothing received) or 'none' (no price agreed and nothing received)."""
    if deal_amount:
        if paid >= deal_amount:
            return "paid"
        return "partial" if paid > 0 else "due"
    return "paid" if paid > 0 else "none"


def is_due(status: str, follow_up_on: date | None, today: date) -> bool:
    """Follow-up date today or earlier and the lead still open."""
    return follow_up_on is not None and follow_up_on <= today and status not in CLOSED
