# Sika Family Vault — Multi-Sig Group Wallet Specification

## Version: 1.0.0
## Date: 2026-05-26
## Owner: Sika Bank Backend
## Status: Approved for Build

---

## 1. Purpose

The Multi-Sig Group Wallet enables families, susu circles, cooperatives, and savings groups to hold shared funds where **N-of-M** signers must approve any withdrawal. This addresses the #1 trust concern across African fintech platforms — users fear single-person control over communal money.

## 2. Core Flows

### 2.1 Wallet Creation
1. Creator specifies: wallet name, initial signers (at least 2), approval threshold (N)
2. System validates: threshold ≤ total signers, threshold ≥ 1, at least 2 active signers
3. Wallet status: ACTIVE

### 2.2 Fund Deposit
1. Any user can deposit into a wallet (deposit does not require approval)
2. Funds held in escrow service (pure Python, no blockchain)
3. Wallet balance updated atomically
4. Transaction logged to audit trail

### 2.3 Withdrawal Proposal
1. Any active signer proposes: amount, destination account, description
2. System checks: proposer is active signer, amount ≤ wallet balance
3. Funds are moved from wallet balance to proposal escrow
4. Proposal status: PENDING
5. Approval count starts at 1 (the proposer's implicit approval)

### 2.4 Approval Flow
1. Other active signers review proposal and approve or reject
2. Double-approval prevention: each signer can only approve/reject once
3. Non-signers cannot approve

### 2.5 Execution
1. When approvals ≥ threshold, proposal is auto-executable
2. On execute: funds released to destination, proposal status → EXECUTED
3. If threshold never met (rejected by quorum or timeout): funds returned to wallet

## 3. Data Models

### MultiSigWallet
```python
class MultiSigWallet:
    id: str                    # UUID v4
    name: str                  # Human-readable name
    balance_cents: int         # Funds held, integer cents
    signers: list[Signer]      # Active + pending + removed signers
    threshold: int             # N approvals required
    created_at: datetime       # UTC
    status: str                # ACTIVE | FROZEN | CLOSED
    owner_id: str              # Creator's user_id
    total_deposits_cents: int  # Running tally
    total_withdrawals_cents: int
```

### Signer
```python
class Signer:
    id: str                    # UUID v4
    user_id: str               # Link to user table
    wallet_id: str             # FK to wallet
    status: str                # ACTIVE | PENDING | REMOVED
    added_at: datetime         # UTC
    removed_at: datetime | None
    invited_by: str            # user_id of inviter
```

### WithdrawalProposal
```python
class WithdrawalProposal:
    id: str                    # UUID v4
    wallet_id: str             # FK to wallet
    proposer_id: str           # user_id
    amount_cents: int          # Integer cents
    destination_account: str   # Bank account / mobile money number
    description: str
    status: str                # PENDING | APPROVED | REJECTED | EXECUTED | EXPIRED
    approvals_required: int    # Threshold at time of creation
    approvals_gathered: int    # Current count
    created_at: datetime       # UTC
    expires_at: datetime       # UTC (default: +7 days)
    executed_at: datetime | None
    rejected_at: datetime | None
```

### Approval
```python
class Approval:
    id: str
    proposal_id: str
    signer_id: str             # user_id
    action: str                # APPROVED | REJECTED
    created_at: datetime       # UTC
    ip_address: str | None     # Optional audit field
```

### AuditLog
```python
class AuditLog:
    id: str
    wallet_id: str
    actor_id: str              # user_id who performed action
    action: str                # CREATED | DEPOSIT | PROPOSE | APPROVE | REJECT | EXECUTE | SIGNER_ADDED | SIGNER_REMOVED | THRESHOLD_CHANGED
    details: dict              # Context-specific data
    created_at: datetime       # UTC
```

## 4. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST   | /api/v1/wallets | Create wallet |
| GET    | /api/v1/wallets/{wallet_id} | Get wallet details |
| POST   | /api/v1/wallets/{wallet_id}/signers | Add signer |
| DELETE | /api/v1/wallets/{wallet_id}/signers/{user_id} | Remove signer |
| PATCH  | /api/v1/wallets/{wallet_id}/threshold | Update threshold |
| POST   | /api/v1/wallets/{wallet_id}/deposit | Deposit funds |
| POST   | /api/v1/wallets/{wallet_id}/proposals | Propose withdrawal |
| POST   | /api/v1/proposals/{proposal_id}/approve | Approve proposal |
| POST   | /api/v1/proposals/{proposal_id}/reject | Reject proposal |
| POST   | /api/v1/proposals/{proposal_id}/execute | Execute approved proposal |
| GET    | /api/v1/wallets/{wallet_id}/proposals | List proposals |
| GET    | /api/v1/wallets/{wallet_id}/audit-log | Get audit trail |

## 5. N-of-M Escrow Pattern (Pure Python)

### Deposit Flow
```
User → POST /deposit → EscrowService.hold(wallet_id, amount)
  → Wallet.balance += amount
  → AuditLog: DEPOSIT
```

### Withdrawal Flow
```
Signer → POST /propose → ProposalService.propose(...)
  → Check: proposer is active signer
  → Check: amount ≤ wallet.balance
  → EscrowService.lock(wallet_id, proposal_id, amount)
    → Wallet.balance -= amount
    → Proposal.escrowed = amount
  → AuditLog: PROPOSE
  → Approval: auto-approve by proposer

Signer → POST /approve → ProposalService.approve(proposal_id, signer_id)
  → Check: signer is active
  → Check: not already approved/rejected
  → Approval: APPROVED
  → approvals_gathered += 1
  → If approvals_gathered >= threshold:
      → Proposal.status = APPROVED
  → AuditLog: APPROVE

Signer → POST /execute → ProposalService.execute(proposal_id)
  → Check: status == APPROVED
  → EscrowService.release(proposal_id, destination)
  → Proposal.status = EXECUTED
  → AuditLog: EXECUTE
```

### Rejection Flow
```
Signer → POST /reject → ProposalService.reject(proposal_id, signer_id)
  → Check: signer is active
  → If rejections >= (total_active_signers - threshold + 1):
      → Proposal.status = REJECTED
      → EscrowService.return_to_wallet(proposal_id)
  → AuditLog: REJECT
```

## 6. Edge Cases & Rules

### 6.1 Threshold > Signers
- **Rule:** Creating/updating a wallet with threshold > active_signers_count is FORBIDDEN
- **Error:** HTTP 400 "Threshold cannot exceed number of active signers"

### 6.2 All Signers Removed
- **Rule:** A wallet must always retain at least 1 active signer
- **Error:** HTTP 400 "Cannot remove last active signer"
- **Auto-freeze:** If threshold is ever set higher than active signers, wallet status → FROZEN

### 6.3 Double-Approval Prevention
- **Rule:** Each signer may only submit one approval/rejection per proposal
- **Implementation:** Unique constraint on (proposal_id, signer_id) in Approval table
- **Error:** HTTP 409 "You have already responded to this proposal"

### 6.4 Signer Leaving Mid-Proposal
- **Rule:** Signers who are REMOVED after a proposal is created CANNOT approve/reject it
- **Rule:** If removed signer had already approved, their approval remains valid
- **Reason:** Retroactive invalidation creates chaos and potential fund lock
- **Safety:** If removing a signer drops approvals_gathered below threshold, proposal stays APPROVED but execution requires re-verification of active threshold

### 6.5 Proposal Timeout
- **Rule:** Proposals expire after 7 days if not executed
- **On expiry:** Funds returned to wallet, status → EXPIRED
- **AuditLog:** EXPIRED

### 6.6 Race Condition on Simultaneous Approvals
- **Implementation:** Use atomic increment/check pattern
- **Pseudo-code:**
```python
with atomic_lock(proposal_id):
    proposal.approvals_gathered += 1
    if proposal.approvals_gathered >= proposal.approvals_required:
        proposal.status = Status.APPROVED
```

### 6.7 Insufficient Balance
- **Rule:** Propose amount must be ≤ wallet.balance_cents
- **Error:** HTTP 400 "Insufficient funds"

### 6.8 Non-Signer Rejection
- **Rule:** Only active signers can propose, approve, or reject
- **Error:** HTTP 403 "You are not an active signer on this wallet"

## 7. Security Considerations

1. **Audit immutability:** Audit logs are append-only, never deleted
2. **Escrow segregation:** Each proposal's escrow is tracked independently
3. **Threshold immutability during proposal:** approvals_required is snapshotted at proposal creation time
4. **Signer count minimum:** At least 2 signers to create a wallet (prevents single-point-of-failure)
5. **Rate limiting:** Max 10 proposals per wallet per day

## 8. Response Format

All API responses follow:
```json
{
  "status": "success",
  "data": { /* payload */ },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-05-26T01:00:00Z"
  }
}
```

Error responses:
```json
{
  "status": "error",
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Wallet balance (₵50.00) is less than proposed withdrawal (₵100.00)"
  },
  "meta": { ... }
}
```

## 9. Open Questions

1. Should we support SMS/email notifications for pending approvals? → Phase 2
2. Should signers be able to set daily/weekly withdrawal limits? → Phase 2
3. Integration with actual payment rails (MTN MoMo, Vodafone Cash) → Phase 2
