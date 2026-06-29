from fastapi import APIRouter, Depends
from app.core.config import get_settings
from app.core.security import require_permission

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("")
def settings(user: dict = Depends(require_permission("claims:read"))) -> dict[str, str | int | bool]:
    app_settings = get_settings()
    return {
        "app_name": app_settings.app_name,
        "environment": app_settings.environment,
        "database": app_settings.mongodb_database,
        "rate_limit_per_minute": app_settings.rate_limit_per_minute,
        "mongo_enabled": app_settings.use_mongo,
        "auth_required": app_settings.auth_required,
    }
