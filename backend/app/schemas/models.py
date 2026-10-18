"""Validated API contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints
from typing_extensions import Annotated

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BusinessCreate(BaseModel):
    name: Name
    industry: Name
    description: str = Field(default="", max_length=10000)
    products: list[str] = Field(default_factory=list, max_length=50)
    target_locations: list[str] = Field(default_factory=list, max_length=50)
    ideal_customer: str = Field(default="", max_length=5000)


class BusinessPatch(BaseModel):
    name: Name | None = None
    industry: Name | None = None
    description: str | None = Field(default=None, max_length=10000)
    products: list[str] | None = Field(default=None, max_length=50)
    target_locations: list[str] | None = Field(default=None, max_length=50)
    ideal_customer: str | None = Field(default=None, max_length=5000)


class BusinessOut(BusinessCreate, ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class ResearchCreate(BaseModel):
    business_id: str
    run_type: Literal["market", "leads"] = "market"
    location: str | None = Field(default=None, max_length=240)
    query: str | None = Field(default=None, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class ResearchOut(ORMModel):
    id: str
    business_id: str
    run_type: str
    query_params: dict[str, Any]
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class SourceOut(ORMModel):
    id: str
    url: str
    title: str
    source_type: str
    snippet: str
    retrieved_at: datetime


class ReportOut(BaseModel):
    research: ResearchOut
    summary: str
    findings: list[dict[str, Any]]
    sources: list[SourceOut]


class LeadSearch(BaseModel):
    business_id: str
    location: str | None = Field(default=None, max_length=240)
    query: str | None = Field(default=None, max_length=500)
    limit: int = Field(default=20, ge=1, le=50)


class LeadPatch(BaseModel):
    status: Literal["new", "contacted", "qualified", "converted", "rejected"] | None = None
    notes: str | None = Field(default=None, max_length=10000)


class LeadOut(ORMModel):
    id: str
    business_id: str
    name: str
    website: str | None
    address: str | None
    category: str | None
    lead_type: str
    fit_score: float
    fit_reasons: list[str]
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime


class LeadList(BaseModel):
    items: list[LeadOut]
    total: int


class Recommendation(BaseModel):
    timeframe: Literal["7 days", "30 days", "90 days"]
    title: str = Field(min_length=1, max_length=200)
    action: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=2000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=10)
    priority: Literal["high", "medium", "low"] = "medium"


class GrowthPlanCreate(BaseModel):
    business_id: str
    research_run_id: str | None = None


class GrowthPlanOut(ORMModel):
    id: str
    business_id: str
    research_run_id: str | None
    summary: str
    recommendations: list[dict[str, Any]]
    created_at: datetime
