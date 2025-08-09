"""Handlers d'exceptions personnalisées (validation Pydantic/FastAPI)."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Model validation error: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

__all__ = ["validation_exception_handler", "pydantic_validation_exception_handler"]
