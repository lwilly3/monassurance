import os
import pathlib
from typing import Any, Callable, Dict

import pytest

from alembic import command
from alembic.config import Config

# Forcer une base SQLite dédiée aux tests pour éviter de réutiliser monassurance.db
TEST_DB_PATH = pathlib.Path("test_monassurance.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

# Exporter la variable d'environnement avant tout import d'app
os.environ["DATABASE_URL"] = TEST_DB_URL

# Purger le cache des settings afin de prendre en compte la variable d'env
try:
    from backend.app.core import config as app_config
    app_config.get_settings.cache_clear()  # type: ignore[attr-defined]
except Exception:
    # Si le module n'est pas encore importé, ce n'est pas grave
    pass


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: Any) -> None:  # noqa: ANN001
    # Nettoyage du fichier DB de tests s'il existe
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)  # type: ignore[arg-type]
    # Appliquer migrations Alembic sur la base de tests fraîche
    cfg = Config("alembic.ini")
    # Forcer l'URL dans config si besoin
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: Any, exitstatus: int) -> None:  # noqa: ANN001,ARG001
    # Optionnel: nettoyer les artefacts de tests
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


# --- Fixtures helpers auth ---
@pytest.fixture(scope="session")
def admin_headers_factory() -> Callable[[str], dict[str, str]]:
    """Factory de headers admin avec cache par email pour éviter logins répétés."""
    from tests.utils import auth_headers  # import local pour éviter import précoce app
    cache: Dict[str, dict[str, str]] = {}

    def _get(email: str = "admin.fixture@example.com") -> dict[str, str]:
        if email not in cache:
            cache[email] = auth_headers(email)
        return cache[email]

    return _get


@pytest.fixture()
def admin_headers(admin_headers_factory: Callable[[str], dict[str, str]]) -> dict[str, str]:
    """Headers pour un admin par défaut (email stable)."""
    return admin_headers_factory()
