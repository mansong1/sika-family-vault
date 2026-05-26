"""Business-logic services for multi-sig group wallet."""

from __future__ import annotations

from datetime import datetime, timezone

from models import (
    Approval,
    ApprovalAction,
    AuditAction,
    AuditLog,
    CreateWalletRequest,
    DataStore,
    DepositRequest,
    MultiSigWallet,
    ProposalStatus,
    ProposeWithdrawalRequest,
    Signer,
    SignerStatus,
    UpdateThresholdRequest,
    WalletStatus,
    WithdrawalProposal,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class MultiSigError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# WalletService
# ---------------------------------------------------------------------------

class WalletService:
    @staticmethod
    def create_wallet(req: CreateWalletRequest) -> MultiSigWallet:
        if req.threshold > len(req.initial_signers):
            raise MultiSigError(
                "INVALID_THRESHOLD",
                "Threshold cannot exceed number of initial signers",
                400,
            )
        if len(req.initial_signers) < 2:
            raise MultiSigError(
                "INSUFFICIENT_SIGNERS",
                "At least 2 signers are required to create a wallet",
                400,
            )

        wallet = MultiSigWallet(
            name=req.name,
            threshold=req.threshold,
            owner_id=req.owner_id,
        )
        DataStore.wallets[wallet.id] = wallet

        # Add owner as first signer
        owner_signer = Signer(
            user_id=req.owner_id,
            wallet_id=wallet.id,
            status=SignerStatus.ACTIVE,
            invited_by=None,
        )
        DataStore.signers[owner_signer.id] = owner_signer

        # Add remaining initial signers
        for user_id in req.initial_signers:
            if user_id == req.owner_id:
                continue
            signer = Signer(
                user_id=user_id,
                wallet_id=wallet.id,
                status=SignerStatus.ACTIVE,
                invited_by=req.owner_id,
            )
            DataStore.signers[signer.id] = signer

        WalletService._log(
            wallet.id,
            req.owner_id,
            AuditAction.WALLET_CREATED,
            {"wallet_name": req.name, "threshold": req.threshold},
        )
        return wallet

    @staticmethod
    def add_signer(wallet_id: str, user_id: str, invited_by: str) -> Signer:
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)
        if wallet.status != WalletStatus.ACTIVE:
            raise MultiSigError("WALLET_INACTIVE", "Wallet is not active", 400)

        # Check inviter is active signer
        inviter = DataStore.get_active_signer_for_wallet(wallet_id, invited_by)
        if not inviter:
            raise MultiSigError(
                "NOT_A_SIGNER", "Only active signers can invite new members", 403
            )

        # Prevent duplicate active signers
        existing = DataStore.get_active_signer_for_wallet(wallet_id, user_id)
        if existing:
            raise MultiSigError(
                "SIGNER_EXISTS", "User is already an active signer on this wallet", 409
            )

        signer = Signer(
            user_id=user_id,
            wallet_id=wallet_id,
            status=SignerStatus.ACTIVE,
            invited_by=invited_by,
        )
        DataStore.signers[signer.id] = signer

        WalletService._log(
            wallet_id,
            invited_by,
            AuditAction.SIGNER_ADDED,
            {"added_user_id": user_id},
        )
        return signer

    @staticmethod
    def remove_signer(wallet_id: str, user_id: str, removed_by: str) -> None:
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)

        # Check remover is active signer
        remover = DataStore.get_active_signer_for_wallet(wallet_id, removed_by)
        if not remover:
            raise MultiSigError(
                "NOT_A_SIGNER", "Only active signers can remove members", 403
            )

        signer = DataStore.get_active_signer_for_wallet(wallet_id, user_id)
        if not signer:
            raise MultiSigError(
                "SIGNER_NOT_FOUND", "Signer not found or not active", 404
            )

        # Prevent removing the last active signer
        active = DataStore.get_wallet_signers(wallet_id, SignerStatus.ACTIVE)
        if len(active) <= 1:
            raise MultiSigError(
                "LAST_SIGNER",
                "Cannot remove the last active signer. Add a replacement first.",
                400,
            )

        signer.status = SignerStatus.REMOVED
        signer.removed_at = datetime.now(timezone.utc)

        # If threshold now exceeds active signers, freeze wallet
        remaining_active = DataStore.get_wallet_signers(wallet_id, SignerStatus.ACTIVE)
        if wallet.threshold > len(remaining_active):
            wallet.status = WalletStatus.FROZEN

        WalletService._log(
            wallet_id,
            removed_by,
            AuditAction.SIGNER_REMOVED,
            {"removed_user_id": user_id},
        )

    @staticmethod
    def update_threshold(wallet_id: str, req: UpdateThresholdRequest, updated_by: str) -> MultiSigWallet:
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)
        if wallet.status != WalletStatus.ACTIVE:
            raise MultiSigError("WALLET_INACTIVE", "Wallet is not active", 400)

        # Check updater is active signer
        updater = DataStore.get_active_signer_for_wallet(wallet_id, updated_by)
        if not updater:
            raise MultiSigError(
                "NOT_A_SIGNER", "Only active signers can update threshold", 403
            )

        active_count = len(DataStore.get_wallet_signers(wallet_id, SignerStatus.ACTIVE))
        if req.threshold > active_count:
            raise MultiSigError(
                "INVALID_THRESHOLD",
                f"Threshold ({req.threshold}) cannot exceed active signers ({active_count})",
                400,
            )

        old_threshold = wallet.threshold
        wallet.threshold = req.threshold

        WalletService._log(
            wallet_id,
            updated_by,
            AuditAction.THRESHOLD_CHANGED,
            {"old_threshold": old_threshold, "new_threshold": req.threshold},
        )
        return wallet

    @staticmethod
    def deposit(wallet_id: str, req: DepositRequest) -> MultiSigWallet:
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)
        if wallet.status != WalletStatus.ACTIVE:
            raise MultiSigError("WALLET_INACTIVE", "Wallet is not active", 400)

        wallet.balance_cents += req.amount_cents
        wallet.total_deposits_cents += req.amount_cents

        WalletService._log(
            wallet_id,
            req.actor_id,
            AuditAction.DEPOSIT,
            {"amount_cents": req.amount_cents, "new_balance_cents": wallet.balance_cents},
        )
        return wallet

    @staticmethod
    def get_wallet(wallet_id: str) -> MultiSigWallet | None:
        return DataStore.wallets.get(wallet_id)

    @staticmethod
    def _log(wallet_id: str, actor_id: str, action: AuditAction, details: dict) -> None:
        log = AuditLog(
            wallet_id=wallet_id,
            actor_id=actor_id,
            action=action,
            details=details,
        )
        DataStore.audit_logs[log.id] = log


# ---------------------------------------------------------------------------
# ProposalService
# ---------------------------------------------------------------------------

class ProposalService:
    @staticmethod
    def propose(wallet_id: str, req: ProposeWithdrawalRequest) -> WithdrawalProposal:
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)
        if wallet.status != WalletStatus.ACTIVE:
            raise MultiSigError("WALLET_INACTIVE", "Wallet is frozen or closed", 400)

        # Proposer must be active signer
        proposer = DataStore.get_active_signer_for_wallet(wallet_id, req.proposer_id)
        if not proposer:
            raise MultiSigError(
                "NOT_A_SIGNER", "Only active signers can propose withdrawals", 403
            )

        if req.amount_cents > wallet.balance_cents:
            raise MultiSigError(
                "INSUFFICIENT_FUNDS",
                f"Wallet balance ({wallet.balance_cents} cents) is less than proposed withdrawal ({req.amount_cents} cents)",
                400,
            )

        # Lock funds
        wallet.balance_cents -= req.amount_cents
        proposal = WithdrawalProposal(
            wallet_id=wallet_id,
            proposer_id=req.proposer_id,
            amount_cents=req.amount_cents,
            destination_account=req.destination_account,
            description=req.description,
            approvals_required=wallet.threshold,
            approvals_gathered=1,  # proposer auto-approves
            escrowed_cents=req.amount_cents,
        )
        DataStore.proposals[proposal.id] = proposal

        # Record proposer's implicit approval
        approval = Approval(
            proposal_id=proposal.id,
            signer_id=req.proposer_id,
            action=ApprovalAction.APPROVED,
        )
        DataStore.approvals[approval.id] = approval

        # Auto-approve if threshold is 1
        if proposal.approvals_gathered >= proposal.approvals_required:
            proposal.status = ProposalStatus.APPROVED

        WalletService._log(
            wallet_id,
            req.proposer_id,
            AuditAction.PROPOSE,
            {
                "proposal_id": proposal.id,
                "amount_cents": req.amount_cents,
                "destination": req.destination_account,
            },
        )
        return proposal

    @staticmethod
    def approve(proposal_id: str, signer_id: str) -> WithdrawalProposal:
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        if proposal.is_final:
            raise MultiSigError("PROPOSAL_FINAL", "Proposal is already finalized", 400)
        if proposal.is_expired:
            ProposalService._expire(proposal)
            raise MultiSigError("PROPOSAL_EXPIRED", "Proposal has expired", 400)

        # Signer must be active on the wallet
        signer = DataStore.get_active_signer_for_wallet(proposal.wallet_id, signer_id)
        if not signer:
            raise MultiSigError(
                "NOT_A_SIGNER",
                "You are not an active signer on this wallet",
                403,
            )

        # Double-approval prevention
        if DataStore.has_signer_responded(proposal_id, signer_id):
            raise MultiSigError(
                "ALREADY_RESPONDED",
                "You have already responded to this proposal",
                409,
            )

        approval = Approval(
            proposal_id=proposal_id,
            signer_id=signer_id,
            action=ApprovalAction.APPROVED,
        )
        DataStore.approvals[approval.id] = approval
        proposal.approvals_gathered += 1

        if proposal.approvals_gathered >= proposal.approvals_required:
            proposal.status = ProposalStatus.APPROVED

        WalletService._log(
            proposal.wallet_id,
            signer_id,
            AuditAction.APPROVE,
            {"proposal_id": proposal_id, "approvals_gathered": proposal.approvals_gathered},
        )
        return proposal

    @staticmethod
    def reject(proposal_id: str, signer_id: str) -> WithdrawalProposal:
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        if proposal.is_final:
            raise MultiSigError("PROPOSAL_FINAL", "Proposal is already finalized", 400)
        if proposal.is_expired:
            ProposalService._expire(proposal)
            raise MultiSigError("PROPOSAL_EXPIRED", "Proposal has expired", 400)

        signer = DataStore.get_active_signer_for_wallet(proposal.wallet_id, signer_id)
        if not signer:
            raise MultiSigError(
                "NOT_A_SIGNER",
                "You are not an active signer on this wallet",
                403,
            )

        if DataStore.has_signer_responded(proposal_id, signer_id):
            raise MultiSigError(
                "ALREADY_RESPONDED",
                "You have already responded to this proposal",
                409,
            )

        approval = Approval(
            proposal_id=proposal_id,
            signer_id=signer_id,
            action=ApprovalAction.REJECTED,
        )
        DataStore.approvals[approval.id] = approval
        proposal.rejections_gathered += 1

        # Check if rejection quorum reached
        active_signers = DataStore.get_wallet_signers(proposal.wallet_id, SignerStatus.ACTIVE)
        rejections_needed = len(active_signers) - proposal.approvals_required + 1
        if proposal.rejections_gathered >= rejections_needed:
            proposal.status = ProposalStatus.REJECTED
            proposal.rejected_at = datetime.now(timezone.utc)
            # Return funds to wallet
            ProposalService._return_funds(proposal)

        WalletService._log(
            proposal.wallet_id,
            signer_id,
            AuditAction.REJECT,
            {"proposal_id": proposal_id, "rejections_gathered": proposal.rejections_gathered},
        )
        return proposal

    @staticmethod
    def execute(proposal_id: str, executor_id: str) -> WithdrawalProposal:
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        if proposal.is_final:
            raise MultiSigError("PROPOSAL_FINAL", "Proposal is already finalized", 400)
        if proposal.is_expired:
            ProposalService._expire(proposal)
            raise MultiSigError("PROPOSAL_EXPIRED", "Proposal has expired", 400)

        executor = DataStore.get_active_signer_for_wallet(proposal.wallet_id, executor_id)
        if not executor:
            raise MultiSigError(
                "NOT_A_SIGNER",
                "Only active signers can execute proposals",
                403,
            )

        if proposal.status != ProposalStatus.APPROVED:
            raise MultiSigError(
                "NOT_APPROVED",
                f"Proposal needs {proposal.approvals_required} approvals, has {proposal.approvals_gathered}",
                400,
            )

        # Verify threshold hasn't drifted due to signer removal
        active_signers = DataStore.get_wallet_signers(proposal.wallet_id, SignerStatus.ACTIVE)
        if proposal.approvals_required > len(active_signers):
            raise MultiSigError(
                "THRESHOLD_DRIFT",
                "Wallet threshold exceeds active signers. Wallet is frozen.",
                400,
            )

        proposal.status = ProposalStatus.EXECUTED
        proposal.executed_at = datetime.now(timezone.utc)
        proposal.escrowed_cents = 0

        wallet = DataStore.wallets[proposal.wallet_id]
        wallet.total_withdrawals_cents += proposal.amount_cents

        WalletService._log(
            proposal.wallet_id,
            executor_id,
            AuditAction.EXECUTE,
            {
                "proposal_id": proposal_id,
                "amount_cents": proposal.amount_cents,
                "destination": proposal.destination_account,
            },
        )
        return proposal

    @staticmethod
    def get_status(proposal_id: str) -> WithdrawalProposal | None:
        proposal = DataStore.proposals.get(proposal_id)
        if proposal and proposal.is_expired and not proposal.is_final:
            ProposalService._expire(proposal)
        return proposal

    @staticmethod
    def get_proposals_for_wallet(wallet_id: str) -> list[WithdrawalProposal]:
        proposals = DataStore.get_wallet_proposals(wallet_id)
        for p in proposals:
            if p.is_expired and not p.is_final:
                ProposalService._expire(p)
        return proposals

    @staticmethod
    def _expire(proposal: WithdrawalProposal) -> None:
        if proposal.is_final:
            return
        proposal.status = ProposalStatus.EXPIRED
        ProposalService._return_funds(proposal)
        WalletService._log(
            proposal.wallet_id,
            "system",
            AuditAction.PROPOSAL_EXPIRED,
            {"proposal_id": proposal.id},
        )

    @staticmethod
    def _return_funds(proposal: WithdrawalProposal) -> None:
        if proposal.escrowed_cents <= 0:
            return
        wallet = DataStore.wallets.get(proposal.wallet_id)
        if wallet:
            wallet.balance_cents += proposal.escrowed_cents
        proposal.escrowed_cents = 0
        WalletService._log(
            proposal.wallet_id,
            "system",
            AuditAction.FUNDS_RETURNED,
            {"proposal_id": proposal.id, "amount_cents": proposal.amount_cents},
        )


# ---------------------------------------------------------------------------
# EscrowService
# ---------------------------------------------------------------------------

class EscrowService:
    """Pure-Python escrow. Funds are tracked via proposal.escrowed_cents."""

    @staticmethod
    def hold(wallet_id: str, amount_cents: int) -> None:
        """Deposit funds into wallet (no escrow needed)."""
        wallet = DataStore.wallets.get(wallet_id)
        if not wallet:
            raise MultiSigError("WALLET_NOT_FOUND", "Wallet not found", 404)
        wallet.balance_cents += amount_cents

    @staticmethod
    def lock(wallet_id: str, proposal_id: str, amount_cents: int) -> None:
        """Lock funds in proposal escrow. Called by ProposalService.propose."""
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        proposal.escrowed_cents = amount_cents

    @staticmethod
    def release(proposal_id: str, destination_account: str) -> None:
        """Release escrowed funds to destination. Called by ProposalService.execute."""
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        proposal.escrowed_cents = 0

    @staticmethod
    def return_to_wallet(proposal_id: str) -> None:
        """Return escrowed funds to wallet. Called by ProposalService.reject/_expire."""
        proposal = DataStore.proposals.get(proposal_id)
        if not proposal:
            raise MultiSigError("PROPOSAL_NOT_FOUND", "Proposal not found", 404)
        if proposal.escrowed_cents > 0:
            wallet = DataStore.wallets.get(proposal.wallet_id)
            if wallet:
                wallet.balance_cents += proposal.escrowed_cents
            proposal.escrowed_cents = 0
