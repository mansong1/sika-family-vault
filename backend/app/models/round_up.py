"""Auto Round-Up models for Sika Bank — spare change → Susu circles"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4


class RoundUpRule(BaseModel):
    """Configuration for automatic spare-change savings"""
    rule_id: str = ""
    user_id: str
    circle_id: str
    active: bool = True
    round_to: float = Field(default=1.0, ge=0.1, le=100.0, description="Round to nearest X GHS")
    multiplier: int = Field(default=1, ge=1, le=10, description="1-10x boost")
    floor_amount: float = Field(default=0.10, ge=0.0, description="Minimum spare change to trigger sweep")
    weekly_cap: Optional[float] = Field(default=None, ge=0.0, description="Max weekly round-up total")
    allocation_pct: float = Field(default=100.0, ge=1.0, le=100.0, description="% of spare change to this circle")
    paused_until: Optional[datetime] = None
    total_accumulated: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context) -> None:
        if not self.rule_id:
            self.rule_id = self._generate_id()

    @staticmethod
    def _generate_id() -> str:
        return str(uuid4())

    def is_paused(self) -> bool:
        if not self.paused_until:
            return False
        return self.paused_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)


class RoundUpRuleCreate(BaseModel):
    """Request body for creating a round-up rule"""
    user_id: str
    circle_id: str
    round_to: float = Field(default=1.0, ge=0.1, le=100.0)
    multiplier: int = Field(default=1, ge=1, le=10)
    floor_amount: float = Field(default=0.10, ge=0.0)
    weekly_cap: Optional[float] = None
    allocation_pct: float = Field(default=100.0, ge=1.0, le=100.0)


class RoundUpRuleUpdate(BaseModel):
    """Partial update for round-up rules"""
    active: Optional[bool] = None
    round_to: Optional[float] = Field(default=None, ge=0.1, le=100.0)
    multiplier: Optional[int] = Field(default=None, ge=1, le=10)
    floor_amount: Optional[float] = Field(default=None, ge=0.0)
    weekly_cap: Optional[float] = None
    allocation_pct: Optional[float] = Field(default=None, ge=1.0, le=100.0)
    paused_until: Optional[datetime] = None  # Set to pause, None to resume
    circle_id: Optional[str] = None


class RoundUpTransaction(BaseModel):
    """A single spare-change sweep"""
    id: str = ""
    user_id: str
    circle_id: str
    rule_id: str
    purchase_amount: float
    rounded_amount: float
    spare_change: float
    multiplier_applied: int = 1
    swept_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_tx_id: str = ""

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.source_tx_id:
            self.source_tx_id = f"RND-{self.id[:8].upper()}"


class RoundUpSimulateRequest(BaseModel):
    """Simulate a round-up on a purchase"""
    purchase_amount: float = Field(..., gt=0)
    circle_id: str


class RoundUpSweepRequest(BaseModel):
    """Trigger a sweep manually (for demo/testing)"""
    purchase_amount: float = Field(..., gt=0)
    circle_id: str


class CircleRoundUpStats(BaseModel):
    """Aggregate round-up stats for a circle"""
    circle_id: str
    circle_name: str = ""
    total_spare_change: float = 0.0
    total_sweeps: int = 0
    member_leaderboard: List[dict] = []
    recent_sweeps: List[dict] = []
