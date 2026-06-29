import time
from uuid import uuid4
from collections import defaultdict, deque
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        settings = get_settings()
        client = request.client.host if request.client else "unknown"
        now = time.time()
        window = self.requests[client]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            return JSONResponse(
                {"detail": "Rate limit exceeded", "request_id": request.state.request_id},
                status_code=429,
            )
        window.append(now)
        return await call_next(request)
