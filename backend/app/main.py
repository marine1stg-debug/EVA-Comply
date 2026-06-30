from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.core.client_context import client_id_ctx
from app.core.config import settings
from app.api import auth, frameworks, controls, evidence, users, tenants, billing, reports, dashboard, review, msp, audit, plans, platform, promos, policy, maturity, llm_settings, recommendations, support, notifications, partners, videos, marketplace, backup, agreement, improvements, email_settings, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("EVA Portal API starting up...")
    yield
    # Shutdown
    print("EVA Portal API shutting down...")


_PROD = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="EVA Cybersecurity Audit Portal API",
    description="Multi-tenant SaaS platform for cybersecurity compliance management",
    version="1.0.0",
    lifespan=lifespan,
    # Hide the interactive API schema in production (it would expose the full
    # surface to anyone past the basic-auth gate). Available in development.
    docs_url=None if _PROD else "/docs",
    redoc_url=None if _PROD else "/redoc",
    openapi_url=None if _PROD else "/openapi.json",
)

# CORS - explicit origins, methods, and headers (no wildcards with credentials).
# In production the SPA is served same-origin via the proxy, so CORS rarely
# applies; the prod origin is included for completeness.
_cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:80",
]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_URL.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Client-Id", "X-Lang"],
)


@app.middleware("http")
async def client_context_middleware(request: Request, call_next):
    """Capture the reviewer's selected client (X-Client-Id) for this request."""
    token = client_id_ctx.set(request.headers.get("x-client-id"))
    try:
        return await call_next(request)
    finally:
        client_id_ctx.reset(token)

# ── Routers ──────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Authentication"])
app.include_router(dashboard.router,  prefix="/api/v1/dashboard",   tags=["Dashboard"])
app.include_router(review.router,     prefix="/api/v1/review",      tags=["Review"])
app.include_router(msp.router,        prefix="/api/v1/msp",         tags=["MSP"])
app.include_router(audit.router,      prefix="/api/v1/audit",       tags=["Audit"])
app.include_router(plans.router,      prefix="/api/v1/plans",       tags=["Plans"])
app.include_router(platform.router,   prefix="/api/v1/platform",    tags=["Platform"])
app.include_router(promos.router,     prefix="/api/v1/promos",      tags=["Promo codes"])
app.include_router(policy.router,     prefix="/api/v1/policy-templates", tags=["Policy templates"])
app.include_router(frameworks.router, prefix="/api/v1/frameworks",  tags=["Frameworks"])
app.include_router(controls.router,   prefix="/api/v1/controls",    tags=["Controls"])
app.include_router(evidence.router,   prefix="/api/v1/evidence",    tags=["Evidence"])
app.include_router(users.router,      prefix="/api/v1/users",       tags=["Users"])
app.include_router(tenants.router,    prefix="/api/v1/tenants",     tags=["Tenants"])
app.include_router(billing.router,    prefix="/api/v1/billing",     tags=["Billing"])
app.include_router(reports.router,    prefix="/api/v1/reports",     tags=["Reports"])
app.include_router(maturity.router,   prefix="/api/v1/maturity",    tags=["Maturity"])
app.include_router(llm_settings.router, prefix="/api/v1/llm",       tags=["LLM connector"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(support.router,    prefix="/api/v1/support",       tags=["Support"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(partners.router,   prefix="/api/v1/partners",    tags=["Partners"])
app.include_router(videos.router,     prefix="/api/v1/videos",      tags=["Training videos"])
app.include_router(marketplace.router, prefix="/api/v1/marketplace", tags=["Marketplace"])
app.include_router(backup.router,     prefix="/api/v1/backup",      tags=["Backup & Restore"])
app.include_router(agreement.router,  prefix="/api/v1/agreement",   tags=["Agreement"])
app.include_router(improvements.router, prefix="/api/v1/improvements", tags=["Improvement requests"])
app.include_router(email_settings.router, prefix="/api/v1/email-settings", tags=["Email settings"])
app.include_router(system.router,     prefix="/api/v1/system",      tags=["System"])


@app.get("/")
async def root():
    return {"message": "EVA Portal API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
