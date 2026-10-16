"""Shared validated inputs and report contracts for independently registered services."""
from datetime import date, time
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BirthInput(StrictInput):
    name: str = Field(default="", max_length=100)
    birth_date: date
    birth_time: time
    place: str = Field(min_length=2, max_length=160)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    timezone: str = Field(default="Asia/Kolkata", max_length=80)

    @field_validator("birth_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value.year < 1900 or value > date.today():
            raise ValueError("Birth date must be between 1900 and today")
        return value

    @field_validator("birth_time")
    @classmethod
    def local_time(cls, value: time) -> time:
        if value.tzinfo is not None:
            raise ValueError("Enter local birth time without a UTC offset")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Choose a valid IANA timezone") from exc
        return value


class ReportRequest(StrictInput):
    inputs: dict[str, Any]
    language: Literal["ta", "en"] = "ta"
    tier: Literal["basic"] = "basic"
    consent: Literal[True]


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    heading: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=6000)


class WrittenReport(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    sections: list[ReportSection] = Field(min_length=1, max_length=12)
    disclaimer: str = Field(min_length=1, max_length=1500)


class ServiceModule(Protocol):
    key: str
    title_ta: str
    title_en: str
    description_ta: str
    description_en: str
    icon: str
    input_schema: type[BaseModel]
    sections: tuple[str, ...]

    def calculate(self, inputs: BaseModel) -> dict[str, Any]: ...

    async def generate_report(self, raw_data: dict[str, Any], language: str = "ta") -> WrittenReport: ...