"""Growth plan generation and retrieval."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile, GrowthPlan, ResearchRun
from app.db.session import get_db
from app.schemas.models import GrowthPlanCreate, GrowthPlanOut
from app.services.growth_service import create_growth_plan

router = APIRouter(prefix="/growth-plans", tags=["growth plans"])


@router.post("", response_model=GrowthPlanOut, status_code=201)
def generate_plan(payload: GrowthPlanCreate, db: Session = Depends(get_db)):
    business = db.get(BusinessProfile, payload.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    research = db.get(ResearchRun, payload.research_run_id) if payload.research_run_id else None
    if payload.research_run_id and (not research or research.business_id != business.id):
        raise HTTPException(status_code=404, detail="Research run not found for this business")
    return create_growth_plan(db, business, research)


@router.get("/{plan_id}", response_model=GrowthPlanOut)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.get(GrowthPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Growth plan not found")
    return plan
