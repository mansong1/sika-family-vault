from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Wallet
from app.schemas import WalletResponse

router = APIRouter(prefix="/wallets", tags=["wallets"])

@router.get("/circle/{circle_id}", response_model=WalletResponse)
def get_wallet(circle_id: UUID, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.circle_id == circle_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet
