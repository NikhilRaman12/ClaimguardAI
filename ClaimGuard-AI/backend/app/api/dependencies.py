from functools import lru_cache
from app.core.config import get_settings
from app.repositories.audit import AuditRepository
from app.repositories.claims import ClaimRepository, InMemoryClaimRepository, MongoClaimRepository
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.claim_service import ClaimService


@lru_cache
def get_claim_repository() -> ClaimRepository:
    settings = get_settings()
    if settings.use_mongo:
        return MongoClaimRepository(settings.mongodb_uri, settings.mongodb_database)
    return InMemoryClaimRepository()


@lru_cache
def get_audit_repository() -> AuditRepository:
    return AuditRepository()


def get_claim_service() -> ClaimService:
    return ClaimService(get_claim_repository())


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(get_claim_repository())


def get_audit_service() -> AuditService:
    return AuditService(get_audit_repository())
