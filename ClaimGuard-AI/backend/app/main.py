import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api import agents, analytics, audit, auth, claims, dashboard, health, reports, settings
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware


def create_app() -> FastAPI:
    configure_logging()
    app_settings = get_settings()
    app = FastAPI(
        title="ClaimGuard AI API",
        version="1.0.0",
        description="Enterprise insurance claims orchestration API",
        openapi_url=f"{app_settings.api_prefix}/openapi.json",
        docs_url=f"{app_settings.api_prefix}/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=app_settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    for router in [
        auth.router,
        claims.router,
        agents.router,
        dashboard.router,
        analytics.router,
        audit.router,
        reports.router,
        settings.router,
        health.router,
    ]:
        app.include_router(router, prefix=app_settings.api_prefix)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "path": str(request.url.path)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger("claimguard.api").exception("Unhandled API error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "path": str(request.url.path)},
        )
    return app


app = create_app()
