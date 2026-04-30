from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class CircleStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MemberStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    REMOVED = "removed"

class ScheduleStatus(str, Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    PAID = "paid"
    MISSED = "missed"

class PaymentMethod(str, Enum):
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO = "airteltigo"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class SusuCircleBase(BaseModel):
    name: str
    description: Optional[str] = None
    contribution_amount: Decimal
    cycle_days: int = 30
    max_members: int = 10

class SusuCircleCreate(SusuCircleBase):
    pass

class SusuCircleResponse(SusuCircleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: CircleStatus
    created_at: datetime
    updated_at: datetime

class SusuMemberBase(BaseModel):
    display_name: str
    phone_number: str

class SusuMemberCreate(SusuMemberBase):
    pass

class SusuMemberResponse(SusuMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    circle_id: UUID
    user_id: str
    position_in_rotation: Optional[int]
    status: MemberStatus
    joined_at: Optional[datetime]
    created_at: datetime

class RotationScheduleBase(BaseModel):
    sequence_number: int
    member_id: UUID
    assigned_date: datetime
    due_date: datetime
    payout_amount: Decimal

class RotationScheduleResponse(RotationScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    circle_id: UUID
    status: ScheduleStatus
    created_at: datetime

class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    circle_id: UUID
    balance: Decimal
    required_approvals: int
    created_at: datetime
    updated_at: datetime

class PaymentBase(BaseModel):
    amount: Decimal
    method: PaymentMethod

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    wallet_id: UUID
    member_id: UUID
    status: PaymentStatus
    reference_code: Optional[str]
    created_at: datetime
