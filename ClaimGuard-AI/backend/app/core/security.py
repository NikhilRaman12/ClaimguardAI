from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


USERS = {
    "admin@claimguard.ai": {
        "email": "admin@claimguard.ai",
        "name": "Avery Brooks",
        "role": "admin",
        "hashed_password": pwd_context.hash("ClaimGuard@2026"),
    },
    "adjuster@claimguard.ai": {
        "email": "adjuster@claimguard.ai",
        "name": "Maya Srinivasan",
        "role": "adjuster",
        "hashed_password": pwd_context.hash("Adjuster@2026"),
    },
    "reviewer@claimguard.ai": {
        "email": "reviewer@claimguard.ai",
        "name": "Daniel Cho",
        "role": "reviewer",
        "hashed_password": pwd_context.hash("Reviewer@2026"),
    },
}

ROLE_PERMISSIONS = {
    "admin": {"claims:read", "claims:write", "approve", "audit:read", "settings:write"},
    "adjuster": {"claims:read", "claims:write", "audit:read"},
    "reviewer": {"claims:read", "approve", "audit:read"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, claims: dict[str, Any]) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": subject, "exp": expire, **claims}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    user = USERS.get(email.lower())
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def default_user() -> dict[str, Any]:
    settings = get_settings()
    return {
        "email": settings.demo_actor_email,
        "name": settings.demo_actor_name,
        "role": settings.demo_actor_role,
        "hashed_password": "",
    }


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict[str, Any]:
    settings = get_settings()
    if not token:
        if settings.auth_required:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        return default_user()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        if email is None or email not in USERS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return USERS[email]
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def require_permission(permission: str):
    def checker(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        allowed = ROLE_PERMISSIONS.get(user["role"], set())
        if permission not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker
