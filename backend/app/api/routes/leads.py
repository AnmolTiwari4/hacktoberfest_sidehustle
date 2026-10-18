"""Lead discovery, CRUD, filtering, and CSV export."""

import csv
import io
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile, Lead, LeadSource, ResearchRun, Source
from app.db.session import get_db
from app.schemas.models import LeadList, LeadOut, LeadPatch, LeadSearch
from app.services.scoring_service import score_lead
from app.services.search_service import SearchProviderError, search_maps

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/search", response_model=LeadList)
def discover_leads(payload: LeadSearch, db: Session = Depends(get_db)):
    business = db.get(BusinessProfile, payload.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    location = payload.location or (business.target_locations or [None])[0]
    if not location:
        raise HTTPException(status_code=422, detail="Provide a location or add target_locations to the business profile")
    query = payload.query or f"{business.industry} {business.name}"
    try:
        candidates = search_maps(query, location, payload.limit)
    except SearchProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    run = ResearchRun(business_id=business.id, run_type="leads", query_params={"query": query, "location": location}, status="running")
    db.add(run)
    db.flush()
    existing = db.query(Lead).filter(Lead.business_id == business.id).all()
    created = []
    for candidate in candidates:
        score, reasons = score_lead({"industry": business.industry, "products": business.products or [], "target_locations": business.target_locations or []}, candidate)
        website = candidate.get("website")
        domain = (urlparse(website).hostname or "").removeprefix("www.").lower() if website else None
        candidate_address = (candidate.get("address") or "").strip().lower()
        lead = next((x for x in existing if (domain and x.website and (urlparse(x.website).hostname or "").removeprefix("www.").lower() == domain) or (not domain and x.name.casefold() == candidate["name"].casefold() and (x.address or "").strip().lower() == candidate_address)), None)
        if lead:
            lead.fit_score, lead.fit_reasons = score, reasons
        else:
            lead = Lead(business_id=business.id, name=candidate["name"], website=website, address=candidate.get("address"), category=candidate.get("category"), lead_type="business", fit_score=score, fit_reasons=reasons)
            db.add(lead)
            db.flush()
            existing.append(lead)
        if candidate.get("url"):
            source = Source(research_run_id=run.id, url=candidate["url"], title=candidate["title"], source_type="maps", snippet=candidate.get("snippet", ""))
            db.add(source)
            db.flush()
            if not any(link.source_id == source.id for link in lead.source_links):
                db.add(LeadSource(lead_id=lead.id, source_id=source.id, relationship_type="discovered_from"))
        created.append(lead)
    from datetime import datetime, timezone
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    for item in created:
        db.refresh(item)
    return {"items": created, "total": len(created)}


@router.get("", response_model=LeadList)
def list_leads(business_id: str | None = None, status: str | None = None, min_score: float = Query(default=0, ge=0, le=100), limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Lead)
    if business_id:
        query = query.filter(Lead.business_id == business_id)
    if status:
        query = query.filter(Lead.status == status)
    query = query.filter(Lead.fit_score >= min_score)
    total = query.count()
    items = query.order_by(Lead.fit_score.desc(), Lead.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/export")
def export_leads(business_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Lead)
    if business_id:
        query = query.filter(Lead.business_id == business_id)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "business_id", "name", "website", "address", "category", "fit_score", "fit_reasons", "status", "notes", "created_at"])
    for lead in query.order_by(Lead.fit_score.desc()).all():
        writer.writerow([lead.id, lead.business_id, lead.name, lead.website or "", lead.address or "", lead.category or "", lead.fit_score, "; ".join(lead.fit_reasons or []), lead.status, lead.notes or "", lead.created_at.isoformat() if lead.created_at else ""])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=marketscout-leads.csv"})


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: str, payload: LeadPatch, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead
