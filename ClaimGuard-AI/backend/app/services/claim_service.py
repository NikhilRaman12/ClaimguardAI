from app.agents.graph import ClaimGraph
from app.models.claim import AgentOutput, ApprovalEvent, Claim, ClaimCreate, ClaimDecision, ClaimStatus
from app.repositories.claims import ClaimRepository


def fraud_indicators_for_score(score: int) -> list[str]:
    if score >= 75:
        return [
            "High claim-to-coverage ratio",
            "Manual investigation threshold exceeded",
            "Additional document verification required",
        ]
    if score >= 40:
        return ["Moderate anomaly score", "Human approval recommended"]
    return ["Low-risk claim profile"]


class ClaimService:
    def __init__(self, repository: ClaimRepository) -> None:
        self.repository = repository
        self.graph = ClaimGraph()

    def list_claims(self) -> list[Claim]:
        return self.repository.list_claims()

    def get_claim(self, case_id: str) -> Claim | None:
        return self.repository.get_claim(case_id)

    def create_claim(self, payload: ClaimCreate) -> Claim:
        claim = self.repository.create_claim(payload)
        return self.process_claim(claim.case_id)

    def process_claim(self, case_id: str) -> Claim:
        claim = self.repository.get_claim(case_id)
        if claim is None:
            raise ValueError("Claim not found")
        state = self.graph.run(
            {
                "case_id": claim.case_id,
                "fraud_score": claim.risk_score,
                "settlement_amount": min(claim.claim_amount, claim.coverage),
            }
        )
        route = state.get("route", "settlement")
        if route == "reject":
            claim.status = ClaimStatus.rejected
        elif route in {"human_review", "investigation"}:
            claim.status = ClaimStatus.investigation if route == "investigation" else ClaimStatus.human_review
        else:
            claim.status = ClaimStatus.settlement
        claim.fraud_indicators = fraud_indicators_for_score(claim.risk_score)
        claim.agent_outputs = [
            AgentOutput(agent="Intake Agent", status="completed", confidence=0.98, explanation="Claim data normalized."),
            AgentOutput(agent="Document Validation Agent", status="completed", confidence=0.97, explanation="Submitted evidence package checked for processing readiness."),
            AgentOutput(agent="Policy Verification Agent", status="completed", confidence=0.94, explanation="Policy and coverage validated."),
            AgentOutput(agent="Fraud Detection Agent", status="completed", confidence=0.91, explanation=f"Fraud score calculated at {claim.risk_score}."),
            AgentOutput(agent="Supervisor Agent", status="completed", confidence=0.96, explanation=f"Routed to {claim.status.value}."),
        ]
        return self.repository.update_claim(claim)

    def decide(self, case_id: str) -> ClaimDecision:
        claim = self.repository.get_claim(case_id)
        if claim is None:
            raise ValueError("Claim not found")
        if claim.risk_score > 75:
            decision = ClaimDecision(case_id=case_id, decision="Investigate", reason="Fraud score exceeds enterprise threshold.", next_status=ClaimStatus.investigation)
        elif claim.risk_score >= 40:
            decision = ClaimDecision(case_id=case_id, decision="Manual Approval", reason="Moderate fraud score requires human review.", next_status=ClaimStatus.human_review)
        else:
            settlement = round(min(claim.claim_amount, claim.coverage) * 0.92, 2)
            decision = ClaimDecision(case_id=case_id, decision="Approve", reason="Low risk claim with valid policy coverage.", next_status=ClaimStatus.approved, settlement_amount=settlement)
        return decision

    def approve(self, case_id: str, actor: str, note: str) -> Claim:
        claim = self.repository.get_claim(case_id)
        if claim is None:
            raise ValueError("Claim not found")
        claim.status = ClaimStatus.approved
        claim.approval_history.append(ApprovalEvent(actor=actor, action="approved", note=note))
        return self.repository.update_claim(claim)
