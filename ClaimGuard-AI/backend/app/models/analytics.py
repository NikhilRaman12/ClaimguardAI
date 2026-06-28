from pydantic import BaseModel


class DashboardKpi(BaseModel):
    claims_today: int
    pending_approvals: int
    high_risk_claims: int
    average_processing_time_hours: float
    automation_rate: float
    cost_saved: float
    fraud_prevented: float
    human_review_queue: int


class AnalyticsPayload(BaseModel):
    claim_volume: dict[str, int]
    settlement_rate: dict[str, float]
    fraud_distribution: dict[str, int]
    approval_rate: dict[str, float]
    claim_categories: dict[str, int]
    policy_coverage: dict[str, float]
    agent_performance: dict[str, float]
    processing_time: dict[str, float]
    automation_metrics: dict[str, float]
