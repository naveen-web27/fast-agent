import re
from datetime import date

from pydantic import Field, field_validator

from ..astrology import metadata
from ..contracts import StrictInput, WrittenReport
from ..rules import reduce_number


class NumerologyInput(StrictInput):
    full_name: str = Field(min_length=2, max_length=100, description="Full name in English spelling, A-Z letters and spaces only")
    birth_date: date

    @field_validator("full_name")
    @classmethod
    def english_spelling(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", normalized):
            raise ValueError("Use English A-Z spelling and spaces only; Tamil and other scripts cannot be scored")
        if normalized.lower() in {"unknown", "unspecified", "anonymous", "name", "full name", "not known", "not provided", "na", "none", "null", "test"}:
            raise ValueError("Supply the person's actual full name in English spelling")
        if len(normalized.replace(" ", "")) < 2:
            raise ValueError("Supply a full name, not a single initial")
        return normalized

    @field_validator("birth_date")
    @classmethod
    def valid_birth_date(cls, value: date) -> date:
        if value.year < 1900 or value > date.today():
            raise ValueError("Birth date must be between 1900 and today")
        return value


class NumerologyService:
    key = "numerology"
    title_ta = "எண் கணிதம்"
    title_en = "Numerology"
    description_ta = "ஆங்கிலப் பெயர் எழுத்துகள் மற்றும் பிறந்த தேதியின் எண் கணக்கீடு."
    description_en = "Transparent Pythagorean name and date arithmetic, without luck guarantees."
    icon = "hash"
    input_schema = NumerologyInput
    sections = ("Name Spelling and Method", "Name Number Calculation", "Birth and Life Path Numbers",
                "Traditional Reflection", "Spelling Sensitivity and Limitations")

    def calculate(self, inputs: NumerologyInput) -> dict:
        letters = [{"letter": letter, "value": (ord(letter) - ord("A")) % 9 + 1}
                   for letter in inputs.full_name.upper() if letter != " "]
        total = sum(entry["value"] for entry in letters)
        birth_digits = [int(digit) for digit in inputs.birth_date.strftime("%Y%m%d")]
        return {"metadata": metadata(False), "inputs": inputs.model_dump(mode="json"),
                "system": "Pythagorean repeating A=1 through I=9, J=1 through Z=8",
                "reduction": "Sum all digits repeatedly; preserve 11, 22, 33 at every reduction, including intermediate totals. Date components are not separately reduced.",
                "letters": letters, "name_total": total, "name_number": reduce_number(total),
                "birth_number": reduce_number(inputs.birth_date.day),
                "life_path_total": sum(birth_digits), "life_path_number": reduce_number(sum(birth_digits)),
                "limitations": ["This is a spelling-dependent cultural practice, not a prediction of luck or success.",
                                "No Chaldean scoring, lucky dates, guaranteed outcomes or name-change recommendation."]}

    async def generate_report(self, raw_data: dict, language: str = "ta") -> WrittenReport:
        from app.features.ai_reports.writer import write_report
        return await write_report(self.key, self.sections, raw_data, language)