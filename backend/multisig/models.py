"""Pydantic v2 models and in-memory data stores for multi-sig group wallet."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WalletStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class SignerStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    REMOVED = "removed"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class ApprovalAction(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditAction(str, Enum):
    WALLET_CREATED = "wallet_created"
    DEPOSIT = "deposit"
    PROPOSE = "propose"
    APPROVE = "approve"
    REJECT = "reject"
    EXECUTE = "execute"
    SIGNER_ADDED = "signer_added"
    SIGNER_REMOVED = "signer_removed"
    THRESHOLD_CHANGED = "threshold_changed"
    PROPOSAL_EXPIRED = "proposal_expired"
    FUNDS_RETURNED = "funds_returned"


# ---------------------------------------------------------------------------
# Base Models
# ---------------------------------------------------------------------------

class _BaseModel(BaseModel):
    """Base with sensible defaults."""

    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class Signer(_BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    wallet_id: str
    status: SignerStatus = SignerStatus.ACTIVE
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    removed_at: datetime | None = None
    invited_by: str | None = None


class MultiSigWallet(_BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=120)
    balance_cents: int = Field(default=0, ge=0)
    threshold: int = Field(..., ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: WalletStatus = WalletStatus.ACTIVE
    owner_id: str
    total_deposits_cents: int = Field(default=0, ge=0)
    total_withdrawals_cents: int = Field(default=0, ge=0)

    @field_validator("threshold")
    @classmethod
    def _threshold_must_be_at_least_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Threshold must be at least 1")
        return v


class WithdrawalProposal(_BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_id: str
    proposer_id: str
    amount_cents: int = Field(..., ge=1)
    destination_account: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    status: ProposalStatus = ProposalStatus.PENDING
    approvals_required: int = Field(..., ge=1)
    approvals_gathered: int = Field(default=0, ge=0)
    rejections_gathered: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )
    executed_at: datetime | None = None
    rejected_at: datetime | None = None
    escrowed_cents: int = Field(default=0, ge=0)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_final(self) -> bool:
        return self.status in {
            ProposalStatus.EXECUTED,
            ProposalStatus.REJECTED,
            ProposalStatus.EXPIRED,
        }


class Approval(_BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    signer_id: str
    action: ApprovalAction
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str | None = None


class AuditLog(_BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_id: str
    actor_id: str
    action: AuditAction
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class CreateWalletRequest(_BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    owner_id: str
    initial_signers: list[str] = Field(..., min_length=2)
    threshold: int = Field(..., ge=1)

    @field_validator("threshold")
    @classmethod
    def _threshold_vs_signers(cls, v: int, info) -> int:
        signers = info.data.get("initial_signers", [])
        if v > len(signers):
            raise ValueError("Threshold cannot exceed number of initial signers")
        return v


class UpdateThresholdRequest(_BaseModel):
    threshold: int = Field(..., ge=1)


class DepositRequest(_BaseModel):
    amount_cents: int = Field(..., ge=1)
    actor_id: str


class ProposeWithdrawalRequest(_BaseModel):
    amount_cents: int = Field(..., ge=1)
    destination_account: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    proposer_id: str


class AddSignerRequest(_BaseModel):
    user_id: str
    invited_by: str


class RemoveSignerRequest(_BaseModel):
    removed_by: str


class ExecuteRequest(_BaseModel):
    executor_id: str


class ApproveRejectRequest(_BaseModel):
    signer_id: str


class ApiResponse(_BaseModel):
    status: str
    data: dict | None = None
    meta: dict = Field(default_factory=dict)

    @classmethod
    def success(cls, data: dict | None = None, meta: dict | None = None) -> "ApiResponse":
        return cls(status="success", data=data, meta=meta or {})

    @classmethod
    def error(cls, code: str, message: str, meta: dict | None = None) -> "ApiResponse":
        return cls(
            status="error",
            data={"code": code, "message": message},
            meta=meta or {},
        )


# ---------------------------------------------------------------------------
# In-Memory Stores (production → PostgreSQL + Redis locks)
# ---------------------------------------------------------------------------

class DataStore:
    """Thread-unsafe in-memory stores. Production → PostgreSQL + Redis."""

    wallets: ClassVar[dict[str, MultiSigWallet]] = {}
    signers: ClassVar[dict[str, Signer]] = {}
    proposals: ClassVar[dict[str, WithdrawalProposal]] = {}
    approvals: ClassVar[dict[str, Approval]] = {}
    audit_logs: ClassVar[dict[str, AuditLog]] = {}

    @classmethod
    def clear(cls) -> None:
        cls.wallets.clear()
        cls.signers.clear()
        cls.proposals.clear()
        cls.approvals.clear()
        cls.audit_logs.clear()

    @classmethod
    def get_wallet_signers(cls, wallet_id: str, status: SignerStatus | None = None) -> list[Signer]:
        signers = [s for s in cls.signers.values() if s.wallet_id == wallet_id]
        if status:
            signers = [s for s in signers if s.status == status]
        return signers

    @classmethod
    def get_active_signer_for_wallet(cls, wallet_id: str, user_id: str) -> Signer | None:
        for s in cls.signers.values():
            if s.wallet_id == wallet_id and s.user_id == user_id and s.status == SignerStatus.ACTIVE:
                return s
        return None

    @classmethod
    def get_wallet_proposals(cls, wallet_id: str) -> list[WithdrawalProposal]:
        return [p for p in cls.proposals.values() if p.wallet_id == wallet_id]

    @classmethod
    def get_proposal_approvals(cls, proposal_id: str) -> list[Approval]:
        return [a for a in cls.approvals.values() if a.proposal_id == proposal_id]

    @classmethod
    def get_wallet_audit_logs(cls, wallet_id: str) -> list[AuditLog]:
        return sorted(
            (a for a in cls.audit_logs.values() if a.wallet_id == wallet_id),
            key=lambda x: x.created_at,
        )

    @classmethod
    def has_signer_responded(cls, proposal_id: str, signer_id: str) -> bool:
        return any(
            a.proposal_id == proposal_id and a.signer_id == signer_id
            for a in cls.approvals.values()
        )
