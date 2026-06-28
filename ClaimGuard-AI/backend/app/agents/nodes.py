from app.agents.state import ClaimState


def intake_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Intake"
    state["explanation"] = "Claim intake validated and normalized."
    return state


def document_validation_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Document Validation"
    state["documents_valid"] = True
    return state


def ocr_processing_agent(state: ClaimState) -> ClaimState:
    state["status"] = "OCR"
    return state


def policy_verification_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Policy Verification"
    state["policy_valid"] = state.get("settlement_amount", 0) >= 0
    return state


def fraud_detection_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Fraud Analysis"
    return state


def duplicate_claim_detection_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Duplicate Claim Detection"
    return state


def compliance_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Compliance Review"
    return state


def supervisor_agent(state: ClaimState) -> ClaimState:
    if not state.get("documents_valid", False):
        state["route"] = "human_review"
    elif not state.get("policy_valid", True):
        state["route"] = "reject"
    elif state.get("fraud_score", 0) > 75:
        state["route"] = "investigation"
    elif state.get("fraud_score", 0) >= 40:
        state["route"] = "human_review"
    else:
        state["route"] = "settlement"
    return state


def human_review_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Human Review"
    state["decision"] = "manual approval required"
    return state


def settlement_recommendation_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Settlement Recommendation"
    state["decision"] = "approve"
    return state


def audit_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Audit Logged"
    return state


def notification_agent(state: ClaimState) -> ClaimState:
    state["status"] = "Notification Queued"
    return state
