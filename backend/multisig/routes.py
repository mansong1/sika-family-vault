"""FastAPI routes for multi-sig group wallet."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from models import (
    AddSignerRequest,
    ApiResponse,
    ApproveRejectRequest,
    CreateWalletRequest,
    DataStore,
    DepositRequest,
    ExecuteRequest,
    ProposeWithdrawalRequest,
    RemoveSignerRequest,
    UpdateThresholdRequest,
)
from services import (
    MultiSigError,
    ProposalService,
    WalletService,
)

router = APIRouter(prefix="/api/v1")


@router.exception_handler(MultiSigError)
async def multisig_exception_handler(request: Request, exc: MultiSigError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            code=exc.code,
            message=exc.message,
            meta={"request_id": getattr(request.state, "request_id", "")},
        ).model_dump(mode="json"),
    )


def _handle(error: MultiSigError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    )


# ---------------------------------------------------------------------------
# Wallets
# ---------------------------------------------------------------------------

@router.post("/wallets", response_model=ApiResponse)
async def create_wallet(req: CreateWalletRequest) -> ApiResponse:
    try:
        wallet = WalletService.create_wallet(req)
        return ApiResponse.success(
            data={
                "wallet": wallet.model_dump(mode="json"),
                "signers": [
                    s.model_dump(mode="json")
                    for s in DataStore.get_wallet_signers(wallet.id)
                ],
            },
            meta={"request_id": wallet.id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.get("/wallets/{wallet_id}", response_model=ApiResponse)
async def get_wallet(wallet_id: str) -> ApiResponse:
    wallet = WalletService.get_wallet(wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail={"code": "WALLET_NOT_FOUND", "message": "Wallet not found"})

    signers = DataStore.get_wallet_signers(wallet_id)
    proposals = DataStore.get_wallet_proposals(wallet_id)
    return ApiResponse.success(
        data={
            "wallet": wallet.model_dump(mode="json"),
            "signers": [s.model_dump(mode="json") for s in signers],
            "proposals": [p.model_dump(mode="json") for p in proposals],
        },
        meta={"request_id": wallet_id},
    )


@router.post("/wallets/{wallet_id}/signers", response_model=ApiResponse)
async def add_signer(wallet_id: str, req: AddSignerRequest) -> ApiResponse:
    try:
        signer = WalletService.add_signer(wallet_id, req.user_id, req.invited_by)
        return ApiResponse.success(
            data={"signer": signer.model_dump(mode="json")},
            meta={"request_id": wallet_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.delete("/wallets/{wallet_id}/signers/{user_id}", response_model=ApiResponse)
async def remove_signer(wallet_id: str, user_id: str, req: RemoveSignerRequest) -> ApiResponse:
    try:
        WalletService.remove_signer(wallet_id, user_id, req.removed_by)
        return ApiResponse.success(
            data={"message": "Signer removed"},
            meta={"request_id": wallet_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.patch("/wallets/{wallet_id}/threshold", response_model=ApiResponse)
async def update_threshold(wallet_id: str, req: UpdateThresholdRequest, updated_by: str) -> ApiResponse:
    try:
        wallet = WalletService.update_threshold(wallet_id, req, updated_by)
        return ApiResponse.success(
            data={"wallet": wallet.model_dump(mode="json")},
            meta={"request_id": wallet_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.post("/wallets/{wallet_id}/deposit", response_model=ApiResponse)
async def deposit(wallet_id: str, req: DepositRequest) -> ApiResponse:
    try:
        wallet = WalletService.deposit(wallet_id, req)
        return ApiResponse.success(
            data={
                "wallet": wallet.model_dump(mode="json"),
                "deposited_cents": req.amount_cents,
            },
            meta={"request_id": wallet_id},
        )
    except MultiSigError as e:
        raise _handle(e)


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

@router.post("/wallets/{wallet_id}/proposals", response_model=ApiResponse)
async def propose_withdrawal(wallet_id: str, req: ProposeWithdrawalRequest) -> ApiResponse:
    try:
        proposal = ProposalService.propose(wallet_id, req)
        return ApiResponse.success(
            data={"proposal": proposal.model_dump(mode="json")},
            meta={"request_id": proposal.id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.post("/proposals/{proposal_id}/approve", response_model=ApiResponse)
async def approve_proposal(proposal_id: str, req: ApproveRejectRequest) -> ApiResponse:
    try:
        proposal = ProposalService.approve(proposal_id, req.signer_id)
        return ApiResponse.success(
            data={"proposal": proposal.model_dump(mode="json")},
            meta={"request_id": proposal_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.post("/proposals/{proposal_id}/reject", response_model=ApiResponse)
async def reject_proposal(proposal_id: str, req: ApproveRejectRequest) -> ApiResponse:
    try:
        proposal = ProposalService.reject(proposal_id, req.signer_id)
        return ApiResponse.success(
            data={"proposal": proposal.model_dump(mode="json")},
            meta={"request_id": proposal_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.post("/proposals/{proposal_id}/execute", response_model=ApiResponse)
async def execute_proposal(proposal_id: str, req: ExecuteRequest) -> ApiResponse:
    try:
        proposal = ProposalService.execute(proposal_id, req.executor_id)
        return ApiResponse.success(
            data={"proposal": proposal.model_dump(mode="json")},
            meta={"request_id": proposal_id},
        )
    except MultiSigError as e:
        raise _handle(e)


@router.get("/wallets/{wallet_id}/proposals", response_model=ApiResponse)
async def list_proposals(wallet_id: str) -> ApiResponse:
    proposals = ProposalService.get_proposals_for_wallet(wallet_id)
    return ApiResponse.success(
        data={"proposals": [p.model_dump(mode="json") for p in proposals]},
        meta={"request_id": wallet_id},
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

@router.get("/wallets/{wallet_id}/audit-log", response_model=ApiResponse)
async def get_audit_log(wallet_id: str) -> ApiResponse:
    logs = DataStore.get_wallet_audit_logs(wallet_id)
    return ApiResponse.success(
        data={"logs": [log.model_dump(mode="json") for log in logs]},
        meta={"request_id": wallet_id},
    )


# Ensure DataStore is available in routes scope
from models import DataStore  # noqa: E402
