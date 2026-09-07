"""Shared Pydantic models (P-02). Protected after P-02: changes need an ADR."""

from __future__ import annotations

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
    status: str = Field(description="ok | needs_help | medical | unclear | unreachable | opted_out")
    need: str = Field(default="", description="none | cooling | transport | power | wellness_check | other (ADR-002)")
    confidence: float = 0.0
    reason: str = ""
    quote: str = Field(default="", description="resident's exact words that decided it (ADR-001)")


class Dispatch(BaseModel):
    resident_name: str
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
