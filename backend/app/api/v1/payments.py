from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Payment, Wallet, PaymentStatus
from app.schemas import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, wallet_id: UUID, member_id: UUID, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    payment = Payment(**payload.model_dump(), wallet_id=wallet_id, member_id=member_id, status=PaymentStatus.COMPLETED)
    wallet.balance += payload.amount
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/wallet/{wallet_id}", response_model=List[PaymentResponse])
def list_payments(wallet_id: UUID, db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.wallet_id == wallet_id).all()
