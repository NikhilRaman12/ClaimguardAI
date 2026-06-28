from fastapi import APIRouter, Depends
from app.api.dependencies import get_audit_service
from app.core.security import require_permission
from app.models.audit import AuditLog
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=list[AuditLog])
def list_audit_logs(
    service: AuditService = Depends(get_audit_service),
    user: dict = Depends(require_permission("audit:read")),
) -> list[AuditLog]:
    return service.list_events()
