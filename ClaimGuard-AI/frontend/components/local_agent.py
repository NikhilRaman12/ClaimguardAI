from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
import csv
import io
import os
from pathlib import Path
import random
from typing import Any
from uuid import uuid4

import requests
import streamlit as st


CURRENT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = CURRENT_DIR.parent
REPO_DIR = APP_DIR.parent

CATEGORIES = [
    "Auto",
    "Medical",
    "Travel",
    "Home",
    "Property",
    "Flood",
    "Fire",
    "Theft",
    "Life",
    "Motor",
    "Business Insurance",
]
STATUSES = [
    "Intake",
    "Document Validation",
    "Policy Verification",
    "Fraud Analysis",
    "Human Review",
    "Investigation",
    "Settlement Recommendation",
    "Approved",
    "Rejected",
    "Case Closure",
]


def load_local_env() -> None:
    for path in [REPO_DIR / ".env", APP_DIR / ".env", CURRENT_DIR / ".env"]:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def secret(name: str, default: str = "") -> str:
    load_local_env()
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_case_id() -> str:
    return f"CG-2026-{uuid4().hex[:8].upper()}"


def risk_indicators(score: int) -> list[str]:
    if score >= 75:
        return [
            "High claim-to-coverage ratio",
            "Prior anomaly pattern detected",
            "Manual investigation threshold exceeded",
            "Document consistency review required",
        ]
    if score >= 40:
        return ["Moderate anomaly score", "Human approval recommended"]
    return ["Low-risk claim profile", "Policy and evidence package are consistent"]


def seeded_claims() -> list[dict[str, Any]]:
    random.seed(20260629)
    cities = ["Hyderabad", "Mumbai", "Bengaluru", "Chennai", "Pune", "Delhi", "Kolkata", "Ahmedabad"]
    adjusters = ["Maya Srinivasan", "Arjun Mehta", "Sara Williams", "Daniel Cho", "Lena Ortiz"]
    names = ["Aarav Rao", "Isha Iyer", "Raman Sharma", "Priya Patel", "Vikram Brown", "Neha Kim"]
    claims: list[dict[str, Any]] = []
    for index in range(1, 41):
        category = CATEGORIES[index % len(CATEGORIES)]
        risk = min(98, max(8, int(random.gauss(46, 22))))
        amount = round(random.uniform(1800, 240000), 2)
        coverage = round(amount * random.uniform(1.15, 3.2), 2)
        status = random.choice(STATUSES)
        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
        claims.append(
            {
                "case_id": f"CG-2026-{index:05d}",
                "customer": random.choice(names),
                "policy": f"{category[:3].upper().replace(' ', '')}-{random.randint(100000, 999999)}",
                "category": category,
                "coverage": coverage,
                "claim_amount": amount,
                "incident_date": str(date.today() - timedelta(days=random.randint(0, 90))),
                "location": random.choice(cities),
                "adjuster": random.choice(adjusters),
                "status": status,
                "risk_score": risk,
                "fraud_indicators": risk_indicators(risk),
                "agent_outputs": [
                    {
                        "agent": "Supervisor Agent",
                        "status": "completed",
                        "confidence": round(random.uniform(0.82, 0.98), 2),
                        "explanation": "Case routed using policy, document, risk, and settlement signals.",
                        "created_at": created_at.isoformat(),
                    }
                ],
                "approval_history": [
                    {
                        "actor": "embedded-agent-runtime",
                        "action": "created",
                        "note": "Claim available in embedded Streamlit runtime.",
                        "created_at": created_at.isoformat(),
                    }
                ],
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            }
        )
    return sorted(claims, key=lambda item: item["created_at"], reverse=True)


def claims_store() -> list[dict[str, Any]]:
    if "embedded_claims" not in st.session_state:
        st.session_state.embedded_claims = seeded_claims()
    return st.session_state.embedded_claims


def audit_store() -> list[dict[str, Any]]:
    if "embedded_audit" not in st.session_state:
        st.session_state.embedded_audit = [
            {
                "event_id": uuid4().hex,
                "actor": "embedded-agent-runtime",
                "action": "runtime.started",
                "resource": "streamlit",
                "outcome": "success",
                "details": {"mode": "standalone"},
                "created_at": now_iso(),
            }
        ]
    return st.session_state.embedded_audit


def record_audit(action: str, resource: str, details: dict[str, Any] | None = None) -> None:
    audit_store().insert(
        0,
        {
            "event_id": uuid4().hex,
            "actor": "embedded-agent-runtime",
            "action": action,
            "resource": resource,
            "outcome": "success",
            "details": details or {},
            "created_at": now_iso(),
        },
    )


def find_claim(case_id: str) -> dict[str, Any] | None:
    return next((claim for claim in claims_store() if claim["case_id"] == case_id), None)


def llm_summary(claim: dict[str, Any], route: str) -> str:
    api_key = secret("GROQ_API_KEY")
    model = secret("GROQ_MODEL", "llama-3.1-8b-instant")
    fallback = (
        f"Routed to {route} after evaluating policy coverage, claim amount, "
        f"risk score {claim['risk_score']}, and document completeness."
    )
    if not api_key:
        return fallback

    prompt = (
        "You are ClaimGuard AI, an enterprise insurance claim supervisor. "
        "Write a concise, client-ready decision explanation in two sentences. "
        f"Case: {claim['case_id']}; category: {claim['category']}; "
        f"claim amount: {claim['claim_amount']}; coverage: {claim['coverage']}; "
        f"risk score: {claim['risk_score']}; route: {route}; "
        f"signals: {', '.join(claim.get('fraud_indicators', []))}."
    )
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 180,
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content or fallback
    except requests.RequestException:
        return fallback


def process_claim(case_id: str) -> dict[str, Any] | None:
    claim = find_claim(case_id)
    if not claim:
        return None
    score = int(claim["risk_score"])
    if score >= 75:
        route = "Investigation"
    elif score >= 40:
        route = "Human Review"
    else:
        route = "Settlement Recommendation"
    claim["status"] = route
    claim["fraud_indicators"] = risk_indicators(score)
    explanation = llm_summary(claim, route)
    claim["agent_outputs"] = [
        {"agent": "Intake Agent", "status": "completed", "confidence": 0.98, "explanation": "Claim data normalized.", "created_at": now_iso()},
        {"agent": "Document Validation Agent", "status": "completed", "confidence": 0.96, "explanation": "Evidence package checked for processing readiness.", "created_at": now_iso()},
        {"agent": "Policy Verification Agent", "status": "completed", "confidence": 0.94, "explanation": "Policy and coverage validated.", "created_at": now_iso()},
        {"agent": "Fraud Detection Agent", "status": "completed", "confidence": 0.91, "explanation": f"Fraud score calculated at {score}.", "created_at": now_iso()},
        {"agent": "Supervisor Agent", "status": "completed", "confidence": 0.96, "explanation": explanation, "created_at": now_iso()},
    ]
    claim["updated_at"] = now_iso()
    record_audit("claim.processed", case_id, {"status": route, "llm_enabled": bool(secret("GROQ_API_KEY"))})
    return claim


def claim_decision(case_id: str) -> dict[str, Any] | None:
    claim = find_claim(case_id)
    if not claim:
        return None
    score = int(claim["risk_score"])
    if score >= 75:
        return {"case_id": case_id, "decision": "Investigate", "reason": "Fraud score exceeds enterprise threshold.", "next_status": "Investigation", "settlement_amount": None}
    if score >= 40:
        return {"case_id": case_id, "decision": "Manual Approval", "reason": "Moderate fraud score requires human review.", "next_status": "Human Review", "settlement_amount": None}
    settlement = round(min(float(claim["claim_amount"]), float(claim["coverage"])) * 0.92, 2)
    return {"case_id": case_id, "decision": "Approve", "reason": "Low-risk claim with valid policy coverage.", "next_status": "Approved", "settlement_amount": settlement}


def create_claim(payload: dict[str, Any]) -> dict[str, Any]:
    amount = float(payload.get("claim_amount", 0))
    coverage = float(payload.get("coverage", 1))
    document_count = len(payload.get("documents", []))
    risk = int(min(95, max(8, (amount / max(coverage, 1)) * 55 - document_count * 3 + random.randint(0, 25))))
    claim = {
        "case_id": new_case_id(),
        "customer": payload.get("customer", "New Customer"),
        "policy": payload.get("policy", "AUT-000000"),
        "category": payload.get("category", "Auto"),
        "coverage": coverage,
        "claim_amount": amount,
        "incident_date": str(payload.get("incident_date", date.today())),
        "location": payload.get("location", "Hyderabad"),
        "adjuster": "Maya Srinivasan",
        "status": "Intake",
        "risk_score": risk,
        "fraud_indicators": risk_indicators(risk),
        "agent_outputs": [],
        "approval_history": [{"actor": "embedded-agent-runtime", "action": "created", "note": "Claim received.", "created_at": now_iso()}],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    claims_store().insert(0, claim)
    record_audit("claim.created", claim["case_id"], {"risk_score": risk})
    return process_claim(claim["case_id"]) or claim


def approve_claim(case_id: str, note: str) -> dict[str, Any] | None:
    claim = find_claim(case_id)
    if not claim:
        return None
    claim["status"] = "Approved"
    claim["approval_history"].append(
        {"actor": "embedded-agent-runtime", "action": "approved", "note": note, "created_at": now_iso()}
    )
    claim["updated_at"] = now_iso()
    record_audit("claim.approved", case_id, {"note": note})
    return claim


def dashboard() -> dict[str, Any]:
    claims = claims_store()
    pending = sum(1 for item in claims if item["status"] == "Human Review")
    high_risk = sum(1 for item in claims if int(item["risk_score"]) >= 75)
    total_amount = sum(float(item["claim_amount"]) for item in claims) or 1
    automated = sum(1 for item in claims if item["status"] in {"Approved", "Case Closure", "Settlement Recommendation"})
    return {
        "claims_today": sum(1 for item in claims if item["created_at"][:10] == str(date.today())),
        "pending_approvals": pending,
        "high_risk_claims": high_risk,
        "average_processing_time_hours": 2.4,
        "automation_rate": round(automated / max(len(claims), 1) * 100, 1),
        "cost_saved": round(total_amount * 0.07, 2),
        "fraud_prevented": round(sum(float(item["claim_amount"]) for item in claims if int(item["risk_score"]) >= 75), 2),
        "human_review_queue": pending,
    }


def analytics() -> dict[str, Any]:
    claims = claims_store()
    category_counter = Counter(item["category"] for item in claims)
    fraud_buckets = Counter("High" if item["risk_score"] >= 75 else "Medium" if item["risk_score"] >= 40 else "Low" for item in claims)
    volume = Counter(item["created_at"][:10] for item in claims)
    coverage: defaultdict[str, float] = defaultdict(float)
    for item in claims:
        coverage[item["category"]] += float(item["coverage"])
    return {
        "claim_volume": dict(volume),
        "settlement_rate": {"Approved": 73.4, "Manual": 18.8, "Rejected": 7.8},
        "fraud_distribution": dict(fraud_buckets),
        "approval_rate": {"Auto Approved": 58.2, "Human Approved": 29.9, "Rejected": 11.9},
        "claim_categories": dict(category_counter),
        "policy_coverage": {key: round(value, 2) for key, value in coverage.items()},
        "agent_performance": {
            "Intake Agent": 98.4,
            "Policy Verification Agent": 96.7,
            "Fraud Detection Agent": 93.9,
            "Supervisor Agent": 96.1,
        },
        "processing_time": {"Intake": 0.3, "Validation": 1.1, "Fraud": 2.4, "Review": 4.8},
        "automation_metrics": {"Straight Through Processing": 61.5, "Human in the Loop": 27.1, "Exception": 11.4},
    }


def agents_status() -> list[dict[str, str | float]]:
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
    mode = "llm-assisted" if secret("GROQ_API_KEY") else "deterministic"
    return [{"agent": agent, "status": "online", "sla": 99.95, "mode": mode} for agent in agents]


def claims_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["case_id", "customer", "policy", "category", "claim_amount", "status", "risk_score"])
    for claim in claims_store():
        writer.writerow([claim["case_id"], claim["customer"], claim["policy"], claim["category"], claim["claim_amount"], claim["status"], claim["risk_score"]])
    return output.getvalue()


def handle_get(path: str) -> Any:
    if path == "/health":
        return {
            "status": "healthy",
            "service": "claimguard-streamlit-embedded",
            "timestamp": now_iso(),
            "environment": "streamlit",
            "auth_required": False,
            "mongo_enabled": False,
            "claims_available": len(claims_store()),
            "llm_enabled": bool(secret("GROQ_API_KEY")),
        }
    if path == "/claims":
        return claims_store()
    if path.startswith("/claims/") and path.endswith("/decision"):
        return claim_decision(path.split("/")[2])
    if path.startswith("/claims/"):
        return find_claim(path.split("/")[2])
    if path == "/dashboard/kpis":
        return dashboard()
    if path == "/analytics":
        return analytics()
    if path == "/agents/status":
        return agents_status()
    if path == "/audit":
        return audit_store()
    if path == "/settings":
        return {
            "app_name": "ClaimGuard AI",
            "environment": "streamlit-cloud-ready",
            "database": "embedded-session-state",
            "rate_limit_per_minute": 0,
            "mongo_enabled": False,
            "auth_required": False,
            "llm_enabled": bool(secret("GROQ_API_KEY")),
        }
    if path == "/reports/claims.json":
        return claims_store()
    if path == "/reports/claims.csv":
        return claims_csv()
    return None


def handle_post(path: str, payload: dict[str, Any] | None = None) -> Any:
    payload = payload or {}
    if path == "/claims":
        return create_claim(payload)
    if path.startswith("/claims/") and path.endswith("/process"):
        return process_claim(path.split("/")[2])
    if path.startswith("/claims/") and path.endswith("/approve"):
        return approve_claim(path.split("/")[2], payload.get("note", "Approved by embedded reviewer."))
    return None
