from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.api.dependencies import get_claim_service
from app.core.config import get_settings
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health(service: ClaimService = Depends(get_claim_service)) -> dict[str, str | int | bool]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "claimguard-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "auth_required": settings.auth_required,
        "mongo_enabled": settings.use_mongo,
        "claims_available": len(service.list_claims()),
    }
