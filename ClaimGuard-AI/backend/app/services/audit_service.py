from app.models.audit import AuditLog
from app.repositories.audit import AuditRepository
from app.utils.ids import event_id


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self.repository = repository

    def record(self, actor: str, action: str, resource: str, outcome: str, details: dict | None = None) -> AuditLog:
        event = AuditLog(
            event_id=event_id(),
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            details=details or {},
        )
        return self.repository.add(event)

    def list_events(self) -> list[AuditLog]:
        return self.repository.list_events()
