from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    event_id: str
    actor: str
    action: str
    resource: str
    outcome: str
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
