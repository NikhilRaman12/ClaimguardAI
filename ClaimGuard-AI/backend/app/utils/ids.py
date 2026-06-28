from datetime import datetime
from uuid import uuid4


def case_id() -> str:
    return f"CG-{datetime.utcnow().year}-{str(uuid4())[:8].upper()}"


def event_id() -> str:
    return f"EVT-{str(uuid4())[:12].upper()}"
