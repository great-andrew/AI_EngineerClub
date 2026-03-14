from pydantic import BaseModel
from typing import Optional


class UserAccountContext(BaseModel):

    customer_id: int
    name: str


class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str
    detected_language: str = "ko"
    contains_pii: bool = False
    is_abusive: bool = False


class MenuOutputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str

    contains_unavailable_item: bool = False
    contains_incorrect_price: bool = False
    contains_allergen_error: bool = False


class TriageOutputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str


class OrderOutputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str

    contains_invalid_item: bool = False
    contains_incorrect_price: bool = False
    order_confirmed: bool = False


class ComplaintOutputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str
    made_unauthorized_promise: bool = False
    escalation_required: bool = False


class ReservationOutputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str
    contains_invalid_datetime: bool = False
    reservation_confirmed: bool = False
    contains_incorrect_capacity: bool = False


class HandoffData(BaseModel):

    to_agent_name: str
    reason: str
    issue_type: str
    issue_description: str
