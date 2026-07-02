from typing import Any

from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    event_type: str = Field(..., examples=["order.created"])
    payload: dict[str, Any] = Field(default_factory=dict)


class EventAcceptedResponse(BaseModel):
    event_id: str
    status: str
    message: str


class EventStatusResponse(BaseModel):
    event_id: str
    event_type: str
    payload: dict[str, Any]
    status: str
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: str | None = None
