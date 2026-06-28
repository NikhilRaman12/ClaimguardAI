from typing import TypedDict


class ClaimState(TypedDict, total=False):
    case_id: str
    status: str
    documents_valid: bool
    policy_valid: bool
    fraud_score: int
    retries: int
    decision: str
    settlement_amount: float
    explanation: str
    route: str
