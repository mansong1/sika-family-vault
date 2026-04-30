from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import SusuMember, SusuCircle, MemberStatus
from app.schemas import SusuMemberCreate, SusuMemberResponse

router = APIRouter(prefix="/members", tags=["members"])

@router.post("", response_model=SusuMemberResponse, status_code=201)
def add_member(payload: SusuMemberCreate, circle_id: UUID, db: Session = Depends(get_db)):
    circle = db.query(SusuCircle).filter(SusuCircle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    member = SusuMember(**payload.model_dump(), circle_id=circle_id, user_id="user_placeholder", status=MemberStatus.INVITED)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.get("/circle/{circle_id}", response_model=List[SusuMemberResponse])
def list_members(circle_id: UUID, db: Session = Depends(get_db)):
    return db.query(SusuMember).filter(SusuMember.circle_id == circle_id).all()

@router.patch("/{member_id}/accept", response_model=SusuMemberResponse)
def accept_invite(member_id: UUID, db: Session = Depends(get_db)):
    member = db.query(SusuMember).filter(SusuMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.status = MemberStatus.ACTIVE
    db.commit()
    db.refresh(member)
    return member
