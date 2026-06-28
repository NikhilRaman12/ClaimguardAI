from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "claimguard-api", "timestamp": datetime.now(timezone.utc).isoformat()}
