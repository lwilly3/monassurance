from __future__ import annotations
"""Fournit un client Redis singleton (lru_cache)."""
import redis
from functools import lru_cache
from backend.app.core.config import get_settings

@lru_cache(maxsize=1)
def get_redis():
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
