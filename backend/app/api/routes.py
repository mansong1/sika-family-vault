from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from ..models.susu import (
    SusuCircleCreate, SusuStatus, PaymentCreate, CreditScore, RoundUpRule, UserCreate, Token, LoginRequest
)
from ..services.susu_service import store
from ..core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/api/v1", tags=["susu"])
security = HTTPBearer(auto_error=False)

# Mock auth (in production would verify JWT against Supabase)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        # For demo, return a mock user
        user_id = "demo-user"
        if user_id not in store.users:
            store.users[user_id] = {
                "id": user_id,
                "email": "demo@sika.bank",
                "phone": "+233501234567",
                "full_name": "Demo User",
                "credit_score": CreditScore(
                    user_id=user_id,
                    score=500,
                    circles_completed=0,
                    on_time_payments=0,
                    late_payments=0,
                    defaulted_circles=0,
                    last_updated=datetime.now(timezone.utc)
                )
            }
        return store.users[user_id]
    
    # Real token verification would go here
    user_id = "demo-user"
    return store.users.get(user_id, {"id": user_id})

@router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "phone": user_data.phone_number,
        "full_name": user_data.full_name,
        "hashed_password": get_password_hash(user_data.password),
        "credit_score": CreditScore(
            user_id=user_id,
            score=500,
            circles_completed=0,
            on_time_payments=0,
            late_payments=0,
            defaulted_circles=0,
            last_updated=datetime.now(timezone.utc)
        )
    }
    store.users[user_id] = user
    store.credit_scores[user_id] = user["credit_score"]
    
    token = create_access_token({"sub": user_id})
    return {"user_id": user_id, "token": token, "message": "Registration successful"}

@router.post("/auth/login", response_model=Token)
async def login(credentials: LoginRequest):
    # Find user by email
    user = next((u for u in store.users.values() if u["email"] == credentials.email), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    return Token(access_token=token)

@router.get("/circles", response_model=List[dict])
async def get_circles(user: dict = Depends(get_current_user)):
    circles = store.get_user_circles(user["id"])
    return [{
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "status": c.status.value,
        "contribution_amount": c.contribution_amount,
        "cycle_length_days": c.cycle_length_days,
        "member_count": len(c.members),
        "max_members": c.max_members,
        "total_collected": c.total_collected,
        "insurance_pool_balance": c.insurance_pool_balance,
        "created_at": c.created_at.isoformat()
    } for c in circles]

@router.post("/circles", response_model=dict)
async def create_circle(circle_data: SusuCircleCreate, user: dict = Depends(get_current_user)):
    circle = store.create_circle(circle_data, user["id"])
    return {
        "id": circle.id,
        "name": circle.name,
        "status": circle.status.value,
        "message": "Susu circle created. Share the invite link with members."
    }

@router.get("/circles/{circle_id}", response_model=dict)
async def get_circle(circle_id: str, user: dict = Depends(get_current_user)):
    circle = store.circles.get(circle_id)
    if not circle or not any(m.user_id == user["id"] for m in circle.members):
        raise HTTPException(status_code=404, detail="Circle not found")
    
    return {
        "id": circle.id,
        "name": circle.name,
        "description": circle.description,
        "status": circle.status.value,
        "contribution_amount": circle.contribution_amount,
        "cycle_length_days": circle.cycle_length_days,
        "max_members": circle.max_members,
        "penalty_for_late": circle.penalty_for_late,
        "total_collected": circle.total_collected,
        "insurance_pool_balance": circle.insurance_pool_balance,
        "members": [{
            "user_id": m.user_id,
            "role": m.role.value,
            "position": m.position,
            "has_paid_current_cycle": m.has_paid_current_cycle,
            "joined_at": m.joined_at.isoformat()
        } for m in circle.members],
        "cycles": [{
            "cycle_number": c.cycle_number,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "payout_to": c.payout_to,
            "total_collected": c.total_collected,
            "status": c.status
        } for c in circle.cycles],
        "current_cycle": circle.cycles[-1].cycle_number if circle.cycles else None,
        "created_at": circle.created_at.isoformat()
    }

@router.post("/circles/{circle_id}/join", response_model=dict)
async def join_circle(circle_id: str, user: dict = Depends(get_current_user)):
    circle = store.add_member(circle_id, user["id"])
    if not circle:
        raise HTTPException(status_code=400, detail="Could not join circle")
    
    return {
        "message": "Joined successfully",
        "circle_status": circle.status.value,
        "member_count": len(circle.members)
    }

@router.post("/circles/{circle_id}/pay", response_model=dict)
async def make_payment(circle_id: str, payment_data: PaymentCreate, user: dict = Depends(get_current_user)):
    circle = store.circles.get(circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    
    payment = store.process_payment(payment_data, user["id"])
    
    return {
        "payment_id": payment.id,
        "status": payment.status.value,
        "amount": payment.amount,
        "provider": payment.provider.value,
        "transaction_id": payment.transaction_id,
        "message": f"Payment of GHS {payment.amount} processed via {payment.provider.value}"
    }

@router.get("/circles/{circle_id}/schedule", response_model=List[dict])
async def get_schedule(circle_id: str, user: dict = Depends(get_current_user)):
    circle = store.circles.get(circle_id)
    if not circle or not any(m.user_id == user["id"] for m in circle.members):
        raise HTTPException(status_code=404, detail="Circle not found")
    
    members_sorted = sorted(circle.members, key=lambda m: m.position or 999)
    return [{
        "position": i + 1,
        "user_id": m.user_id,
        "role": m.role.value,
        "estimated_payout_date": (circle.created_at + timedelta(days=circle.cycle_length_days * (i + 1))).isoformat()
    } for i, m in enumerate(members_sorted)]

@router.get("/credit-score", response_model=dict)
async def get_credit_score(user: dict = Depends(get_current_user)):
    cs = store.get_credit_score(user["id"])
    return {
        "score": cs.score,
        "rating": _get_score_rating(cs.score),
        "circles_completed": cs.circles_completed,
        "on_time_payments": cs.on_time_payments,
        "late_payments": cs.late_payments,
        "defaulted_circles": cs.defaulted_circles,
        "last_updated": cs.last_updated.isoformat()
    }

def _get_score_rating(score: int) -> str:
    if score >= 750:
        return "Excellent"
    if score >= 670:
        return "Good"
    if score >= 580:
        return "Fair"
    if score >= 500:
        return "Average"
    return "Poor"

@router.post("/roundup", response_model=dict)
async def create_roundup_rule(rule: RoundUpRule, user: dict = Depends(get_current_user)):
    store.roundup_rules[user["id"]] = rule
    return {
        "message": "Round-up rule created",
        "round_to": rule.round_to,
        "active": rule.active
    }

@router.get("/roundup", response_model=dict)
async def get_roundup_rule(user: dict = Depends(get_current_user)):
    rule = store.roundup_rules.get(user["id"])
    if not rule:
        return {"active": False, "total_accumulated": 0.0}
    return {
        "active": rule.active,
        "round_to": rule.round_to,
        "total_accumulated": rule.total_accumulated
    }

@router.get("/dashboard", response_model=dict)
async def get_dashboard(user: dict = Depends(get_current_user)):
    circles = store.get_user_circles(user["id"])
    cs = store.get_credit_score(user["id"])
    rule = store.roundup_rules.get(user["id"])
    
    active_circles = [c for c in circles if c.status == SusuStatus.ACTIVE]
    pending_circles = [c for c in circles if c.status == SusuStatus.PENDING]
    
    return {
        "user_id": user["id"],
        "credit_score": {
            "score": cs.score,
            "rating": _get_score_rating(cs.score)
        },
        "circles": {
            "active": len(active_circles),
            "pending": len(pending_circles),
            "total": len(circles)
        },
        "total_saved": sum(c.total_collected for c in circles),
        "roundup_accumulated": rule.total_accumulated if rule else 0.0,
        "upcoming_payments": [
            {
                "circle_name": c.name,
                "amount": c.contribution_amount,
                "due_in_days": max(0, (c.cycles[-1].end_date - datetime.now(timezone.utc)).days) if c.cycles else 0
            }
            for c in active_circles
        ]
    }
