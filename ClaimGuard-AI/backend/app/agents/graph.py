from app.agents.nodes import (
    audit_agent,
    compliance_agent,
    document_validation_agent,
    duplicate_claim_detection_agent,
    fraud_detection_agent,
    human_review_agent,
    intake_agent,
    notification_agent,
    ocr_processing_agent,
    policy_verification_agent,
    settlement_recommendation_agent,
    supervisor_agent,
)
from app.agents.state import ClaimState


def route_from_supervisor(state: ClaimState) -> str:
    return state.get("route", "settlement")


class ClaimGraph:
    def __init__(self) -> None:
        self.compiled = None
        try:
            from langgraph.graph import END, StateGraph

            graph = StateGraph(ClaimState)
            graph.add_node("intake", intake_agent)
            graph.add_node("document_validation", document_validation_agent)
            graph.add_node("ocr", ocr_processing_agent)
            graph.add_node("policy_verification", policy_verification_agent)
            graph.add_node("fraud_detection", fraud_detection_agent)
            graph.add_node("duplicate_detection", duplicate_claim_detection_agent)
            graph.add_node("compliance", compliance_agent)
            graph.add_node("supervisor", supervisor_agent)
            graph.add_node("human_review", human_review_agent)
            graph.add_node("settlement", settlement_recommendation_agent)
            graph.add_node("audit", audit_agent)
            graph.add_node("notification", notification_agent)
            graph.set_entry_point("intake")
            graph.add_edge("intake", "document_validation")
            graph.add_edge("document_validation", "ocr")
            graph.add_edge("ocr", "policy_verification")
            graph.add_edge("policy_verification", "fraud_detection")
            graph.add_edge("fraud_detection", "duplicate_detection")
            graph.add_edge("duplicate_detection", "compliance")
            graph.add_edge("compliance", "supervisor")
            graph.add_conditional_edges(
                "supervisor",
                route_from_supervisor,
                {
                    "human_review": "human_review",
                    "investigation": "human_review",
                    "reject": "audit",
                    "settlement": "settlement",
                },
            )
            graph.add_edge("human_review", "audit")
            graph.add_edge("settlement", "audit")
            graph.add_edge("audit", "notification")
            graph.add_edge("notification", END)
            self.compiled = graph.compile()
        except Exception:
            self.compiled = None

    def run(self, state: ClaimState) -> ClaimState:
        if self.compiled:
            return self.compiled.invoke(state)
        for node in [
            intake_agent,
            document_validation_agent,
            ocr_processing_agent,
            policy_verification_agent,
            fraud_detection_agent,
            duplicate_claim_detection_agent,
            compliance_agent,
            supervisor_agent,
        ]:
            state = node(state)
        route = state.get("route")
        state = human_review_agent(state) if route in {"human_review", "investigation"} else settlement_recommendation_agent(state)
        state = audit_agent(state)
        return notification_agent(state)
