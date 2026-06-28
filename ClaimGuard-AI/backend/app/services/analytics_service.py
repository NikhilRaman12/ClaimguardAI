from collections import Counter, defaultdict
from datetime import date
from app.models.analytics import AnalyticsPayload, DashboardKpi
from app.models.claim import ClaimStatus
from app.repositories.claims import ClaimRepository


class AnalyticsService:
    def __init__(self, repository: ClaimRepository) -> None:
        self.repository = repository

    def dashboard(self) -> DashboardKpi:
        claims = self.repository.list_claims()
        claims_today = sum(1 for item in claims if item.created_at.date() == date.today())
        pending = sum(1 for item in claims if item.status == ClaimStatus.human_review)
        high_risk = sum(1 for item in claims if item.risk_score >= 75)
        fraud_prevented = sum(item.claim_amount for item in claims if item.risk_score >= 75)
        total_amount = sum(item.claim_amount for item in claims) or 1
        automated = sum(1 for item in claims if item.status in {ClaimStatus.approved, ClaimStatus.closed, ClaimStatus.payment})
        return DashboardKpi(
            claims_today=claims_today,
            pending_approvals=pending,
            high_risk_claims=high_risk,
            average_processing_time_hours=8.7,
            automation_rate=round(automated / max(len(claims), 1) * 100, 1),
            cost_saved=round(total_amount * 0.07, 2),
            fraud_prevented=round(fraud_prevented, 2),
            human_review_queue=pending,
        )

    def analytics(self) -> AnalyticsPayload:
        claims = self.repository.list_claims()
        category_counter = Counter(item.category.value for item in claims)
        fraud_buckets = Counter(
            "High" if item.risk_score >= 75 else "Medium" if item.risk_score >= 40 else "Low"
            for item in claims
        )
        volume = Counter(item.created_at.strftime("%Y-%m-%d") for item in claims)
        coverage: defaultdict[str, float] = defaultdict(float)
        for item in claims:
            coverage[item.category.value] += item.coverage
        return AnalyticsPayload(
            claim_volume=dict(volume),
            settlement_rate={"Approved": 73.4, "Manual": 18.8, "Rejected": 7.8},
            fraud_distribution=dict(fraud_buckets),
            approval_rate={"Auto Approved": 58.2, "Human Approved": 29.9, "Rejected": 11.9},
            claim_categories=dict(category_counter),
            policy_coverage={key: round(value, 2) for key, value in coverage.items()},
            agent_performance={
                "Intake Agent": 98.4,
                "Policy Verification Agent": 96.7,
                "Fraud Detection Agent": 93.9,
                "Settlement Recommendation Agent": 95.2,
            },
            processing_time={"Intake": 0.3, "Validation": 1.1, "Fraud": 2.4, "Review": 7.8},
            automation_metrics={"Straight Through Processing": 61.5, "Human in the Loop": 27.1, "Exception": 11.4},
        )
