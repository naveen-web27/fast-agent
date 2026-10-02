"""Validation models for company team seats."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class InvitePayload(BaseModel):
    email: EmailStr


class TeamMemberOut(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    member_role: Literal["admin", "staff"]
    open_assigned: int


class PendingInviteOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class TeamResponse(BaseModel):
    organization_id: UUID
    name: str
    can_manage: bool
    plan_active: bool
    seat_limit: int
    seats_used: int
    members: list[TeamMemberOut]
    invites: list[PendingInviteOut]
