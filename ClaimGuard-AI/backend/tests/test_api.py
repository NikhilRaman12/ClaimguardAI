import os

os.environ["USE_MONGO"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-for-claimguard"

from fastapi.testclient import TestClient
from app.main import create_app


client = TestClient(create_app())


def token() -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@claimguard.ai", "password": "ClaimGuard@2026"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_claims_and_dashboard_are_secured_and_available() -> None:
    auth = {"Authorization": f"Bearer {token()}"}
    claims = client.get("/api/claims", headers=auth)
    assert claims.status_code == 200
    assert len(claims.json()) >= 10
    dashboard = client.get("/api/dashboard/kpis", headers=auth)
    assert dashboard.status_code == 200
    assert "automation_rate" in dashboard.json()


def test_create_claim_runs_orchestration() -> None:
    auth = {"Authorization": f"Bearer {token()}"}
    response = client.post(
        "/api/claims",
        headers=auth,
        json={
            "customer": "Enterprise Customer",
            "policy": "AUT-123456",
            "category": "Auto",
            "coverage": 100000,
            "claim_amount": 24000,
            "incident_date": "2026-06-20",
            "location": "Hyderabad",
            "description": "Insured vehicle collision with validated repair estimate and police report.",
            "documents": ["Policy", "Invoice", "Police Report"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"].startswith("CG-")
    assert payload["status"] in {"Settlement Recommendation", "Human Review", "Investigation", "Rejected"}
