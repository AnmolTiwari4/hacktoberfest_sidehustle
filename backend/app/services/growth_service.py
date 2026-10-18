"""Evidence-grounded growth plan orchestration."""

from typing import Any

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile, GrowthPlan, ResearchRun
from app.schemas.models import Recommendation
from app.services.ai_service import AIServiceError, generate_structured


class PlanAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)
    recommendations: list[Recommendation] = Field(min_length=3, max_length=15)

    @model_validator(mode="after")
    def require_each_horizon(self):
        horizons = {item.timeframe for item in self.recommendations}
        if horizons != {"7 days", "30 days", "90 days"}:
            raise ValueError("Recommendations must cover 7, 30, and 90 days")
        return self


def create_growth_plan(db: Session, business: BusinessProfile, research: ResearchRun | None) -> GrowthPlan:
    evidence = []
    if research:
        evidence = [{"url": s.url, "title": s.title, "snippet": s.snippet} for s in research.sources]
    prompt = (
        "Create practical, measurable recommendations for the next 7, 30, and 90 days. "
        "Return JSON {summary, recommendations}; every recommendation requires timeframe, title, action, rationale, "
        "evidence_urls, priority. Use only URLs from supplied evidence; if evidence is thin, say so and propose validation steps. "
        f"Business: {business.name}; industry: {business.industry}; products: {business.products}; target locations: {business.target_locations}; "
        f"ideal customer: {business.ideal_customer}; research evidence: {evidence[:40]}"
    )
    try:
        result = generate_structured(prompt, PlanAnalysis)
        summary = result.summary
        known_urls = {item["url"] for item in evidence}
        recommendations: list[dict[str, Any]] = [
            {**item.model_dump(), "evidence_urls": [url for url in item.evidence_urls if url in known_urls]}
            for item in result.recommendations
        ]
        if evidence and any(not item["evidence_urls"] for item in recommendations):
            raise AIServiceError("Groq returned recommendations without valid evidence citations")
    except AIServiceError:
        # Actionable, transparent plan when Groq is not configured or unavailable.
        summary = "A validation-first plan based on the available business profile and research. Verify assumptions before committing budget."
        url = evidence[0]["url"] if evidence else ""
        recommendations = [
            {"timeframe": "7 days", "title": "Validate customer demand", "action": "Interview five target customers and record the problem, current workaround, and willingness to pay.", "rationale": "Customer conversations test demand before spending on acquisition.", "evidence_urls": [url] if url else [], "priority": "high"},
            {"timeframe": "30 days", "title": "Run a focused acquisition test", "action": "Choose one target location and one customer segment; run a small outreach or landing-page test and track qualified responses.", "rationale": "A narrow experiment makes channel performance measurable.", "evidence_urls": [url] if url else [], "priority": "medium"},
            {"timeframe": "90 days", "title": "Scale the proven channel", "action": "Compare acquisition cost and conversion quality across tests, then expand only the channel that meets a predefined return threshold.", "rationale": "Scaling after validation limits wasted effort and spend.", "evidence_urls": [url] if url else [], "priority": "medium"},
        ]
    plan = GrowthPlan(business_id=business.id, research_run_id=research.id if research else None, summary=summary, recommendations=recommendations)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
