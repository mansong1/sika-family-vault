"""Round-Up Engine — spare change automation for Sika Bank Susu circles"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict
from math import ceil

from ..models.round_up import (
    RoundUpRule, RoundUpRuleCreate, RoundUpRuleUpdate,
    RoundUpTransaction, CircleRoundUpStats,
)


class RoundUpEngine:
    """Calculates spare change, enforces limits, sweeps into Susu circles."""

    def __init__(self, store):
        self.store = store
        # Ensure round-up storage exists on the in-memory store
        if not hasattr(store, "roundup_rules"):
            store.roundup_rules: Dict[str, RoundUpRule] = {}
        if not hasattr(store, "roundup_transactions"):
            store.roundup_transactions: List[RoundUpTransaction] = []

    # ── Calculation ──────────────────────────────────────────────

    def calculate_spare_change(
        self,
        purchase_amount: float,
        round_to: float = 1.0,
        multiplier: int = 1,
    ) -> Tuple[float, float]:
        """
        Calculate spare change from a purchase.
        Returns (spare_change, rounded_amount).
        Example: purchase 2.50, round_to 1.0 → (0.50, 3.00)
                 purchase 2.50, round_to 1.0, multiplier 2 → (1.00, 3.00)
        """
        if purchase_amount <= 0:
            return (0.0, purchase_amount)

        # Round up to nearest round_to unit
        rounded = ceil(purchase_amount / round_to) * round_to
        base_spare = round(rounded - purchase_amount, 2)

        # Apply multiplier
        spare_change = round(base_spare * multiplier, 2)

        return (spare_change, rounded)

    # ── Validation ───────────────────────────────────────────────

    def should_sweep(
        self,
        user_id: str,
        rule: RoundUpRule,
        spare_change: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a sweep should proceed.
        Returns (should_proceed, reason_if_blocked).
        """
        # 1. Rule active?
        if not rule.active:
            return (False, "Rule is inactive")

        # 2. Paused?
        if rule.is_paused():
            return (False, f"Rule paused until {rule.paused_until.isoformat()}")

        # 3. Floor amount?
        if spare_change < rule.floor_amount:
            return (False, f"Spare change {spare_change} below floor {rule.floor_amount}")

        # 4. Weekly cap?
        if rule.weekly_cap is not None:
            week_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # Adjust to Monday
            days_since_monday = week_start.weekday()
            monday = week_start - timedelta(days=days_since_monday)

            weekly_total = sum(
                t.spare_change
                for t in self.store.roundup_transactions
                if t.user_id == user_id and t.swept_at >= monday
            )
            if weekly_total + spare_change > rule.weekly_cap:
                return (
                    False,
                    f"Weekly cap of GHS {rule.weekly_cap} would be exceeded "
                    f"(current: {weekly_total}, adding: {spare_change})",
                )

        # 5. Balance check — ensure user has enough in their wallet
        # (In production, this queries the actual bank balance)
        user = self.store.users.get(user_id)
        if user and user.get("balance", 0) < (spare_change + 5.0):
            return (False, "Insufficient balance buffer")

        return (True, None)

    # ── Sweep ────────────────────────────────────────────────────

    def sweep_to_circle(
        self,
        user_id: str,
        rule: RoundUpRule,
        purchase_amount: float,
        spare_change: float,
        rounded_amount: float,
    ) -> RoundUpTransaction:
        """Execute a sweep: record transaction, update totals."""
        txn = RoundUpTransaction(
            user_id=user_id,
            circle_id=rule.circle_id,
            rule_id=rule.rule_id,
            purchase_amount=purchase_amount,
            rounded_amount=rounded_amount,
            spare_change=spare_change,
            multiplier_applied=rule.multiplier,
            swept_at=datetime.now(timezone.utc),
        )

        self.store.roundup_transactions.append(txn)

        # Update rule accumulated total
        rule.total_accumulated += spare_change

        # Update circle total
        circle = self.store.circles.get(rule.circle_id)
        if circle:
            circle.total_collected += spare_change

        return txn

    # ── Process purchase (full pipeline) ─────────────────────────

    def process_purchase(
        self,
        user_id: str,
        purchase_amount: float,
        circle_id: str,
    ) -> dict:
        """Full round-up pipeline for a purchase. Returns result dict."""
        rule = self._get_active_rule_for_circle(user_id, circle_id)

        if not rule:
            return {
                "swept": False,
                "reason": "No active rule for this circle",
                "spare_change": 0.0,
            }

        spare_change, rounded_amount = self.calculate_spare_change(
            purchase_amount, rule.round_to, rule.multiplier
        )

        should_proceed, block_reason = self.should_sweep(user_id, rule, spare_change)

        if not should_proceed:
            return {
                "swept": False,
                "reason": block_reason,
                "spare_change": spare_change,
                "rounded_amount": rounded_amount,
            }

        txn = self.sweep_to_circle(
            user_id, rule, purchase_amount, spare_change, rounded_amount
        )

        return {
            "swept": True,
            "transaction_id": txn.id,
            "spare_change": spare_change,
            "rounded_amount": rounded_amount,
            "rule_id": rule.rule_id,
            "circle_id": circle_id,
        }

    # ── Simulation ───────────────────────────────────────────────

    def simulate(self, user_id: str, purchase_amount: float, circle_id: str) -> dict:
        """Simulate what would happen without executing."""
        rule = self._get_active_rule_for_circle(user_id, circle_id)

        if not rule:
            return {
                "swept": False,
                "reason": "No active rule for this circle",
                "spare_change": 0.0,
                "purchase_amount": purchase_amount,
            }

        spare_change, rounded_amount = self.calculate_spare_change(
            purchase_amount, rule.round_to, rule.multiplier
        )

        should_proceed, block_reason = self.should_sweep(user_id, rule, spare_change)

        return {
            "swept": should_proceed,
            "reason": block_reason,
            "purchase_amount": purchase_amount,
            "rounded_amount": rounded_amount,
            "spare_change": spare_change,
            "multiplier": rule.multiplier,
            "round_to": rule.round_to,
            "floor_amount": rule.floor_amount,
            "weekly_cap": rule.weekly_cap,
            "circle_id": circle_id,
        }

    # ── Rule Management ──────────────────────────────────────────

    def create_rule(self, data: RoundUpRuleCreate) -> RoundUpRule:
        rule = RoundUpRule(
            user_id=data.user_id,
            circle_id=data.circle_id,
            round_to=data.round_to,
            multiplier=data.multiplier,
            floor_amount=data.floor_amount,
            weekly_cap=data.weekly_cap,
            allocation_pct=data.allocation_pct,
        )
        self.store.roundup_rules[rule.rule_id] = rule
        return rule

    def get_user_rules(self, user_id: str) -> List[RoundUpRule]:
        return [
            r
            for r in self.store.roundup_rules.values()
            if r.user_id == user_id
        ]

    def get_user_rules_for_circle(self, user_id: str, circle_id: str) -> List[RoundUpRule]:
        return [
            r
            for r in self.store.roundup_rules.values()
            if r.user_id == user_id and r.circle_id == circle_id
        ]

    def _get_active_rule_for_circle(
        self, user_id: str, circle_id: str
    ) -> Optional[RoundUpRule]:
        rules = self.get_user_rules_for_circle(user_id, circle_id)
        active = [r for r in rules if r.active and not r.is_paused()]
        return active[0] if active else None

    def get_rule(self, rule_id: str) -> Optional[RoundUpRule]:
        return self.store.roundup_rules.get(rule_id)

    def update_rule(self, rule_id: str, data: RoundUpRuleUpdate) -> Optional[RoundUpRule]:
        rule = self.store.roundup_rules.get(rule_id)
        if not rule:
            return None

        update_dict = data.model_dump(exclude_unset=True)

        # Handle pause/resume
        if "paused_until" in update_dict:
            if update_dict["paused_until"] is None:
                rule.paused_until = None  # Resume
            else:
                rule.paused_until = update_dict["paused_until"]  # Pause until date
            del update_dict["paused_until"]

        for field, value in update_dict.items():
            setattr(rule, field, value)

        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self.store.roundup_rules:
            del self.store.roundup_rules[rule_id]
            return True
        return False

    # ── Stats & History ──────────────────────────────────────────

    def get_transactions(
        self, user_id: str, circle_id: Optional[str] = None, limit: int = 20
    ) -> List[RoundUpTransaction]:
        txns = [t for t in self.store.roundup_transactions if t.user_id == user_id]
        if circle_id:
            txns = [t for t in txns if t.circle_id == circle_id]
        txns.sort(key=lambda t: t.swept_at, reverse=True)
        return txns[:limit]

    def get_circle_stats(self, circle_id: str) -> CircleRoundUpStats:
        """Aggregate round-up stats for a circle."""
        txns = [
            t for t in self.store.roundup_transactions if t.circle_id == circle_id
        ]

        circle_name = ""
        circle = self.store.circles.get(circle_id)
        if circle:
            circle_name = circle.name

        total_spare = round(sum(t.spare_change for t in txns), 2)

        # Member leaderboard
        leaderboard: Dict[str, dict] = {}
        for t in txns:
            if t.user_id not in leaderboard:
                leaderboard[t.user_id] = {"user_id": t.user_id, "total": 0.0, "sweeps": 0}
            leaderboard[t.user_id]["total"] = round(
                leaderboard[t.user_id]["total"] + t.spare_change, 2
            )
            leaderboard[t.user_id]["sweeps"] += 1

        sorted_leaderboard = sorted(
            leaderboard.values(), key=lambda x: x["total"], reverse=True
        )

        # Recent sweeps (last 10)
        recent = sorted(txns, key=lambda t: t.swept_at, reverse=True)[:10]

        return CircleRoundUpStats(
            circle_id=circle_id,
            circle_name=circle_name,
            total_spare_change=total_spare,
            total_sweeps=len(txns),
            member_leaderboard=sorted_leaderboard,
            recent_sweeps=[
                {
                    "id": t.id,
                    "user_id": t.user_id,
                    "spare_change": t.spare_change,
                    "purchase_amount": t.purchase_amount,
                    "multiplier": t.multiplier_applied,
                    "swept_at": t.swept_at.isoformat(),
                }
                for t in recent
            ],
        )
