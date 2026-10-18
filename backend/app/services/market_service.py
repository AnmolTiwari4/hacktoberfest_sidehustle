"""Market research orchestration and evidence-backed report generation."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile, ResearchRun, Source
from app.services.ai_service import AIServiceError, generate_structured
from app.services.search_service import build_queries, search_google, search_maps


class MarketFinding(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    insight: str = Field(min_length=1, max_length=2000)
    evidence_urls: list[str] = Field(default_factory=list)


class MarketAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)
    findings: list[MarketFinding] = Field(default_factory=list, max_length=12)


def run_market_research(db: Session, business: BusinessProfile, location: str, custom_query: str | None, limit: int) -> tuple[ResearchRun, str, list[dict[str, Any]]]:
    run = ResearchRun(business_id=business.id, run_type="market", query_params={"location": location, "query": custom_query, "limit": limit}, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    queries = build_queries(business.industry, business.products or [], location, custom_query)
    try:
        gathered: list[dict] = []
        for query in queries[:3]:
            gathered.extend(search_google(query, limit=min(limit, 10)))
        gathered.extend(search_maps(f"{business.industry} {business.name}", location, limit=limit))
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:4000]
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise
    unique = []
    seen_urls = set()
    for item in gathered:
        url = item.get("url") or ""
        key = url.lower().rstrip("/") or item.get("title", "").lower()
        if key not in seen_urls:
            seen_urls.add(key)
            unique.append(item)
    for item in unique:
        if item.get("url"):
            db.add(Source(research_run_id=run.id, url=item["url"], title=item["title"], source_type=item["source_type"], snippet=item["snippet"]))
    evidence = [{"title": x["title"], "url": x["url"], "snippet": x["snippet"], "source_type": x["source_type"]} for x in unique if x.get("url")]
    prompt = (
        "Create a concise market intelligence report using only the evidence provided. "
        "Return JSON with summary and findings [{title, insight, evidence_urls}]. "
        f"Business: {business.name}; industry: {business.industry}; products: {business.products}; location: {location}; "
        f"ideal customer: {business.ideal_customer}. Evidence: {evidence[:40]}"
    )
    try:
        if not evidence:
            raise AIServiceError("No source evidence was returned")
        analysis = generate_structured(prompt, MarketAnalysis)
        summary = analysis.summary
        known_urls = {item["url"] for item in evidence}
        findings = [
            {**item.model_dump(), "evidence_urls": [url for url in item.evidence_urls if url in known_urls]}
            for item in analysis.findings
        ]
        findings = [item for item in findings if item["evidence_urls"]]
    except AIServiceError:
        # Search results remain useful when the optional summarizer is down; make the fallback explicit.
        summary = f"Collected {len(evidence)} public sources for {business.industry} in {location}. Review the cited evidence below; AI synthesis was unavailable."
        findings = [{"title": e["title"], "insight": e["snippet"] or "No source excerpt was provided.", "evidence_urls": [e["url"]]} for e in evidence[:12]]
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run, summary, findings
