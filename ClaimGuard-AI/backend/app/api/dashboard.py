from fastapi import APIRouter, Depends
from app.api.dependencies import get_analytics_service
from app.core.security import require_permission
from app.models.analytics import DashboardKpi
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=DashboardKpi)
def kpis(
    service: AnalyticsService = Depends(get_analytics_service),
    user: dict = Depends(require_permission("claims:read")),
) -> DashboardKpi:
    return service.dashboard()
