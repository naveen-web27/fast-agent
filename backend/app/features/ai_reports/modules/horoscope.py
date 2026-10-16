from ..astrology import birth_chart
from ..contracts import BirthInput, WrittenReport


class HoroscopeService:
    key = "horoscope"
    title_ta = "ஜாதகம்"
    title_en = "Birth Horoscope"
    description_ta = "பிறந்த நேரத்தின் கிரக நிலைகள் மற்றும் பாரம்பரிய விளக்கம்."
    description_en = "Calculated birth positions with clearly qualified traditional interpretation."
    icon = "orbit"
    input_schema = BirthInput
    sections = ("Birth Details and Calculation Method", "Moon Sign and Nakshatra",
                "Ascendant and Planetary Positions", "Traditional Reflection", "Uncomputed Factors and Limitations")

    def calculate(self, inputs: BirthInput) -> dict:
        return birth_chart(inputs)

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)