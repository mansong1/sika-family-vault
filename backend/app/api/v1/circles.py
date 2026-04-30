from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import SusuCircle, CircleStatus
from app.schemas import SusuCircleCreate, SusuCircleResponse

router = APIRouter(prefix="/circles", tags=["circles"])

@router.post("", response_model=SusuCircleResponse, status_code=201)
def create_circle(payload: SusuCircleCreate, db: Session = Depends(get_db)):
    circle = SusuCircle(**payload.model_dump(), status=CircleStatus.PENDING)
    db.add(circle)
    db.commit()
    db.refresh(circle)
    return circle

@router.get("", response_model=List[SusuCircleResponse])
def list_circles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(SusuCircle).offset(skip).limit(limit).all()

@router.get("/{circle_id}", response_model=SusuCircleResponse)
def get_circle(circle_id: UUID, db: Session = Depends(get_db)):
    circle = db.query(SusuCircle).filter(SusuCircle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    return circle

@router.patch("/{circle_id}/activate", response_model=SusuCircleResponse)
def activate_circle(circle_id: UUID, db: Session = Depends(get_db)):
    circle = db.query(SusuCircle).filter(SusuCircle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    circle.status = CircleStatus.ACTIVE
    db.commit()
    db.refresh(circle)
    return circle
