from fastapi import APIRouter, Depends
from app.api.dependencies import get_analytics_service
from app.core.security import require_permission
from app.models.analytics import AnalyticsPayload
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsPayload)
def analytics(
    service: AnalyticsService = Depends(get_analytics_service),
    user: dict = Depends(require_permission("claims:read")),
) -> AnalyticsPayload:
    return service.analytics()
