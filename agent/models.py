"""Shared Pydantic models (P-02). Protected after P-02: changes need an ADR."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HazardEvent(BaseModel):
    type: str = Field(description="heat | cold | outage")
    severity: str = Field(description="NWS severity or drill severity")
    onset: str | None = None
    expires: str | None = None
    headline: str
    source: str = Field(description="nws:<alert-id> | drill:<fixture> | coordinator:<id>")
    zone: str = ""


class BoundaryDecision(BaseModel):
    resident_name: str
    score: int
    tier: int = Field(description="1, 2, or 3")
    reason: str = Field(description="one line")


class TierPlan(BaseModel):
    decisions: list[BoundaryDecision] = Field(default_factory=list)


class Triage(BaseModel):
    status: Literal["ok", "needs_help", "medical", "unclear", "unreachable", "opted_out"]
    need: Literal["none", "cooling", "transport", "power", "wellness_check", "other"] = "none"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, strict=True, allow_inf_nan=False)
    reason: str = ""
    quote: str = Field(default="", description="resident's exact words that decided it (ADR-001)")


class Dispatch(BaseModel):
    resident_name: str
    resident_id: str = ""
    resource_id: str = ""
    resource_name: str = ""
    volunteer_name: str = ""
    message: str = ""
    status: str = "proposed"


class CoordinatorPing(BaseModel):
    headline: str
    tier1_count: int = 0
    tier2_count: int = 0
    tier3_count: int = 0
    needs_human: list[str] = Field(default_factory=list)
