from typing import Literal

from ..astrology import birth_chart
from ..contracts import BirthInput, WrittenReport
from ..rules import baby_name_options


class BabyNamesInput(BirthInput):
    gender: Literal["neutral", "male", "female"] = "neutral"


class BabyNamesService:
    key = "baby-names"
    title_ta = "குழந்தைப் பெயர்கள்"
    title_en = "Tamil Baby Names"
    description_ta = "நட்சத்திரப் பாத ஒலிக்கு ஏற்ப தேர்ந்தெடுக்கப்பட்ட தமிழ்ப் பெயர்கள்."
    description_en = "A small curated Tamil name collection matched to the calculated naming syllable."
    icon = "baby"
    input_schema = BabyNamesInput
    sections = ("Birth Star and Pada", "Traditional Naming Syllable", "Curated Tamil Names and Meanings",
                "Coverage and Transliteration Limits")

    def calculate(self, inputs: BabyNamesInput) -> dict:
        chart = birth_chart(inputs)
        options = baby_name_options(chart["moon"]["nakshatra"], chart["moon"]["pada"], inputs.gender)
        return {"metadata": chart["metadata"], "birth": chart["birth"], "moon": chart["moon"],
                "gender": inputs.gender, **options,
                "interpretation_policy": "Use only the returned names and lexical meanings. When names is empty say no curated match; never invent names, meanings or alternate matching syllables."}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)