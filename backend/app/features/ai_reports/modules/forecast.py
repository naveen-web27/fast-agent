from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field

from ..astrology import RASI, metadata, panchangam
from ..contracts import StrictInput, WrittenReport


class ForecastInput(StrictInput):
    rasi: int = Field(ge=0, le=11, strict=True)
    period: Literal["daily", "weekly"] = "daily"


class ForecastService:
    key = "forecast"
    title_ta = "ராசிப் பலன்"
    title_en = "Daily and Weekly Sky Context"
    description_ta = "சென்னை நேரப் பஞ்சாங்க நிலைகள் மற்றும் ராசியிலிருந்து கிரகப் பெயர்ச்சிகள்."
    description_en = "Actual dated Chennai noon Panchangam and transits relative to the selected Moon sign."
    icon = "calendar-days"
    input_schema = ForecastInput
    sections = ("Dates and Chennai Reference", "Tithi Nakshatra Vara Yoga and Karana",
                "Daily Planetary Transits", "Traditional Reflection for the Selected Sign", "Timing and Prediction Limits")

    def calculate(self, inputs: ForecastInput) -> dict:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        days = []
        for offset in range(7 if inputs.period == "weekly" else 1):
            snapshot = panchangam(now.date() + timedelta(days=offset))
            snapshot["houses_from_selected_rasi"] = {
                planet: (position["rasi"] - inputs.rasi) % 12 + 1
                for planet, position in snapshot["transits"].items()}
            days.append(snapshot)
        return {"metadata": metadata(), "rasi": inputs.rasi, "rasi_name": RASI[inputs.rasi],
                "period": inputs.period, "generated_at": now.isoformat(), "days": days,
                "limitations": ["Daily means today in Asia/Kolkata; weekly means today and the next six actual dates.",
                                "Noon geocentric snapshots, not sunrise-based day assignment or a personalized natal forecast.",
                                "No lucky guarantees, exact event timing, medical or financial predictions."]}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)