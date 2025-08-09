"""Handlers d'exceptions personnalisées (validation Pydantic/FastAPI)."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from loguru import logger
from pydantic import ValidationError


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
    # fallback générique
    return JSONResponse(status_code=500, content={"detail": str(exc)})

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> Response:
    logger.warning(f"Model validation error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

__all__ = ["validation_exception_handler", "pydantic_validation_exception_handler"]
