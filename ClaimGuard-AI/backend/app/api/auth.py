from fastapi import APIRouter, HTTPException, status
from app.core.security import authenticate_user, create_access_token
from app.models.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user["email"], {"role": user["role"], "name": user["name"]})
    return TokenResponse(access_token=token, role=user["role"], name=user["name"])
