"""Configuration centralisée (Pydantic Settings).

Note: signature_keys permet rotation des clés de signature d'URL (kid actif).
"""
from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = {
        "env_file": ".env",
        "case_sensitive": False,
    }
    database_url: str = "sqlite:///./monassurance.db"
    environment: str = "development"  # development, test, production
    jwt_secret_key: str = "p8qX9VvZr3sWm2FjA0uLxY6DdNeHtKbC"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    redis_url: str = "redis://localhost:6379/0"  # alias REDIS_URL accepté
    signature_active_kid: str = "k1"
    signature_keys: dict[str, str] = {"k1": "p8qX9VvZr3sWm2FjA0uLxY6DdNeHtKbC"}
    # DB pool/connexion (PostgreSQL)
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 300  # seconds
    # Observabilité
    slow_query_ms: int = 500
    debug_sql: bool = False
    http_warn_ms: int = 1000
    log_json: bool = False
    request_id_header: str = "X-Request-ID"
    enable_metrics: bool = True
    # CORS & sécurité
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["*"]
    security_hsts: bool = False  # Active Strict-Transport-Security (à activer derrière HTTPS)
    security_csp: str | None = None  # e.g. "default-src 'self'"
    security_frame_options: str = "DENY"  # X-Frame-Options
    security_referrer_policy: str = "no-referrer"
    # Rate limiting
    default_rate_limit_per_minute: int = 120  # limite globale douce pour ne pas gêner les tests
    auth_rate_limit_per_minute: int = 10  # plus strict pour /auth/*
    rate_limit_enabled: bool = False  # désactivé par défaut (activable via env)
    # Tentatives de login (IP / compte)
    login_attempts_enabled: bool = True
    login_attempts_ip_per_minute: int = 30
    login_attempts_account_per_minute: int = 10

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
