import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, DateTime, Numeric, ForeignKey, Integer, Enum, Boolean, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class CircleStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MemberStatus(str, PyEnum):
    INVITED = "invited"
    ACTIVE = "active"
    REMOVED = "removed"

class ScheduleStatus(str, PyEnum):
    UPCOMING = "upcoming"
    DUE = "due"
    PAID = "paid"
    MISSED = "missed"

class PaymentMethod(str, PyEnum):
    MTN_MOMO = "mtn_momo"
    VODAFONE_CASH = "vodafone_cash"
    AIRTELTIGO = "airteltigo"

class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class SusuCircle(Base):
    __tablename__ = "susu_circles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contribution_amount = Column(Numeric(12, 2), nullable=False)
    cycle_days = Column(Integer, nullable=False, default=30)
    max_members = Column(Integer, nullable=False, default=10)
    status = Column(Enum(CircleStatus), nullable=False, default=CircleStatus.PENDING)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    members = relationship("SusuMember", back_populates="circle", cascade="all, delete-orphan")
    schedules = relationship("RotationSchedule", back_populates="circle", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="circle", uselist=False, cascade="all, delete-orphan")

class SusuMember(Base):
    __tablename__ = "susu_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id = Column(UUID(as_uuid=True), ForeignKey("susu_circles.id"), nullable=False)
    user_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    position_in_rotation = Column(Integer, nullable=True)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.INVITED)
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    circle = relationship("SusuCircle", back_populates="members")
    payments = relationship("Payment", back_populates="member", cascade="all, delete-orphan")

class RotationSchedule(Base):
    __tablename__ = "rotation_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id = Column(UUID(as_uuid=True), ForeignKey("susu_circles.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("susu_members.id"), nullable=False)
    assigned_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(ScheduleStatus), nullable=False, default=ScheduleStatus.UPCOMING)
    payout_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    circle = relationship("SusuCircle", back_populates="schedules")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id = Column(UUID(as_uuid=True), ForeignKey("susu_circles.id"), nullable=False, unique=True)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    required_approvals = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    circle = relationship("SusuCircle", back_populates="wallet")
    transactions = relationship("Payment", back_populates="wallet", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("susu_members.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    reference_code = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    wallet = relationship("Wallet", back_populates="transactions")
    member = relationship("SusuMember", back_populates="payments")
