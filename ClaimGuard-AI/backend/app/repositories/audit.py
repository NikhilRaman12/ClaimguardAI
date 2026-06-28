from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditLog] = []

    def add(self, event: AuditLog) -> AuditLog:
        self.events.insert(0, event)
        return event

    def list_events(self) -> list[AuditLog]:
        return self.events[:500]
