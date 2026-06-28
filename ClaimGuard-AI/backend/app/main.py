from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        allow_credentials=True,
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
    return app


app = create_app()
