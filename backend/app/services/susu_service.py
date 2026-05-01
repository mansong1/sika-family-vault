from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import uuid
import random
from app.models.susu import (
    SusuCircle, SusuCircleCreate, CircleMember, MemberRole,
    SusuCycle, SusuStatus, Payment, PaymentCreate, PaymentStatus,
    CreditScore, RoundUpRule
)

# In-memory store for MVP - would be Supabase/Postgres in production
class InMemoryStore:
    def __init__(self):
        self.circles: Dict[str, SusuCircle] = {}
        self.users: Dict[str, dict] = {}
        self.payments: Dict[str, Payment] = {}
        self.credit_scores: Dict[str, CreditScore] = {}
        self.roundup_rules: Dict[str, RoundUpRule] = {}

    def create_circle(self, circle_data: SusuCircleCreate, admin_id: str) -> SusuCircle:
        circle_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        circle = SusuCircle(
            id=circle_id,
            **circle_data.dict(),
            status=SusuStatus.PENDING,
            admin_id=admin_id,
            members=[CircleMember(
                user_id=admin_id,
                role=MemberRole.ADMIN,
                position=None,
                joined_at=now
            )],
            cycles=[],
            total_collected=0.0,
            insurance_pool_balance=circle_data.contribution_amount * 0.02,  # 2% insurance fee
            created_at=now,
            updated_at=now
        )
        self.circles[circle_id] = circle
        return circle

    def add_member(self, circle_id: str, user_id: str) -> Optional[SusuCircle]:
        circle = self.circles.get(circle_id)
        if not circle:
            return None
        if len(circle.members) >= circle.max_members:
            return None
        if any(m.user_id == user_id for m in circle.members):
            return circle
        
        circle.members.append(CircleMember(
            user_id=user_id,
            role=MemberRole.MEMBER,
            position=None,
            joined_at=datetime.now(timezone.utc)
        ))
        
        # If circle is full, generate rotation and start
        if len(circle.members) == circle.max_members:
            self._generate_rotation(circle)
            self._start_first_cycle(circle)
            circle.status = SusuStatus.ACTIVE
        
        circle.updated_at = datetime.now(timezone.utc)
        return circle

    def _generate_rotation(self, circle: SusuCircle):
        member_ids = [m.user_id for m in circle.members]
        random.seed(circle.id)  # Deterministic but fair
        shuffled = member_ids.copy()
        random.shuffle(shuffled)
        for i, member in enumerate(circle.members):
            member.position = shuffled.index(member.user_id)

    def _start_first_cycle(self, circle: SusuCircle):
        now = datetime.now(timezone.utc)
        cycle = SusuCycle(
            cycle_number=1,
            start_date=now,
            end_date=now + timedelta(days=circle.cycle_length_days),
            payout_to=min(circle.members, key=lambda m: m.position or 999).user_id,
            total_collected=0.0,
            status="active"
        )
        circle.cycles.append(cycle)

    def advance_cycle(self, circle_id: str) -> Optional[SusuCircle]:
        circle = self.circles.get(circle_id)
        if not circle or circle.status != SusuStatus.ACTIVE:
            return None
        
        current_cycle = circle.cycles[-1] if circle.cycles else None
        if not current_cycle:
            return circle
        
        # Mark cycle complete
        current_cycle.status = "completed"
        current_cycle.total_collected = circle.total_collected
        
        # Start next cycle
        next_position = (current_cycle.cycle_number % len(circle.members))
        members_sorted = sorted(circle.members, key=lambda m: m.position or 999)
        next_payout = members_sorted[next_position].user_id
        
        new_cycle = SusuCycle(
            cycle_number=current_cycle.cycle_number + 1,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=circle.cycle_length_days),
            payout_to=next_payout,
            total_collected=0.0,
            status="active"
        )
        circle.cycles.append(new_cycle)
        
        # Reset payment flags
        for member in circle.members:
            member.has_paid_current_cycle = False
        
        circle.total_collected = 0.0
        circle.updated_at = datetime.now(timezone.utc)
        return circle

    def process_payment(self, payment_data: PaymentCreate, user_id: str) -> Payment:
        payment_id = str(uuid.uuid4())
        payment = Payment(
            id=payment_id,
            circle_id=payment_data.circle_id,
            user_id=user_id,
            amount=payment_data.amount,
            provider=payment_data.provider,
            phone_number=payment_data.phone_number,
            status=PaymentStatus.COMPLETED,
            transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",
            created_at=datetime.now(timezone.utc)
        )
        self.payments[payment_id] = payment
        
        # Update circle total
        circle = self.circles.get(payment_data.circle_id)
        if circle:
            circle.total_collected += payment_data.amount
            for member in circle.members:
                if member.user_id == user_id:
                    member.has_paid_current_cycle = True
            
            # Update credit score
            self._update_credit_score(user_id, on_time=True)
        
        return payment

    def _update_credit_score(self, user_id: str, on_time: bool = True):
        cs = self.credit_scores.get(user_id)
        if not cs:
            cs = CreditScore(
                user_id=user_id,
                score=500,
                circles_completed=0,
                on_time_payments=0,
                late_payments=0,
                defaulted_circles=0,
                last_updated=datetime.now(timezone.utc)
            )
            self.credit_scores[user_id] = cs
        
        cs.last_updated = datetime.now(timezone.utc)
        if on_time:
            cs.on_time_payments += 1
            cs.score = min(850, cs.score + 5)
        else:
            cs.late_payments += 1
            cs.score = max(300, cs.score - 15)

    def get_credit_score(self, user_id: str) -> CreditScore:
        if user_id not in self.credit_scores:
            return CreditScore(
                user_id=user_id,
                score=500,
                circles_completed=0,
                on_time_payments=0,
                late_payments=0,
                defaulted_circles=0,
                last_updated=datetime.now(timezone.utc)
            )
        return self.credit_scores[user_id]

    def get_user_circles(self, user_id: str) -> List[SusuCircle]:
        return [
            c for c in self.circles.values()
            if any(m.user_id == user_id for m in c.members)
        ]

store = InMemoryStore()
