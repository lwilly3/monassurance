"""Initialisation du logging applicatif et middlewares ASGI simples.

Expose:
 - logger (Loguru) configuré
 - RequestLoggerMiddleware: trace les requêtes HTTP entrantes, ajoute request_id et X-Response-Time
 - ExceptionHandlingMiddleware: capture exceptions non gérées et retourne 500 JSON
 - Compteurs Prometheus optionnels
"""
import sys
from collections.abc import Awaitable
from typing import Any, Callable

from loguru import logger

from backend.app.core.config import get_settings

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None  # type: ignore

# Configuration basique Loguru (stdout, niveau INFO)
logger.remove()
_settings = get_settings()
if _settings.log_json:
    # JSON minimalistique: time, level, message
    logger.add(sys.stdout, level="INFO", serialize=True, backtrace=False, diagnose=False, enqueue=True)
else:
    logger.add(
        sys.stdout,
        level="INFO",
        backtrace=False,
        diagnose=False,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

# Prometheus counters (optionnels)
_REQ_COUNT = None
_REQ_ERRORS = None
if Counter is not None and _settings.enable_metrics:
    _REQ_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    _REQ_ERRORS = Counter("http_errors_total", "Total HTTP 5xx errors", ["path"])  # type: ignore


class RequestLoggerMiddleware:
    def __init__(self, app: Callable[[dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]], Awaitable[Any]]):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:  # type: ignore[override]
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method")
        path = scope.get("path")
        import time
        start = time.time()
        # request_id: header si fourni, sinon généré
        headers = {k.decode().lower(): v.decode() for k, v in (scope.get("headers") or [])}
        settings = get_settings()
        req_id = headers.get(settings.request_id_header.lower()) if settings.request_id_header else None
        if not req_id:
            try:
                import uuid
                req_id = uuid.uuid4().hex
            except Exception:
                req_id = "unknown"
        logger.bind(request_id=req_id).info(f"HTTP {method} {path}")

        async def _send(message: dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                status = message.get("status")
                duration = (time.time() - start) * 1000
                # Injecte l'entête X-Response-Time
                headers = message.get("headers") or []
                try:
                    headers = list(headers)
                    headers.append((b"x-response-time", f"{duration:.1f}ms".encode()))
                    if req_id:
                        headers.append((b"x-request-id", req_id.encode()))
                    message["headers"] = headers
                except Exception:
                    pass
                if duration > settings.http_warn_ms:
                    logger.bind(request_id=req_id).warning(f"HTTP SLOW {method} {path} -> {status} in {duration:.1f}ms")
                else:
                    logger.bind(request_id=req_id).info(f"HTTP {method} {path} -> {status} in {duration:.1f}ms")
                # Prometheus
                try:
                    if _REQ_COUNT is not None:
                        _REQ_COUNT.labels(method=method or "", path=path or "", status=str(status or "")).inc()  # type: ignore
                except Exception:
                    pass
            await send(message)
        await self.app(scope, receive, _send)


class ExceptionHandlingMiddleware:
    def __init__(self, app: Callable[[dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]], Awaitable[Any]]):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:  # type: ignore[override]
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        except Exception:  # pragma: no cover (fallback)
            logger.exception("Unhandled exception")
            from starlette.responses import JSONResponse

            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
            # Metrics
            try:
                path = scope.get("path")
                if _REQ_ERRORS is not None and path:
                    _REQ_ERRORS.labels(path=path).inc()  # type: ignore
            except Exception:
                pass
            await response(scope, receive, send)


__all__ = ["ExceptionHandlingMiddleware", "RequestLoggerMiddleware", "logger"]
