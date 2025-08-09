"""Application FastAPI principale (wiring des routes et middlewares)."""
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.api.routes import audit_logs, auth, clients, companies, documents, policies, templates
from backend.app.core.config import get_settings
from backend.app.core.errors import validation_exception_handler
from backend.app.core.logging import ExceptionHandlingMiddleware, RequestLoggerMiddleware
from backend.app.core.redis import get_redis

try:
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    CollectorRegistry = None
    Counter = None
    def generate_latest(_: object | None = None) -> bytes:
        return b""

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: auto-create tables en dev/test pour SQLite
    from backend.app.core.config import get_settings as _gs
    _settings = _gs()
    if _settings.database_url.startswith("sqlite"):
        from sqlalchemy import inspect, text

        from backend.app.db import models  # noqa: F401
        from backend.app.db.base import Base
        from backend.app.db.session import engine
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        if 'policies' in inspector.get_table_names():
            cols = {c['name'] for c in inspector.get_columns('policies')}
            needed = {'status', 'currency'}
            missing = needed - cols
            if missing:
                with engine.begin() as conn:
                    conn.execute(text('DROP TABLE policies'))
                    Base.metadata.tables['policies'].create(bind=conn)
    # (Backfills SQLite retirés; s'appuyer sur Alembic pour tout schéma)
    yield
    # Shutdown: rien pour l'instant

app = FastAPI(title="MONASSURANCE API", version="0.1.0", openapi_url="/api/v1/openapi.json", lifespan=lifespan)  # OpenAPI sous /api/v1

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.middleware("http")
async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Ajoute des en-têtes de sécurité par défaut.

    Remarque: HSTS est pertinent uniquement derrière HTTPS (activable via settings.security_hsts).
    """
    response: Response = await call_next(request)
    # X-Frame-Options
    if settings.security_frame_options:
        response.headers["X-Frame-Options"] = settings.security_frame_options
    # Referrer-Policy
    if settings.security_referrer_policy:
        response.headers["Referrer-Policy"] = settings.security_referrer_policy
    # Content-Security-Policy
    if settings.security_csp:
        response.headers["Content-Security-Policy"] = settings.security_csp
    # HSTS (si activé)
    if settings.security_hsts:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# Rate limiting générique (clé par IP + chemin)
_mem_counts: dict[str, tuple[int, int]] = {}

def _rate_tick(key: str, limit: int) -> bool:
    """Incrémente le compteur pour une clé minute et retourne True si limite dépassée."""
    import time

    minute_bucket = int(time.time()) // 60
    try:
        r = get_redis()
        bucket_key = f"rl:{key}:{minute_bucket}"
        current = r.incr(bucket_key)
        current_i = int(current)
        if current_i == 1:
            r.expire(bucket_key, 65)
        return current_i > limit
    except Exception:
        prev_bucket, count = _mem_counts.get(key, (minute_bucket, 0))
        if prev_bucket != minute_bucket:
            count = 0
            prev_bucket = minute_bucket
        count += 1
        _mem_counts[key] = (prev_bucket, count)
        return count > limit


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Applique un rate limit global par IP+path, avec seuils différents pour /auth/*.

    Exclusions: /health*, /openapi, docs statiques.
    """
    if not settings.rate_limit_enabled:
        return await call_next(request)
    path = request.url.path
    if path.startswith("/health") or path.startswith("/api/v1/openapi") or path.startswith("/docs") or path.startswith("/redoc"):
        return await call_next(request)
    ip = request.client.host if request.client else "unknown"
    is_auth = path.startswith("/api/v1/auth/")
    limit = settings.auth_rate_limit_per_minute if is_auth else settings.default_rate_limit_per_minute
    key = f"{ip}:{path}"
    if _rate_tick(key, limit):
        return Response(status_code=429, content="Trop de requêtes – réessayez plus tard")
    return await call_next(request)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")

app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db() -> dict[str, object]:
    from backend.app.db.session import engine
    db_ok = True
    redis_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    try:
        r = get_redis()
        r.ping()
    except Exception:
        redis_ok = False
    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {"status": status, "database": db_ok, "redis": redis_ok}

@app.get("/metrics")
async def metrics() -> Response:
    if not settings.enable_metrics:
        return Response(status_code=404, content="metrics disabled")
    data = generate_latest(None)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
