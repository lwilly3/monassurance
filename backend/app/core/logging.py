"""Initialisation du logging applicatif et middlewares ASGI simples.

Expose:
 - logger (Loguru) configuré
 - RequestLoggerMiddleware: trace les requêtes HTTP entrantes
 - ExceptionHandlingMiddleware: capture exceptions non gérées et retourne 500 JSON
"""
import sys
from typing import Any, Awaitable, Callable

from loguru import logger

# Configuration basique Loguru (stdout, niveau INFO)
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    backtrace=False,
    diagnose=False,
    enqueue=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


class RequestLoggerMiddleware:
    def __init__(self, app: Callable[[dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]], Awaitable[Any]]):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:  # type: ignore[override]
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method")
        path = scope.get("path")
        logger.info(f"HTTP {method} {path}")  # Trace minimaliste
        await self.app(scope, receive, send)


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
            await response(scope, receive, send)


__all__ = ["logger", "RequestLoggerMiddleware", "ExceptionHandlingMiddleware"]
