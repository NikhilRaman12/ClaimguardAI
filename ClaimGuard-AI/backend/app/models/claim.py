from datetime import date, datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ClaimStatus(str, Enum):
    intake = "Intake"
    document_validation = "Document Validation"
    ocr = "OCR"
    policy_verification = "Policy Verification"
    fraud_analysis = "Fraud Analysis"
    human_review = "Human Review"
    investigation = "Investigation"
    settlement = "Settlement Recommendation"
    payment = "Payment Authorization"
    rejected = "Rejected"
    closed = "Case Closure"
    approved = "Approved"


class ClaimCategory(str, Enum):
    auto = "Auto"
    medical = "Medical"
    travel = "Travel"
    home = "Home"
    property = "Property"
    flood = "Flood"
    fire = "Fire"
    theft = "Theft"
    life = "Life"
    motor = "Motor"
    business = "Business Insurance"


class AgentOutput(BaseModel):
    agent: str
    status: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalEvent(BaseModel):
    actor: str
    action: str
    note: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClaimCreate(BaseModel):
    customer: str = Field(min_length=2, max_length=120)
    policy: str = Field(pattern=r"^[A-Z]{2,4}-\d{6,10}$")
    category: ClaimCategory
    coverage: float = Field(gt=0)
    claim_amount: float = Field(gt=0)
    incident_date: date
    location: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=10, max_length=2000)
    documents: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    case_id: str
    customer: str
    policy: str
    category: ClaimCategory
    coverage: float
    claim_amount: float
    incident_date: date
    location: str
    adjuster: str
    status: ClaimStatus
    risk_score: int = Field(ge=0, le=100)
    fraud_indicators: list[str] = Field(default_factory=list)
    agent_outputs: list[AgentOutput] = Field(default_factory=list)
    approval_history: list[ApprovalEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClaimDecision(BaseModel):
    case_id: str
    decision: str
    reason: str
    next_status: ClaimStatus
    settlement_amount: float | None = None
