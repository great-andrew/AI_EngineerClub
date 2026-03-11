from pydantic import BaseModel
from typing import Optional


class UserAccountContext(BaseModel):

    customer_id: int
    name: str


class InputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class MenuOutputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class ComplaintOutputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class OrderOutputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class ReservationOutputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class HandoffData(BaseModel):

    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str
