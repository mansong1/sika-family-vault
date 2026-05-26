"""pytest suite for multi-sig group wallet — 15+ tests."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from models import (
    ApprovalAction,
    CreateWalletRequest,
    DataStore,
    DepositRequest,
    ProposalStatus,
    ProposeWithdrawalRequest,
    SignerStatus,
    UpdateThresholdRequest,
    WalletStatus,
)
from services import MultiSigError, ProposalService, WalletService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_store():
    """Clean in-memory store before every test."""
    DataStore.clear()
    yield
    DataStore.clear()


@pytest.fixture
def wallet_and_signers():
    """Create a standard 2-of-3 wallet with ₵10,000 balance."""
    req = CreateWalletRequest(
        name="Family Savings",
        owner_id="user_owner",
        initial_signers=["user_owner", "user_sister", "user_brother"],
        threshold=2,
    )
    wallet = WalletService.create_wallet(req)
    WalletService.deposit(
        wallet.id,
        DepositRequest(amount_cents=1_000_000, actor_id="user_owner"),
    )
    return wallet.id


# ---------------------------------------------------------------------------
# Wallet Creation Tests
# ---------------------------------------------------------------------------

def test_create_wallet_success(wallet_and_signers):
    """1. Wallet created with correct threshold and signers."""
    wallet = WalletService.get_wallet(wallet_and_signers)
    assert wallet is not None
    assert wallet.name == "Family Savings"
    assert wallet.threshold == 2
    assert wallet.balance_cents == 1_000_000
    signers = DataStore.get_wallet_signers(wallet.id, SignerStatus.ACTIVE)
    assert len(signers) == 3


def test_create_wallet_threshold_too_high():
    """2. Threshold > signers rejected at service level."""
    # Bypass Pydantic validation to test service-level guard
    req = CreateWalletRequest(
        name="Bad Wallet",
        owner_id="user_a",
        initial_signers=["user_a", "user_b"],
        threshold=2,
    )
    # Manually override threshold to trigger service error
    req = req.model_copy(update={"threshold": 5})
    with pytest.raises(MultiSigError) as exc:
        WalletService.create_wallet(req)
    assert exc.value.code == "INVALID_THRESHOLD"


def test_create_wallet_insufficient_signers():
    """3. Less than 2 signers rejected at service level."""
    # Create valid request then manually set signers to test service guard
    req = CreateWalletRequest(
        name="Solo Wallet",
        owner_id="user_a",
        initial_signers=["user_a", "user_b"],
        threshold=1,
    )
    req = req.model_copy(update={"initial_signers": ["user_a"]})
    with pytest.raises(MultiSigError) as exc:
        WalletService.create_wallet(req)
    assert exc.value.code == "INSUFFICIENT_SIGNERS"


# ---------------------------------------------------------------------------
# Signer Management Tests
# ---------------------------------------------------------------------------

def test_add_signer_success(wallet_and_signers):
    """4. Active signer can invite a new signer."""
    wallet_id = wallet_and_signers
    signer = WalletService.add_signer(wallet_id, "user_cousin", "user_owner")
    assert signer.user_id == "user_cousin"
    assert signer.status == SignerStatus.ACTIVE
    active = DataStore.get_wallet_signers(wallet_id, SignerStatus.ACTIVE)
    assert len(active) == 4


def test_remove_signer_success(wallet_and_signers):
    """5. Signer removal works and drops active count."""
    wallet_id = wallet_and_signers
    WalletService.remove_signer(wallet_id, "user_brother", "user_owner")
    active = DataStore.get_wallet_signers(wallet_id, SignerStatus.ACTIVE)
    assert len(active) == 2


def test_remove_last_signer_rejected(wallet_and_signers):
    """6. Cannot remove the last active signer."""
    wallet_id = wallet_and_signers
    WalletService.remove_signer(wallet_id, "user_sister", "user_owner")
    WalletService.remove_signer(wallet_id, "user_brother", "user_owner")
    with pytest.raises(MultiSigError) as exc:
        WalletService.remove_signer(wallet_id, "user_owner", "user_owner")
    assert exc.value.code == "LAST_SIGNER"


def test_add_duplicate_signer_rejected(wallet_and_signers):
    """7. Cannot add user who is already an active signer."""
    wallet_id = wallet_and_signers
    with pytest.raises(MultiSigError) as exc:
        WalletService.add_signer(wallet_id, "user_sister", "user_owner")
    assert exc.value.code == "SIGNER_EXISTS"


def test_non_signer_cannot_add_signer(wallet_and_signers):
    """8. Non-signer cannot invite new members."""
    wallet_id = wallet_and_signers
    with pytest.raises(MultiSigError) as exc:
        WalletService.add_signer(wallet_id, "user_stranger", "user_stranger")
    assert exc.value.code == "NOT_A_SIGNER"


# ---------------------------------------------------------------------------
# Proposal Tests
# ---------------------------------------------------------------------------

def test_propose_withdrawal_success(wallet_and_signers):
    """9. Active signer can propose withdrawal, funds locked in escrow."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="School fees",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    assert proposal.amount_cents == 100_000
    assert proposal.status.value == "pending" or proposal.status == "approved"
    assert proposal.escrowed_cents == 100_000
    wallet = WalletService.get_wallet(wallet_id)
    assert wallet.balance_cents == 900_000


def test_propose_withdrawal_insufficient_funds(wallet_and_signers):
    """10. Cannot propose more than wallet balance."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=2_000_000,
        destination_account="233555123456",
        description="Too much",
        proposer_id="user_owner",
    )
    with pytest.raises(MultiSigError) as exc:
        ProposalService.propose(wallet_id, req)
    assert exc.value.code == "INSUFFICIENT_FUNDS"


def test_non_signer_cannot_propose(wallet_and_signers):
    """11. Non-signer cannot propose."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=10_000,
        destination_account="233555123456",
        description="Hack attempt",
        proposer_id="user_stranger",
    )
    with pytest.raises(MultiSigError) as exc:
        ProposalService.propose(wallet_id, req)
    assert exc.value.code == "NOT_A_SIGNER"


# ---------------------------------------------------------------------------
# Approval / Execution Tests
# ---------------------------------------------------------------------------

def test_approve_and_execute_flow(wallet_and_signers):
    """12. 2-of-3: owner proposes, sister approves, brother executes."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="School fees",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    assert proposal.approvals_gathered == 1

    # Sister approves → threshold reached
    proposal = ProposalService.approve(proposal.id, "user_sister")
    assert proposal.approvals_gathered == 2
    assert proposal.status == ProposalStatus.APPROVED

    # Brother executes
    executed = ProposalService.execute(proposal.id, "user_brother")
    assert executed.status.value == "executed"
    assert executed.escrowed_cents == 0
    wallet = WalletService.get_wallet(wallet_id)
    assert wallet.total_withdrawals_cents == 100_000


def test_double_approval_rejected(wallet_and_signers):
    """13. Same signer cannot approve twice."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    with pytest.raises(MultiSigError) as exc:
        ProposalService.approve(proposal.id, "user_owner")
    assert exc.value.code == "ALREADY_RESPONDED"


def test_non_signer_cannot_approve(wallet_and_signers):
    """14. Non-signer approval rejected."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    with pytest.raises(MultiSigError) as exc:
        ProposalService.approve(proposal.id, "user_stranger")
    assert exc.value.code == "NOT_A_SIGNER"


def test_execute_without_enough_approvals(wallet_and_signers):
    """15. Cannot execute proposal that hasn't reached threshold."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    with pytest.raises(MultiSigError) as exc:
        ProposalService.execute(proposal.id, "user_owner")
    assert exc.value.code == "NOT_APPROVED"


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

def test_rejection_returns_funds(wallet_and_signers):
    """16. Rejection by quorum returns funds to wallet."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    # Owner already approved implicitly. Sister + brother reject → quorum rejection
    ProposalService.reject(proposal.id, "user_sister")
    proposal = ProposalService.reject(proposal.id, "user_brother")
    assert proposal.status == ProposalStatus.REJECTED
    assert proposal.escrowed_cents == 0
    wallet = WalletService.get_wallet(wallet_id)
    assert wallet.balance_cents == 1_000_000  # fully returned


def test_signer_removed_mid_proposal_still_counts(wallet_and_signers):
    """17. If signer approved then is removed, approval still counts."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    ProposalService.approve(proposal.id, "user_sister")

    # Remove sister — her approval stays valid
    WalletService.remove_signer(wallet_id, "user_sister", "user_owner")
    # Should still be executable (owner + sister = 2 approvals)
    executed = ProposalService.execute(proposal.id, "user_owner")
    assert executed.status == ProposalStatus.EXECUTED


def test_proposal_expiry_returns_funds(wallet_and_signers):
    """18. Expired proposal returns funds to wallet."""
    wallet_id = wallet_and_signers
    req = ProposeWithdrawalRequest(
        amount_cents=100_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    # Manually expire
    proposal.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    refreshed = ProposalService.get_status(proposal.id)
    assert refreshed.status == ProposalStatus.EXPIRED
    assert refreshed.escrowed_cents == 0
    wallet = WalletService.get_wallet(wallet_id)
    assert wallet.balance_cents == 1_000_000


def test_threshold_update_freezes_wallet(wallet_and_signers):
    """19. Removing signers so threshold > active signers freezes wallet."""
    wallet_id = wallet_and_signers
    # Remove sister and brother → 1 active signer, threshold=2 → frozen
    WalletService.remove_signer(wallet_id, "user_sister", "user_owner")
    WalletService.remove_signer(wallet_id, "user_brother", "user_owner")
    wallet = WalletService.get_wallet(wallet_id)
    assert wallet.status == WalletStatus.FROZEN


def test_audit_trail_populated(wallet_and_signers):
    """20. Every action creates an audit log entry."""
    wallet_id = wallet_and_signers
    logs_before = DataStore.get_wallet_audit_logs(wallet_id)
    assert len(logs_before) >= 2  # created + deposit

    req = ProposeWithdrawalRequest(
        amount_cents=50_000,
        destination_account="233555123456",
        description="Test",
        proposer_id="user_owner",
    )
    proposal = ProposalService.propose(wallet_id, req)
    ProposalService.approve(proposal.id, "user_sister")
    ProposalService.execute(proposal.id, "user_owner")

    logs_after = DataStore.get_wallet_audit_logs(wallet_id)
    assert len(logs_after) >= len(logs_before) + 3  # propose + approve + execute
    actions = {log.action.value for log in logs_after}
    assert "propose" in actions
    assert "approve" in actions
    assert "execute" in actions


def test_deposit_increases_balance(wallet_and_signers):
    """21. Deposit correctly adds to wallet balance."""
    wallet_id = wallet_and_signers
    wallet_before = WalletService.get_wallet(wallet_id)
    balance_before = wallet_before.balance_cents  # capture value, not ref
    WalletService.deposit(
        wallet_id,
        DepositRequest(amount_cents=500_000, actor_id="user_owner"),
    )
    wallet_after = WalletService.get_wallet(wallet_id)
    assert wallet_after.balance_cents == balance_before + 500_000
    assert wallet_after.total_deposits_cents == 1_500_000
