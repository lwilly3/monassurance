"""Application FastAPI principale (wiring des routes et middlewares)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from backend.app.api.routes import audit_logs, auth, clients, companies, documents, policies, templates
from backend.app.core.config import get_settings
from backend.app.core.errors import validation_exception_handler
from backend.app.core.logging import ExceptionHandlingMiddleware, RequestLoggerMiddleware

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield
    # Shutdown: rien pour l'instant

app = FastAPI(title="MONASSURANCE API", version="0.1.0", openapi_url="/api/v1/openapi.json", lifespan=lifespan)  # OpenAPI sous /api/v1

app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(audit_logs.router, prefix="/api/v1")

app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
async def health():
    return {"status": "ok"}
