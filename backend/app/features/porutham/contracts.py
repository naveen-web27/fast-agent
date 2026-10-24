"""Validated request bodies for the compatibility API."""
from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .report import stars_for_rasi


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Birth(StrictInput):
    name: str = Field(default="", max_length=100)
    birth_date: date
    birth_time: time
    place: str = Field(default="", max_length=160)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)

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
        return value.replace(microsecond=0)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Choose a valid IANA timezone") from exc
        return value


class StarChoice(StrictInput):
    name: str = Field(default="", max_length=100)
    rasi: int = Field(ge=0, le=11)
    nakshatra: int = Field(ge=0, le=26)

    @model_validator(mode="after")
    def star_in_rasi(self) -> "StarChoice":
        if self.nakshatra not in stars_for_rasi(self.rasi):
            raise ValueError("This Nakshatra does not fall in the chosen Rasi")
        return self


class Pair(StrictInput):
    bride: StarChoice
    groom: StarChoice


class RasiRequest(Pair):
    language: Literal["ta", "en"] = "ta"


class KattamRequest(StrictInput):
    language: Literal["ta", "en"] = "ta"
    bride: Birth
    groom: Birth
    selected: Pair | None = None


class PaymentProof(StrictInput):
    razorpay_order_id: str = Field(pattern=r"^order_[A-Za-z0-9]{1,40}$")
    razorpay_payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]{1,40}$")
    razorpay_signature: str = Field(min_length=1, max_length=128)


class UnlockRequest(KattamRequest):
    payment: PaymentProof


class JathagamRequest(StrictInput):
    language: Literal["ta", "en"] = "ta"
    person: Birth


class JathagamUnlockRequest(JathagamRequest):
    payment: PaymentProof
