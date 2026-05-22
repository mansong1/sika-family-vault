from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from ..models.susu import (
    SusuCircleCreate, SusuStatus, PaymentCreate, CreditScore, UserCreate, Token, LoginRequest
)
from ..models.round_up import (
    RoundUpRuleCreate, RoundUpRuleUpdate, RoundUpSweepRequest,
    RoundUpSimulateRequest,
)
from ..services.susu_service import store
from ..services.round_up_service import RoundUpEngine
from ..services.score_engine import score_engine
from ..core.security import create_access_token, verify_password, get_password_hash

# Initialize round-up engine
roundup_engine = RoundUpEngine(store)

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
    breakdown = score_engine.calculate_from_store(user["id"], store)
    cs = store.get_credit_score(user["id"])

    return {
        "score": breakdown.total_score,
        "tier": breakdown.tier.value,
        "trend": breakdown.trend,
        "factors": [{
            "name": f.name,
            "normalized": round(f.normalized, 3),
            "weight": f.weight,
            "contribution": round(f.weighted_contribution, 4),
            "description": f.description,
        } for f in breakdown.factors],
        "improvement_tips": score_engine.get_improvement_tips(breakdown),
        "circles_completed": cs.circles_completed,
        "on_time_payments": cs.on_time_payments,
        "late_payments": cs.late_payments,
        "defaulted_circles": cs.defaulted_circles,
        "last_updated": cs.last_updated.isoformat() if cs.last_updated else None,
        "last_calculated": breakdown.last_calculated.isoformat(),
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


@router.get("/credit-score/history", response_model=dict)
async def get_credit_score_history(user: dict = Depends(get_current_user)):
    """Get score history for trend visualization."""
    cs = store.get_credit_score(user["id"])
    history = getattr(cs, "history", [])
    if not history:
        # Generate synthetic history based on metrics for demo
        history = _generate_score_history(cs)

    return {
        "current_score": cs.score,
        "history": history,
    }


def _generate_score_history(cs) -> list:
    """Generate a reasonable score history from available metrics."""
    import random
    from datetime import datetime, timezone, timedelta

    points = []
    base_score = max(300, cs.score - cs.circles_completed * 15)
    now = datetime.now(timezone.utc)

    for i in range(max(1, cs.circles_completed)):
        progress = (i + 1) / max(cs.circles_completed, 1)
        score = int(base_score + (cs.score - base_score) * progress)
        score += random.randint(-10, 10)  # small jitter
        score = max(300, min(850, score))
        points.append({
            "date": (now - timedelta(days=30 * (cs.circles_completed - i))).isoformat(),
            "score": score,
        })

    # Add current
    points.append({
        "date": now.isoformat(),
        "score": cs.score,
    })
    return points

# ═══════════════════════════════════════════════════════════
# Auto Round-Up Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/round-up/rules", response_model=dict)
async def create_roundup_rule(data: RoundUpRuleCreate, user: dict = Depends(get_current_user)):
    """Create a new round-up rule for a Susu circle"""
    data.user_id = user["id"]
    rule = roundup_engine.create_rule(data)
    return {
        "rule_id": rule.rule_id,
        "circle_id": rule.circle_id,
        "round_to": rule.round_to,
        "multiplier": rule.multiplier,
        "active": rule.active,
        "message": "Round-up rule created",
    }


@router.get("/round-up/rules", response_model=dict)
async def get_roundup_rules(user: dict = Depends(get_current_user)):
    """Get all round-up rules for the current user"""
    rules = roundup_engine.get_user_rules(user["id"])
    return {
        "rules": [
            {
                "rule_id": r.rule_id,
                "circle_id": r.circle_id,
                "active": r.active,
                "paused": r.is_paused(),
                "paused_until": r.paused_until.isoformat() if r.paused_until else None,
                "round_to": r.round_to,
                "multiplier": r.multiplier,
                "floor_amount": r.floor_amount,
                "weekly_cap": r.weekly_cap,
                "allocation_pct": r.allocation_pct,
                "total_accumulated": r.total_accumulated,
                "created_at": r.created_at.isoformat(),
            }
            for r in rules
        ]
    }


@router.patch("/round-up/rules/{rule_id}", response_model=dict)
async def update_roundup_rule(
    rule_id: str, data: RoundUpRuleUpdate, user: dict = Depends(get_current_user)
):
    """Update a round-up rule (toggle, pause, change multiplier, etc.)"""
    rule = roundup_engine.get_rule(rule_id)
    if not rule or rule.user_id != user["id"]:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    updated = roundup_engine.update_rule(rule_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "rule_id": updated.rule_id,
        "active": updated.active,
        "paused": updated.is_paused(),
        "multiplier": updated.multiplier,
        "round_to": updated.round_to,
        "message": "Rule updated",
    }


@router.delete("/round-up/rules/{rule_id}", response_model=dict)
async def delete_roundup_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Delete a round-up rule"""
    rule = roundup_engine.get_rule(rule_id)
    if not rule or rule.user_id != user["id"]:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    roundup_engine.delete_rule(rule_id)
    return {"message": "Rule deleted", "rule_id": rule_id}


@router.get("/round-up/transactions", response_model=dict)
async def get_roundup_transactions(
    circle_id: str = None, user: dict = Depends(get_current_user)
):
    """Get round-up transaction history, optionally filtered by circle"""
    txns = roundup_engine.get_transactions(user["id"], circle_id)
    return {
        "transactions": [
            {
                "id": t.id,
                "circle_id": t.circle_id,
                "purchase_amount": t.purchase_amount,
                "rounded_amount": t.rounded_amount,
                "spare_change": t.spare_change,
                "multiplier": t.multiplier_applied,
                "swept_at": t.swept_at.isoformat(),
                "source_tx_id": t.source_tx_id,
            }
            for t in txns
        ]
    }


@router.post("/round-up/simulate", response_model=dict)
async def simulate_roundup(data: RoundUpSimulateRequest, user: dict = Depends(get_current_user)):
    """Simulate a round-up without executing it"""
    result = roundup_engine.simulate(user["id"], data.purchase_amount, data.circle_id)
    return result


@router.post("/round-up/sweep", response_model=dict)
async def trigger_sweep(data: RoundUpSweepRequest, user: dict = Depends(get_current_user)):
    """Manually trigger a round-up sweep (for demo/testing)"""
    result = roundup_engine.process_purchase(
        user["id"], data.purchase_amount, data.circle_id
    )
    return result


@router.get("/round-up/circle-stats/{circle_id}", response_model=dict)
async def get_circle_roundup_stats(circle_id: str, user: dict = Depends(get_current_user)):
    """Get aggregate round-up statistics for a Susu circle"""
    circle = store.circles.get(circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    
    stats = roundup_engine.get_circle_stats(circle_id)
    return {
        "circle_id": stats.circle_id,
        "circle_name": stats.circle_name,
        "total_spare_change": stats.total_spare_change,
        "total_sweeps": stats.total_sweeps,
        "member_leaderboard": stats.member_leaderboard,
        "recent_sweeps": stats.recent_sweeps,
    }

@router.get("/dashboard", response_model=dict)
async def get_dashboard(user: dict = Depends(get_current_user)):
    circles = store.get_user_circles(user["id"])
    cs = store.get_credit_score(user["id"])
    all_roundup_rules = roundup_engine.get_user_rules(user["id"])
    total_roundup = sum(r.total_accumulated for r in all_roundup_rules)
    
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
        "roundup_accumulated": total_roundup,
        "upcoming_payments": [
            {
                "circle_name": c.name,
                "amount": c.contribution_amount,
                "due_in_days": max(0, (c.cycles[-1].end_date - datetime.now(timezone.utc)).days) if c.cycles else 0
            }
            for c in active_circles
        ]
    }
