from typing import Literal

from ..astrology import metadata
from ..contracts import StrictInput, WrittenReport
from ..rules import VASTU_PREFERRED

Direction = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


class VastuInput(StrictInput):
    facing: Direction
    main_door: Direction
    kitchen: Direction
    bedroom: Direction


class VastuService:
    key = "vastu"
    title_ta = "வாஸ்து"
    title_en = "Vastu Direction Review"
    description_ta = "வீட்டின் திசைகள் பற்றிய எளிய பாரம்பரிய ஒப்பீடு."
    description_en = "A limited traditional direction checklist, not an architectural assessment."
    icon = "compass"
    input_schema = VastuInput
    sections = ("Direction Inputs and Convention", "Facing and Main Entrance", "Kitchen and Bedroom",
                "Practical Safety Priorities", "Assessment Limits")

    def calculate(self, inputs: VastuInput) -> dict:
        return {"metadata": metadata(False), "inputs": inputs.model_dump(mode="json"),
                "variant": "Popular eight-direction checklist, unreviewed; directions absolute, not relative to facing",
                "checks": [{"area": area, "direction": direction,
                            "traditional_preference": direction in VASTU_PREFERRED[area],
                            "preferred_directions": sorted(VASTU_PREFERRED[area])}
                           for area, direction in inputs.model_dump().items()],
                "limitations": ["A direction outside this checklist is not a defect or a prediction of harm.",
                                "No floor plan, entrance pada, dimensions, site, ventilation or structural analysis.",
                                "Building codes, accessibility, fire safety and qualified architectural advice take priority.",
                                "Do not recommend demolition, relocation, purchases or costly remedies based on this checklist."]}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)