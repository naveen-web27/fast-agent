from datetime import datetime, timezone

from ..astrology import birth_chart, vimshottari
from ..contracts import BirthInput, WrittenReport
from ..rules import GEMSTONES, SIGN_LORDS


class GemstoneService:
    key = "gemstone"
    title_ta = "ரத்தின மரபுகள்"
    title_en = "Gemstone Traditions"
    description_ta = "கிரகங்களுடன் தொடர்புடைய ரத்தின மரபுகள்; அணிய வேண்டிய கட்டாயப் பரிந்துரை அல்ல."
    description_en = "Traditional associations and calculated mahadasa, not individualized suitability."
    icon = "gem"
    input_schema = BirthInput
    sections = ("Birth Chart Context", "Traditional Planet and Gem Associations", "Current Vimshottari Mahadasa",
                "Individual Suitability Not Assessed", "Evidence and Purchase Cautions")

    def calculate(self, inputs: BirthInput) -> dict:
        chart = birth_chart(inputs)
        now = datetime.now(timezone.utc)
        dasa = vimshottari(chart["moon"]["longitude"], datetime.fromisoformat(chart["utc"]), now)
        moon_lord = SIGN_LORDS[chart["moon"]["rasi"]]
        ascendant_lord = SIGN_LORDS[chart["ascendant"]["rasi"]]
        return {"metadata": chart["metadata"], "chart": chart, "vimshottari": dasa,
                "associations": [{"basis": basis, "planet": lord, "gemstone": GEMSTONES[lord],
                                  "status": "traditional_association_only"}
                                 for basis, lord in (("moon_sign_lord", moon_lord),
                                                     ("ascendant_lord", ascendant_lord), ("current_mahadasa_lord", dasa["lord"]))],
                "individualized_suitability": {"status": "not_assessed",
                    "reason": "Functional benefics, strength, divisional charts and conflicting traditions are not synthesized"},
                "limitations": ["A sign lord or mahadasa association does not imply that a stone should be worn.",
                                "No scientifically established health, financial, protective or luck benefit.",
                                "No must-wear instruction, dose, ritual prescription or purchase recommendation.",
                                "Do not ingest gemstones or substitute them for professional care."]}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)