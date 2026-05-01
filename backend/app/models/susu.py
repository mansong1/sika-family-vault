from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SusuStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"

class MemberRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class SusuCircleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    contribution_amount: float = Field(..., gt=0)
    cycle_length_days: int = Field(..., ge=7, le=365)
    max_members: int = Field(..., ge=2, le=50)
    penalty_for_late: float = Field(default=0.05, ge=0, le=1)

class SusuCircleCreate(SusuCircleBase):
    pass

class CircleMember(BaseModel):
    user_id: str
    role: MemberRole
    position: Optional[int] = None
    has_paid_current_cycle: bool = False
    joined_at: datetime
    credit_score_delta: int = 0

class SusuCycle(BaseModel):
    cycle_number: int
    start_date: datetime
    end_date: datetime
    payout_to: Optional[str] = None
    total_collected: float = 0.0
    status: str = "active"

class SusuCircle(SusuCircleBase):
    id: str
    status: SusuStatus
    admin_id: str
    members: List[CircleMember] = []
    cycles: List[SusuCycle] = []
    total_collected: float = 0.0
    insurance_pool_balance: float = 0.0
    created_at: datetime
    updated_at: datetime

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class MobileMoneyProvider(str, Enum):
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO = "airteltigo"

class PaymentCreate(BaseModel):
    circle_id: str
    amount: float = Field(..., gt=0)
    provider: MobileMoneyProvider
    phone_number: str

class Payment(BaseModel):
    id: str
    circle_id: str
    user_id: str
    amount: float
    provider: MobileMoneyProvider
    phone_number: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime

class RoundUpRule(BaseModel):
    user_id: str
    round_to: float = Field(default=1.0, ge=0.1)
    active: bool = True
    total_accumulated: float = 0.0

class CreditScore(BaseModel):
    user_id: str
    score: int = Field(default=500, ge=300, le=850)
    circles_completed: int = 0
    on_time_payments: int = 0
    late_payments: int = 0
    defaulted_circles: int = 0
    last_updated: datetime

class UserBase(BaseModel):
    email: str
    phone_number: str
    full_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    bvn: Optional[str] = None

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    is_verified: bool = False
    credit_score: CreditScore
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: str
    password: str
