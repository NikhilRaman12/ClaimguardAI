import csv
import io
import json
from fastapi import APIRouter, Depends, Response
from app.api.dependencies import get_claim_service
from app.core.security import require_permission
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/claims.csv")
def claims_csv(
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:read")),
) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["case_id", "customer", "policy", "category", "claim_amount", "status", "risk_score"])
    for claim in service.list_claims():
        writer.writerow([claim.case_id, claim.customer, claim.policy, claim.category.value, claim.claim_amount, claim.status.value, claim.risk_score])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=claims.csv"})


@router.get("/claims.json")
def claims_json(
    service: ClaimService = Depends(get_claim_service),
    user: dict = Depends(require_permission("claims:read")),
) -> Response:
    payload = [claim.model_dump(mode="json") for claim in service.list_claims()]
    return Response(json.dumps(payload, indent=2), media_type="application/json")


@router.get("/executive.pdf")
def executive_pdf(user: dict = Depends(require_permission("claims:read"))) -> Response:
    pdf_bytes = b"%PDF-1.4\n% ClaimGuard AI Executive Report\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF"
    return Response(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=executive-report.pdf"})
