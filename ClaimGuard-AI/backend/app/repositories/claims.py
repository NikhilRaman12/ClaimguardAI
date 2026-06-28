from datetime import date, datetime, timedelta, timezone
import random
from typing import Protocol
from app.models.claim import AgentOutput, ApprovalEvent, Claim, ClaimCategory, ClaimCreate, ClaimStatus
from app.utils.ids import case_id


class ClaimRepository(Protocol):
    def list_claims(self) -> list[Claim]: ...
    def get_claim(self, case_id_value: str) -> Claim | None: ...
    def create_claim(self, payload: ClaimCreate) -> Claim: ...
    def update_claim(self, claim: Claim) -> Claim: ...


class InMemoryClaimRepository:
    def __init__(self) -> None:
        self.claims: dict[str, Claim] = {}
        self.seed()

    def seed(self) -> None:
        if self.claims:
            return
        categories = list(ClaimCategory)
        cities = ["Hyderabad", "Mumbai", "Bengaluru", "Chennai", "Pune", "Delhi", "Kolkata", "Ahmedabad"]
        adjusters = ["Maya Srinivasan", "Arjun Mehta", "Sara Williams", "Daniel Cho", "Lena Ortiz"]
        indicators = [
            "Prior similar loss pattern",
            "Claim filed near policy inception",
            "Vendor invoice anomaly",
            "Duplicate bank account match",
            "Location inconsistency",
            "Missing police report",
            "High repair estimate variance",
        ]
        statuses = list(ClaimStatus)
        for index in range(1, 61):
            category = categories[index % len(categories)]
            risk = min(99, max(5, int(random.gauss(45, 24))))
            claim_indicators = random.sample(indicators, k=0 if risk < 35 else 2 if risk < 75 else 4)
            amount = round(random.uniform(1200, 250000), 2)
            coverage = round(amount * random.uniform(1.05, 3.5), 2)
            claim = Claim(
                case_id=f"CG-2026-{index:05d}",
                customer=f"{random.choice(['Aarav', 'Isha', 'Raman', 'Priya', 'Vikram', 'Neha', 'James', 'Sophia'])} {random.choice(['Rao', 'Iyer', 'Sharma', 'Patel', 'Brown', 'Kim'])}",
                policy=f"{category.value[:3].upper().replace(' ', '')}-{random.randint(100000, 999999)}",
                category=category,
                coverage=coverage,
                claim_amount=amount,
                incident_date=date.today() - timedelta(days=random.randint(0, 90)),
                location=random.choice(cities),
                adjuster=random.choice(adjusters),
                status=random.choice(statuses),
                risk_score=risk,
                fraud_indicators=claim_indicators,
                agent_outputs=[
                    AgentOutput(
                        agent="Supervisor Agent",
                        status="completed",
                        confidence=round(random.uniform(0.78, 0.98), 2),
                        explanation="Case routed using policy, fraud, document, and settlement signals.",
                    )
                ],
                approval_history=[
                    ApprovalEvent(actor="system", action="created", note="Claim intake completed.")
                ],
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
            )
            self.claims[claim.case_id] = claim

    def list_claims(self) -> list[Claim]:
        return sorted(self.claims.values(), key=lambda item: item.created_at, reverse=True)

    def get_claim(self, case_id_value: str) -> Claim | None:
        return self.claims.get(case_id_value)

    def create_claim(self, payload: ClaimCreate) -> Claim:
        amount_ratio = payload.claim_amount / payload.coverage
        risk = int(min(95, max(10, amount_ratio * 55 + len(payload.documents) * -3 + random.randint(0, 25))))
        claim = Claim(
            case_id=case_id(),
            customer=payload.customer,
            policy=payload.policy,
            category=payload.category,
            coverage=payload.coverage,
            claim_amount=payload.claim_amount,
            incident_date=payload.incident_date,
            location=payload.location,
            adjuster="Maya Srinivasan",
            status=ClaimStatus.intake,
            risk_score=risk,
            fraud_indicators=[],
            approval_history=[ApprovalEvent(actor="system", action="created", note="Claim received.")],
        )
        self.claims[claim.case_id] = claim
        return claim

    def update_claim(self, claim: Claim) -> Claim:
        claim.updated_at = datetime.now(timezone.utc)
        self.claims[claim.case_id] = claim
        return claim


class MongoClaimRepository(InMemoryClaimRepository):
    def __init__(self, uri: str, database: str) -> None:
        super().__init__()
        self.uri = uri
        self.database = database
        self.client = None
        try:
            from pymongo import MongoClient

            self.client = MongoClient(uri, serverSelectionTimeoutMS=500)
            self.client.admin.command("ping")
            self.collection = self.client[database]["claims"]
            if self.collection.count_documents({}) == 0:
                self.collection.insert_many([claim.model_dump(mode="json") for claim in self.claims.values()])
        except Exception:
            self.client = None

    def list_claims(self) -> list[Claim]:
        if not self.client:
            return super().list_claims()
        return [Claim(**doc) for doc in self.collection.find({}, {"_id": 0}).sort("created_at", -1)]

    def get_claim(self, case_id_value: str) -> Claim | None:
        if not self.client:
            return super().get_claim(case_id_value)
        doc = self.collection.find_one({"case_id": case_id_value}, {"_id": 0})
        return Claim(**doc) if doc else None

    def create_claim(self, payload: ClaimCreate) -> Claim:
        claim = super().create_claim(payload)
        if self.client:
            self.collection.insert_one(claim.model_dump(mode="json"))
        return claim

    def update_claim(self, claim: Claim) -> Claim:
        updated = super().update_claim(claim)
        if self.client:
            self.collection.replace_one({"case_id": claim.case_id}, updated.model_dump(mode="json"), upsert=True)
        return updated
