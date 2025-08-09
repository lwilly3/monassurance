"""Configuration centralisée (Pydantic Settings).

Note: signature_keys permet rotation des clés de signature d'URL (kid actif).
"""
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    database_url: str = "sqlite:///./monassurance.db"
    jwt_secret_key: str = "p8qX9VvZr3sWm2FjA0uLxY6DdNeHtKbC"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    redis_url: str = "redis://localhost:6379/0"
    signature_active_kid: str = "k1"
    signature_keys: dict[str, str] = {"k1": "p8qX9VvZr3sWm2FjA0uLxY6DdNeHtKbC"}

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
