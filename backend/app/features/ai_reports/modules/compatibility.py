from ..astrology import birth_chart, metadata
from ..contracts import BirthInput, StrictInput, WrittenReport
from ..rules import porutham


class CompatibilityInput(StrictInput):
    bride: BirthInput
    groom: BirthInput


class CompatibilityService:
    key = "compatibility"
    title_ta = "திருமணப் பொருத்தம்"
    title_en = "Traditional Porutham"
    description_ta = "பன்னிரண்டு பாரம்பரியக் கணக்கீடுகளின் வெளிப்படையான ஒப்பீடு; திருமண வெற்றி கணிப்பு அல்ல."
    description_en = "Twelve explicit traditional checks, not a marriage probability or recommendation."
    icon = "heart-handshake"
    input_schema = CompatibilityInput
    sections = ("Birth Stars and Rule Variant", "Dina Gana and Mahendra", "Stree Deergha and Yoni",
                "Rasi Rasi Adhipathi and Vasiya", "Rajju Vedha and Nadi", "Varna Convention and Limitations",
                "Twelve Rule Count and Uncertainty")

    def calculate(self, inputs: CompatibilityInput) -> dict:
        bride = birth_chart(inputs.bride)
        groom = birth_chart(inputs.groom)
        bride["birth"]["name"] = bride["birth"]["name"] or "பெண்"
        groom["birth"]["name"] = groom["birth"]["name"] or "பையன்"
        results = porutham(bride["moon"]["nakshatra"], groom["moon"]["nakshatra"],
                           bride["moon"]["rasi"], groom["moon"]["rasi"])
        return {"metadata": metadata(), "bride": bride, "groom": groom, "porutham": results,
                "interpretation_policy": "Describe only rule matches; never infer health, fertility, longevity, consent, personal worth or a marriage outcome."}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)