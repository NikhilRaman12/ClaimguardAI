from fastapi import APIRouter, Depends
from app.core.security import require_permission

router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.get("/status")
def agent_status(user: dict = Depends(require_permission("claims:read"))) -> list[dict[str, str | float]]:
    agents = [
        "Intake Agent",
        "Document Validation Agent",
        "OCR Processing Agent",
        "Policy Verification Agent",
        "Fraud Detection Agent",
        "Duplicate Claim Detection Agent",
        "Settlement Recommendation Agent",
        "Human Review Agent",
        "Compliance Agent",
        "Audit Agent",
        "Notification Agent",
        "Supervisor Agent",
    ]
    return [{"agent": agent, "status": "online", "sla": 99.95, "mode": "orchestrated"} for agent in agents]
