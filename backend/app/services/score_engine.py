"""SusuScore™ — Alternative Credit Scoring Engine

Scores informal savings group participation into a FICO-compatible credit score.
The first credit scoring model built exclusively for West African rotating savings.

Score Range: 300–850
Model: Weighted multi-factor from Susu circle behavioral data
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum


class ScoreTier(str, Enum):
    EXCELLENT = "Excellent"       # 800–850
    VERY_GOOD = "Very Good"       # 740–799
    GOOD = "Good"                  # 670–739
    FAIR = "Fair"                  # 580–669
    NEEDS_IMPROVEMENT = "Needs Improvement"  # 300–579

    @classmethod
    def from_score(cls, score: int) -> "ScoreTier":
        if score >= 800:
            return cls.EXCELLENT
        if score >= 740:
            return cls.VERY_GOOD
        if score >= 670:
            return cls.GOOD
        if score >= 580:
            return cls.FAIR
        return cls.NEEDS_IMPROVEMENT


@dataclass
class ScoreFactor:
    """Individual factor contribution to the total score."""
    name: str
    raw_value: float
    normalized: float          # 0–1
    weight: float              # 0–1
    weighted_contribution: float  # normalized * weight
    max_possible: float        # theoretical max for this factor
    description: str


@dataclass
class SusuScoreBreakdown:
    """Complete score calculation with factor-level detail."""
    user_id: str
    total_score: int
    tier: ScoreTier
    factors: List[ScoreFactor]
    trend: Optional[str] = None      # "up", "down", "stable"
    last_calculated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def summary(self) -> str:
        return (
            f"SusuScore: {self.total_score} ({self.tier.value}) | "
            f"{self._get_top_driver()}"
        )

    def _get_top_driver(self) -> str:
        if not self.factors:
            return "No data"
        best = max(self.factors, key=lambda f: f.weighted_contribution)
        return f"Top driver: {best.name}"


class SusuScoreEngine:
    """
    Computes SusuScore from Susu circle participation data.

    The model evaluates 6 factors, each normalized to 0–1 and weighted:
    1. On-time contribution rate (30%) — most predictive
    2. Streak length in consecutive cycles (20%) — long-term discipline
    3. Circle size and role (15%) — social accountability
    4. Contribution amount consistency (15%) — income stability
    5. Default/delinquency history (15%) — negative signals
    6. Circle completion rate (5%) — commitment follow-through
    """

    BASE_SCORE = 300
    MAX_SCORE = 850
    SCORE_RANGE = MAX_SCORE - BASE_SCORE  # 550

    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        "on_time_rate": 0.30,
        "streak_length": 0.20,
        "circle_participation": 0.15,
        "amount_consistency": 0.15,
        "default_history": 0.15,
        "completion_rate": 0.05,
    }

    def __init__(self):
        # Configuration
        self.max_streak_for_full = 24      # 24 cycles (2 years) = max streak score
        self.max_amount_variance = 0.50     # 50%+ variance = min consistency
        self.default_penalty_per_event = 0.30  # each default drops factor by 30%
        self.late_penalty_per_event = 0.05     # each late payment drops factor by 5%
        self.ideal_circle_size = 10            # circles of 10+ get full participation score

    def calculate(
        self,
        user_id: str,
        on_time_payments: int,
        total_payments: int,
        streak_months: int,
        circles_joined: int,
        circles_completed: int,
        circles_defaulted: int,
        contribution_amounts: List[float],
        is_admin_count: int = 0,
        largest_circle_size: int = 0,
    ) -> SusuScoreBreakdown:
        """Calculate the full SusuScore from raw participation data."""

        factors: List[ScoreFactor] = []

        # 1. On-time contribution rate (30%)
        ot_rate = on_time_payments / max(total_payments, 1)
        factors.append(ScoreFactor(
            name="On-time Contributions",
            raw_value=ot_rate,
            normalized=ot_rate,
            weight=self.WEIGHTS["on_time_rate"],
            weighted_contribution=ot_rate * self.WEIGHTS["on_time_rate"],
            max_possible=self.WEIGHTS["on_time_rate"],
            description=f"{on_time_payments} of {total_payments} payments on time ({ot_rate:.0%})"
        ))

        # 2. Streak length (20%) — capped at max_streak_for_full cycles
        streak_norm = min(streak_months / self.max_streak_for_full, 1.0)
        factors.append(ScoreFactor(
            name="Savings Streak",
            raw_value=streak_months,
            normalized=streak_norm,
            weight=self.WEIGHTS["streak_length"],
            weighted_contribution=streak_norm * self.WEIGHTS["streak_length"],
            max_possible=self.WEIGHTS["streak_length"],
            description=f"{streak_months} consecutive months of participation"
        ))

        # 3. Circle participation & role (15%)
        # Combines: number of circles + leadership role + largest circle size
        role_bonus = min(is_admin_count * 0.1, 0.2)  # up to 20% bonus for admin roles
        size_factor = min(largest_circle_size / self.ideal_circle_size, 1.0)
        participation_norm = min(circles_joined / 3, 1.0) * 0.5 + size_factor * 0.5 + role_bonus
        participation_norm = min(participation_norm, 1.0)
        factors.append(ScoreFactor(
            name="Circle Participation",
            raw_value=circles_joined,
            normalized=participation_norm,
            weight=self.WEIGHTS["circle_participation"],
            weighted_contribution=participation_norm * self.WEIGHTS["circle_participation"],
            max_possible=self.WEIGHTS["circle_participation"],
            description=f"Active in {circles_joined} circles{' (admin)' if is_admin_count > 0 else ''}"
        ))

        # 4. Amount consistency (15%)
        if len(contribution_amounts) >= 3:
            mean = sum(contribution_amounts) / len(contribution_amounts)
            if mean > 0:
                variance = sum((a - mean) ** 2 for a in contribution_amounts) / len(contribution_amounts)
                cv = (variance ** 0.5) / mean  # coefficient of variation
                consistency_norm = max(0, 1.0 - (cv / self.max_amount_variance))
            else:
                consistency_norm = 0.0
        else:
            consistency_norm = 0.5  # neutral — not enough data

        factors.append(ScoreFactor(
            name="Contribution Consistency",
            raw_value=round(consistency_norm, 2),
            normalized=consistency_norm,
            weight=self.WEIGHTS["amount_consistency"],
            weighted_contribution=consistency_norm * self.WEIGHTS["amount_consistency"],
            max_possible=self.WEIGHTS["amount_consistency"],
            description=f"{'Stable' if consistency_norm > 0.7 else 'Variable'} contribution amounts"
        ))

        # 5. Default/delinquency history (15%) — inverted: clean = 1.0
        default_penalty = circles_defaulted * self.default_penalty_per_event
        # Apply late payment penalties to on-time rate factor
        late_penalty = max(0, total_payments - on_time_payments) * self.late_penalty_per_event
        default_norm = max(0, 1.0 - default_penalty - late_penalty)
        factors.append(ScoreFactor(
            name="Payment History",
            raw_value=circles_defaulted + (total_payments - on_time_payments),
            normalized=default_norm,
            weight=self.WEIGHTS["default_history"],
            weighted_contribution=default_norm * self.WEIGHTS["default_history"],
            max_possible=self.WEIGHTS["default_history"],
            description=f"{circles_defaulted} defaults, {total_payments - on_time_payments} late payments"
        ))

        # 6. Circle completion rate (5%)
        total_circles = circles_completed + circles_defaulted
        complete_norm = circles_completed / max(total_circles, 1)
        factors.append(ScoreFactor(
            name="Circle Completion",
            raw_value=complete_norm,
            normalized=complete_norm,
            weight=self.WEIGHTS["completion_rate"],
            weighted_contribution=complete_norm * self.WEIGHTS["completion_rate"],
            max_possible=self.WEIGHTS["completion_rate"],
            description=f"{circles_completed} completed of {total_circles} total circles"
        ))

        # Compute total score
        total_norm = sum(f.weighted_contribution for f in factors)
        total_score = int(self.BASE_SCORE + (total_norm * self.SCORE_RANGE))
        total_score = max(self.BASE_SCORE, min(self.MAX_SCORE, total_score))

        # Determine trend based on recent factors vs baseline
        trend = self._compute_trend(factors)

        return SusuScoreBreakdown(
            user_id=user_id,
            total_score=total_score,
            tier=ScoreTier.from_score(total_score),
            factors=factors,
            trend=trend,
        )

    def calculate_from_store(self, user_id: str, store) -> SusuScoreBreakdown:
        """Convenience method: extract data from the in-memory store and calculate."""
        circles = store.get_user_circles(user_id)
        cs = store.get_credit_score(user_id)

        # Gather payment history from circles
        on_time = cs.on_time_payments if cs else 0
        total = cs.on_time_payments + cs.late_payments if cs else 0
        streak = cs.circles_completed if cs else 0  # approximate

        circles_joined = len(circles)
        circles_completed = sum(1 for c in circles if c.status.value == "completed")
        circles_defaulted = cs.defaulted_circles if cs else 0

        contribution_amounts = [c.contribution_amount for c in circles]
        is_admin = sum(1 for c in circles if any(m.user_id == user_id and m.role.value == "admin" for m in c.members))
        largest = max((len(c.members) for c in circles), default=0)

        return self.calculate(
            user_id=user_id,
            on_time_payments=max(on_time, 0),
            total_payments=max(total, 1),
            streak_months=streak,
            circles_joined=circles_joined,
            circles_completed=max(circles_completed, 0),
            circles_defaulted=max(circles_defaulted, 0),
            contribution_amounts=contribution_amounts if contribution_amounts else [100.0],
            is_admin_count=is_admin,
            largest_circle_size=largest,
        )

    def get_improvement_tips(self, breakdown: SusuScoreBreakdown) -> List[str]:
        """Generate actionable improvement tips based on the score breakdown."""
        tips = []
        for factor in sorted(breakdown.factors, key=lambda f: f.weighted_contribution):
            if factor.weighted_contribution < factor.max_possible * 0.6:
                if factor.name == "On-time Contributions":
                    tips.append("💡 Enable auto-pay to make every contribution on time. Your circle will thank you.")
                elif factor.name == "Savings Streak":
                    tips.append("🔥 Stay in your circle for at least 6 more cycles to build a strong streak.")
                elif factor.name == "Circle Participation":
                    tips.append("👥 Join 1-2 more circles or volunteer as circle admin to boost your score.")
                elif factor.name == "Contribution Consistency":
                    tips.append("📊 Keep your contribution amounts steady — inconsistent amounts signal income instability.")
                elif factor.name == "Payment History":
                    tips.append("⚠️ Avoid defaults at all costs. Set reminders 2 days before payment is due.")
                elif factor.name == "Circle Completion":
                    tips.append("🏁 Complete your current circles — every finished circle adds to your score.")
        if not tips:
            tips.append("🎉 Your score is in great shape! Keep up the consistency and consider becoming a circle admin.")
        return tips[:3]  # Top 3 most impactful

    def _compute_trend(self, factors: List[ScoreFactor]) -> str:
        """Heuristic trend based on factor utilization."""
        avg_utilization = sum(
            f.weighted_contribution / max(f.max_possible, 0.01) for f in factors
        ) / max(len(factors), 1)
        if avg_utilization > 0.8:
            return "up"
        if avg_utilization < 0.4:
            return "down"
        return "stable"


# Singleton
score_engine = SusuScoreEngine()
