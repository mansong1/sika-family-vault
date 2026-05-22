"""Tests for the SusuScore™ credit scoring engine."""

from app.services.score_engine import SusuScoreEngine, ScoreTier


class TestScoreTier:
    def test_excellent_tier(self):
        assert ScoreTier.from_score(800) == ScoreTier.EXCELLENT
        assert ScoreTier.from_score(850) == ScoreTier.EXCELLENT

    def test_very_good_tier(self):
        assert ScoreTier.from_score(740) == ScoreTier.VERY_GOOD
        assert ScoreTier.from_score(799) == ScoreTier.VERY_GOOD

    def test_good_tier(self):
        assert ScoreTier.from_score(670) == ScoreTier.GOOD
        assert ScoreTier.from_score(739) == ScoreTier.GOOD

    def test_fair_tier(self):
        assert ScoreTier.from_score(580) == ScoreTier.FAIR
        assert ScoreTier.from_score(669) == ScoreTier.FAIR

    def test_needs_improvement(self):
        assert ScoreTier.from_score(300) == ScoreTier.NEEDS_IMPROVEMENT
        assert ScoreTier.from_score(579) == ScoreTier.NEEDS_IMPROVEMENT


class TestScoreEngine:
    """Test the SusuScoreEngine calculation logic."""

    def setup_method(self):
        self.engine = SusuScoreEngine()

    def test_baseline_score(self):
        """A user with minimal data should get a baseline score."""
        result = self.engine.calculate(
            user_id="test-1",
            on_time_payments=0,
            total_payments=1,
            streak_months=0,
            circles_joined=0,
            circles_completed=0,
            circles_defaulted=0,
            contribution_amounts=[100.0],
        )
        assert 300 <= result.total_score <= 450
        assert result.tier in (ScoreTier.NEEDS_IMPROVEMENT, ScoreTier.FAIR)

    def test_perfect_score(self):
        """A model user with perfect behavior should score high."""
        result = self.engine.calculate(
            user_id="test-2",
            on_time_payments=48,
            total_payments=48,
            streak_months=24,
            circles_joined=3,
            circles_completed=3,
            circles_defaulted=0,
            contribution_amounts=[200.0, 200.0, 200.0, 200.0, 200.0],
            is_admin_count=2,
            largest_circle_size=12,
        )
        assert result.total_score >= 780
        assert result.tier in (ScoreTier.EXCELLENT, ScoreTier.VERY_GOOD)

    def test_defaults_damage_score(self):
        """Defaults should significantly reduce score."""
        clean = self.engine.calculate(
            user_id="test-3a",
            on_time_payments=12,
            total_payments=12,
            streak_months=12,
            circles_joined=2,
            circles_completed=2,
            circles_defaulted=0,
            contribution_amounts=[150.0, 150.0],
        )

        defaulted = self.engine.calculate(
            user_id="test-3b",
            on_time_payments=8,
            total_payments=12,
            streak_months=0,
            circles_joined=2,
            circles_completed=0,
            circles_defaulted=2,
            contribution_amounts=[150.0, 150.0],
        )

        assert clean.total_score > defaulted.total_score
        assert defaulted.total_score < 550

    def test_consistency_boost(self):
        """Consistent contribution amounts should improve score."""
        inconsistent = self.engine.calculate(
            user_id="test-4a",
            on_time_payments=12,
            total_payments=12,
            streak_months=12,
            circles_joined=1,
            circles_completed=1,
            circles_defaulted=0,
            contribution_amounts=[50.0, 200.0, 30.0, 300.0, 10.0, 500.0],
        )

        consistent = self.engine.calculate(
            user_id="test-4b",
            on_time_payments=12,
            total_payments=12,
            streak_months=12,
            circles_joined=1,
            circles_completed=1,
            circles_defaulted=0,
            contribution_amounts=[100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        )

        assert consistent.total_score >= inconsistent.total_score

    def test_streak_matters(self):
        """Longer streaks produce better scores."""
        short_streak = self.engine.calculate(
            user_id="test-5a",
            on_time_payments=3,
            total_payments=3,
            streak_months=3,
            circles_joined=1,
            circles_completed=0,
            circles_defaulted=0,
            contribution_amounts=[100.0],
        )

        long_streak = self.engine.calculate(
            user_id="test-5b",
            on_time_payments=24,
            total_payments=24,
            streak_months=24,
            circles_joined=1,
            circles_completed=1,
            circles_defaulted=0,
            contribution_amounts=[100.0],
        )

        assert long_streak.total_score > short_streak.total_score

    def test_score_bounds(self):
        """Score must always be within [300, 850]."""
        for i, params in enumerate([
            {"on_time_payments": 0, "total_payments": 0, "streak_months": 0, "circles_joined": 0,
             "circles_completed": 0, "circles_defaulted": 10, "contribution_amounts": []},
            {"on_time_payments": 100, "total_payments": 100, "streak_months": 50, "circles_joined": 20,
             "circles_completed": 20, "circles_defaulted": 0, "contribution_amounts": [500.0] * 50,
             "is_admin_count": 10, "largest_circle_size": 50},
        ]):
            result = self.engine.calculate(user_id=f"test-6-{i}", **params)
            assert 300 <= result.total_score <= 850, f"Iteration {i}: score={result.total_score}"

    def test_all_factors_present(self):
        """The breakdown should include all 6 factors."""
        result = self.engine.calculate(
            user_id="test-7",
            on_time_payments=6,
            total_payments=6,
            streak_months=6,
            circles_joined=1,
            circles_completed=1,
            circles_defaulted=0,
            contribution_amounts=[100.0],
        )

        factor_names = {f.name for f in result.factors}
        expected = {
            "On-time Contributions",
            "Savings Streak",
            "Circle Participation",
            "Contribution Consistency",
            "Payment History",
            "Circle Completion",
        }
        assert factor_names == expected
        # Weights should sum to 1.0
        weight_sum = sum(f.weight for f in result.factors)
        assert abs(weight_sum - 1.0) < 0.01

    def test_improvement_tips(self):
        """Improvement tips should be relevant to weak factors."""
        result = self.engine.calculate(
            user_id="test-8",
            on_time_payments=2,
            total_payments=10,
            streak_months=0,
            circles_joined=1,
            circles_completed=0,
            circles_defaulted=1,
            contribution_amounts=[50.0, 200.0, 30.0],
        )

        tips = self.engine.get_improvement_tips(result)
        assert len(tips) <= 3
        assert len(tips) > 0
        # Tips should be actionable (any real advice is valid)
        assert any(len(t.strip()) > 5 for t in tips)

    def test_perfect_user_tips(self):
        """A perfect user should get a congratulatory tip."""
        result = self.engine.calculate(
            user_id="test-9",
            on_time_payments=48,
            total_payments=48,
            streak_months=24,
            circles_joined=5,
            circles_completed=5,
            circles_defaulted=0,
            contribution_amounts=[200.0] * 30,
            is_admin_count=3,
            largest_circle_size=15,
        )

        tips = self.engine.get_improvement_tips(result)
        assert any("great shape" in t.lower() or "🎉" in t for t in tips)
