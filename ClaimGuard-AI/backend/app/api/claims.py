from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_audit_service, get_claim_service
from app.core.security import require_permission
from app.models.claim import Claim, ClaimCreate, ClaimDecision
from app.services.audit_service import AuditService
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("", response_model=list[Claim])
def list_claims(
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:read")),
) -> list[Claim]:
    return service.list_claims()


@router.post("", response_model=Claim)
def create_claim(
    payload: ClaimCreate,
    service: ClaimService = Depends(get_claim_service),
    audit: AuditService = Depends(get_audit_service),
    user: dict = Depends(require_permission("claims:write")),
) -> Claim:
    claim = service.create_claim(payload)
    audit.record(user["email"], "claim.created", claim.case_id, "success", {"status": claim.status.value})
    return claim


@router.get("/{case_id}", response_model=Claim)
def get_claim(
    case_id: str,
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:read")),
) -> Claim:
    claim = service.get_claim(case_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/{case_id}/process", response_model=Claim)
def process_claim(
    case_id: str,
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:write")),
) -> Claim:
    try:
        return service.process_claim(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{case_id}/decision", response_model=ClaimDecision)
def decision(
    case_id: str,
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:read")),
) -> ClaimDecision:
    try:
        return service.decide(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{case_id}/approve", response_model=Claim)
def approve_claim(
    case_id: str,
    note: str = "Approved by human reviewer.",
    service: ClaimService = Depends(get_claim_service),
    audit: AuditService = Depends(get_audit_service),
    user: dict = Depends(require_permission("approve")),
) -> Claim:
    try:
        claim = service.approve(case_id, user["email"], note)
        audit.record(user["email"], "claim.approved", case_id, "success", {"note": note})
        return claim
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
