"""Business profile CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import BusinessProfile
from app.db.session import get_db
from app.schemas.models import BusinessCreate, BusinessOut, BusinessPatch

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)):
    business = BusinessProfile(**payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("", response_model=list[BusinessOut])
def list_businesses(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    return db.query(BusinessProfile).order_by(BusinessProfile.created_at.desc()).limit(limit).all()


@router.get("/{business_id}", response_model=BusinessOut)
def get_business(business_id: str, db: Session = Depends(get_db)):
    business = db.get(BusinessProfile, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    return business


@router.patch("/{business_id}", response_model=BusinessOut)
def update_business(business_id: str, payload: BusinessPatch, db: Session = Depends(get_db)):
    business = db.get(BusinessProfile, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business profile not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(business, key, value)
    db.commit()
    db.refresh(business)
    return business
