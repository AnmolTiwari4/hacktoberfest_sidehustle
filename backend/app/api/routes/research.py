"""Market research run endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile, ResearchRun, Source
from app.db.session import get_db
from app.schemas.models import ReportOut, ResearchCreate, ResearchOut, SourceOut
from app.services.market_service import run_market_research
from app.services.search_service import SearchProviderError

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchOut, status_code=201)
def create_research(payload: ResearchCreate, db: Session = Depends(get_db)):
    business = db.get(BusinessProfile, payload.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    location = payload.location or (business.target_locations or [None])[0]
    if not location:
        raise HTTPException(status_code=422, detail="Provide a location or add target_locations to the business profile")
    try:
        run, summary, findings = run_market_research(db, business, location, payload.query, payload.limit)
        run.query_params = {**run.query_params, "report": {"summary": summary, "findings": findings}}
        db.commit()
        db.refresh(run)
        return run
    except SearchProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Research run failed") from exc


@router.get("/{research_id}", response_model=ResearchOut)
def get_research(research_id: str, db: Session = Depends(get_db)):
    run = db.get(ResearchRun, research_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.get("/{research_id}/report", response_model=ReportOut)
def get_report(research_id: str, db: Session = Depends(get_db)):
    run = db.get(ResearchRun, research_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    sources = db.query(Source).filter(Source.research_run_id == run.id).order_by(Source.retrieved_at.desc()).all()
    report = run.query_params.get("report", {})
    return {"research": run, "summary": report.get("summary", ""), "findings": report.get("findings", []), "sources": sources}
