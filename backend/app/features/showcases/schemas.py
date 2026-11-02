"""Request and response contracts for provider video showcases."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.showcases.links import parse_video_link


class ShowcaseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_url: str = Field(min_length=8, max_length=500)
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=600)
    cover_url: str | None = Field(default=None, max_length=1000)

    @field_validator("source_url")
    @classmethod
    def valid_video(cls, value: str) -> str:
        return parse_video_link(value).url


class PreviewInput(BaseModel):
    source_url: str = Field(min_length=8, max_length=500)


class VideoPreview(BaseModel):
    source_url: str
    platform: Literal["youtube", "instagram"]
    thumbnail_url: str | None
    message: str


class ShowcaseOut(BaseModel):
    id: UUID
    profile_id: UUID
    provider_name: str
    source_url: str
    platform: Literal["youtube", "instagram"]
    title: str
    description: str
    cover_url: str
    created_at: datetime


class ShowcaseList(BaseModel):
    results: list[ShowcaseOut]
    total: int
    page: int
    page_size: int


class ManagedShowcases(BaseModel):
    results: list[ShowcaseOut]
    total: int
    limit: int
    plan_active: bool
