"""Tests for the Round-Up Engine"""

import pytest
from datetime import datetime, timezone, timedelta

from app.models.round_up import (
    RoundUpRuleCreate, RoundUpRuleUpdate, RoundUpSweepRequest,
)
from app.services.round_up_service import RoundUpEngine
from app.services.susu_service import InMemoryStore


@pytest.fixture
def store():
    s = InMemoryStore()
    s.users["test-user"] = {
        "id": "test-user",
        "email": "test@sika.bank",
        "phone": "+233501234567",
        "full_name": "Test User",
        "balance": 500.0,
    }
    # Create a test circle
    from app.models.susu import SusuCircleCreate
    circle_data = SusuCircleCreate(
        name="Test Circle",
        contribution_amount=50.0,
        cycle_length_days=30,
        max_members=5,
    )
    s.create_circle(circle_data, "test-user")
    return s


@pytest.fixture
def engine(store):
    return RoundUpEngine(store)


class TestSpareChangeCalculation:
    """Phase: spare change math"""

    def test_basic_round_to_1_ghs(self, engine):
        """Purchase GHS 2.50 round to 1 GHS → spare 0.50"""
        spare, rounded = engine.calculate_spare_change(2.50, 1.0)
        assert spare == 0.50
        assert rounded == 3.00

    def test_exact_amount_no_spare(self, engine):
        """Purchase GHS 5.00 round to 1 → no spare change"""
        spare, rounded = engine.calculate_spare_change(5.00, 1.0)
        assert spare == 0.00
        assert rounded == 5.00

    def test_round_to_5_ghs(self, engine):
        """Purchase GHS 7.00 round to 5 → spare 3.00, rounded 10.00"""
        spare, rounded = engine.calculate_spare_change(7.00, 5.0)
        assert spare == 3.00
        assert rounded == 10.00

    def test_round_to_10_ghs_small_purchase(self, engine):
        """Purchase GHS 2.00 round to 10 → spare 8.00"""
        spare, rounded = engine.calculate_spare_change(2.00, 10.0)
        assert spare == 8.00
        assert rounded == 10.00

    def test_multiplier_2x(self, engine):
        """2x multiplier doubles spare change"""
        spare, rounded = engine.calculate_spare_change(2.50, 1.0, multiplier=2)
        assert spare == 1.00
        assert rounded == 3.00

    def test_multiplier_5x(self, engine):
        """5x multiplier quintuples spare change"""
        spare, rounded = engine.calculate_spare_change(2.80, 1.0, multiplier=5)
        assert spare == 1.00
        assert rounded == 3.00

    def test_zero_purchase(self, engine):
        """Zero purchase → zero spare"""
        spare, rounded = engine.calculate_spare_change(0.0, 1.0)
        assert spare == 0.0

    def test_negative_purchase_handled(self, engine):
        """Negative amount → zero"""
        spare, rounded = engine.calculate_spare_change(-10.0, 1.0)
        assert spare == 0.0

    def test_round_to_0_5_ghs(self, engine):
        """Round to 0.5 GHS"""
        spare, rounded = engine.calculate_spare_change(2.30, 0.5, multiplier=1)
        assert spare == 0.20
        assert rounded == 2.50

    def test_large_purchase(self, engine):
        """Large purchase GHS 99.99 round to 1 → spare 0.01"""
        spare, rounded = engine.calculate_spare_change(99.99, 1.0)
        assert spare == 0.01
        assert rounded == 100.00


class TestRuleCreation:
    """Phase: rule lifecycle"""

    def test_create_rule(self, engine):
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user",
            circle_id=list(engine.store.circles.keys())[0],
            round_to=1.0,
            multiplier=1,
        ))
        assert rule.active is True
        assert rule.round_to == 1.0
        assert rule.rule_id != ""

    def test_get_user_rules(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1,
        ))
        rules = engine.get_user_rules("test-user")
        assert len(rules) == 1
        assert rules[0].circle_id == circle_id

    def test_update_rule_multiplier(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1,
        ))
        updated = engine.update_rule(rule.rule_id, RoundUpRuleUpdate(multiplier=5))
        assert updated.multiplier == 5

    def test_pause_and_resume_rule(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1,
        ))
        # Pause for 1 day
        future = datetime.now(timezone.utc) + timedelta(days=1)
        engine.update_rule(rule.rule_id, RoundUpRuleUpdate(paused_until=future))
        assert rule.is_paused() is True

        # Resume
        engine.update_rule(rule.rule_id, RoundUpRuleUpdate(paused_until=None))
        assert rule.is_paused() is False

    def test_delete_rule(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1,
        ))
        assert engine.delete_rule(rule.rule_id) is True
        assert engine.get_rule(rule.rule_id) is None


class TestSweepValidation:
    """Phase: sweep guard rails"""

    def test_floor_amount_blocks_small_spare(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1, floor_amount=0.50,
        ))
        ok, reason = engine.should_sweep("test-user", rule, 0.30)
        assert ok is False
        assert "below floor" in reason

    def test_inactive_rule_blocks_sweep(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1,
        ))
        engine.update_rule(rule.rule_id, RoundUpRuleUpdate(active=False))
        ok, reason = engine.should_sweep("test-user", rule, 1.0)
        assert ok is False
        assert "inactive" in reason.lower()

    def test_weekly_cap_blocks_excess(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1, weekly_cap=5.0,
        ))
        # Manually register a prior sweep
        from app.models.round_up import RoundUpTransaction
        txn = RoundUpTransaction(
            user_id="test-user", circle_id=circle_id, rule_id=rule.rule_id,
            purchase_amount=2.0, rounded_amount=3.0, spare_change=1.0,
        )
        engine.store.roundup_transactions.append(txn)

        ok, reason = engine.should_sweep("test-user", rule, 4.50)
        assert ok is False
        assert "weekly cap" in reason.lower()


class TestSweepExecution:
    """Phase: full sweep pipeline"""

    def test_process_purchase_creates_transaction(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        rule = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=2, floor_amount=0.05,
        ))
        result = engine.process_purchase("test-user", 2.50, circle_id)
        assert result["swept"] is True
        assert result["spare_change"] == 1.00  # 0.50 * 2x
        assert result["transaction_id"] != ""

        # Verify transaction was stored
        txns = engine.get_transactions("test-user", circle_id)
        assert len(txns) == 1
        assert txns[0].spare_change == 1.00

    def test_circle_total_updates_on_sweep(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1, floor_amount=0.05,
        ))
        initial = engine.store.circles[circle_id].total_collected
        engine.process_purchase("test-user", 3.40, circle_id)
        updated = engine.store.circles[circle_id].total_collected
        assert updated == initial + 0.60

    def test_simulate_shows_preview(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=3,
        ))
        result = engine.simulate("test-user", 4.75, circle_id)
        assert result["spare_change"] == 0.75  # 0.25 * 3
        assert result["multiplier"] == 3
        assert result["purchase_amount"] == 4.75

    def test_no_rule_returns_graceful(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        result = engine.process_purchase("test-user", 10.0, circle_id)
        assert result["swept"] is False
        assert "No active rule" in result["reason"]


class TestCircleStats:
    """Phase: aggregate stats"""

    def test_circle_stats_leaderboard(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        # Create rules for two users
        rule1 = engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1, floor_amount=0.01,
        ))

        # Add second user
        engine.store.users["test-user-2"] = {
            "id": "test-user-2",
            "balance": 500.0,
        }
        rule2 = RoundUpRuleCreate(
            user_id="test-user-2", circle_id=circle_id,
            round_to=1.0, multiplier=1, floor_amount=0.01,
        )
        rule2.user_id = "test-user-2"
        engine.create_rule(rule2)

        # Generate sweeps
        engine.process_purchase("test-user", 2.50, circle_id)  # spare 0.50
        engine.process_purchase("test-user", 3.20, circle_id)  # spare 0.80
        engine.process_purchase("test-user-2", 1.50, circle_id)  # spare 0.50

        stats = engine.get_circle_stats(circle_id)
        assert stats.total_sweeps == 3
        assert stats.total_spare_change == 1.80

        # Leaderboard: test-user should be first (1.30 > 0.50)
        assert len(stats.member_leaderboard) >= 2
        top_contributor = stats.member_leaderboard[0]
        assert top_contributor["total"] == 1.30

    def test_empty_circle_stats(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        stats = engine.get_circle_stats(circle_id)
        assert stats.total_sweeps == 0
        assert stats.total_spare_change == 0.0
        assert stats.member_leaderboard == []


class TestTransactionHistory:
    """Phase: history queries"""

    def test_get_transactions_filtered_by_circle(self, engine):
        circle_id = list(engine.store.circles.keys())[0]
        engine.create_rule(RoundUpRuleCreate(
            user_id="test-user", circle_id=circle_id,
            round_to=1.0, multiplier=1, floor_amount=0.01,
        ))
        engine.process_purchase("test-user", 2.50, circle_id)

        txns = engine.get_transactions("test-user", circle_id)
        assert len(txns) == 1

        # Filter by wrong circle → empty
        txns_wrong = engine.get_transactions("test-user", "nonexistent")
        assert len(txns_wrong) == 0
