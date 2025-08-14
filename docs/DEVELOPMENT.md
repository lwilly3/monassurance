# Guide de développement MonAssurance

## Configuration de l'environnement

### Prérequis
- Python 3.11+
- Node.js 18+ (pour le frontend)
- PostgreSQL 14+ (optionnel, SQLite pour dev)
- Redis 6+ (optionnel, fallback en mémoire)

### Installation

1. **Clone et setup Python**
```bash
git clone https://github.com/lwilly3/monassurance.git
cd monassurance
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate     # Windows
pip install -r requirements-dev.txt
```

2. **Configuration environnement**
```bash
cp .env.example .env
# Éditer .env selon vos besoins
```

3. **Base de données**
```bash
# Option 1: SQLite (développement simple)
# Rien à faire, fichier auto-créé

# Option 2: PostgreSQL (recommandé)
docker run -d --name postgres-dev \
  -e POSTGRES_DB=monassurance \
  -e POSTGRES_USER=dev \
  -e POSTGRES_PASSWORD=devpass \
  -p 5432:5432 postgres:16

# Mettre à jour DATABASE_URL dans .env
echo "DATABASE_URL=postgresql://dev:devpass@localhost:5432/monassurance" >> .env
```

4. **Migrations**
```bash
alembic upgrade head
```

5. **Lancement**
```bash
# Backend
uvicorn backend.app.main:app --reload

# Frontend (terminal séparé)
cd frontend
npm install
npm run dev
```

## Structure du projet

```
monassurance/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Routes et endpoints
│   │   │   ├── routes/        # Définition des routes
│   │   │   └── deps.py        # Dépendances FastAPI
│   │   ├── core/              # Configuration et sécurité
│   │   │   ├── config.py      # Settings Pydantic
│   │   │   ├── security.py    # JWT, hash, auth
│   │   │   ├── logging.py     # Logs structurés
│   │   │   └── queue.py       # RQ queue system
│   │   ├── db/                # Base de données
│   │   │   ├── models/        # Modèles SQLAlchemy
│   │   │   ├── session.py     # Configuration DB
│   │   │   └── base.py        # Base classe
│   │   ├── schemas/           # Schémas Pydantic
│   │   ├── services/          # Logique métier
│   │   └── main.py           # Point d'entrée
│   └── tests/                 # Tests pytest
├── frontend/                  # Interface Next.js
│   ├── src/
│   │   ├── app/              # App Router Next.js
│   │   ├── components/       # Composants React
│   │   ├── lib/             # Utilitaires
│   │   └── styles/          # CSS/Tailwind
│   └── tests-e2e/           # Tests Playwright
├── alembic/                  # Migrations DB
├── docs/                     # Documentation
├── scripts/                  # Scripts utilitaires
└── templates_store/          # Stockage templates
```

## Workflows de développement

### 1. Nouvelle fonctionnalité

```bash
# 1. Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# 2. Développer avec TDD
# - Écrire les tests d'abord
# - Implémenter le code
# - Valider les tests

# 3. Valider la qualité
make check-strict  # lint + types + tests + coverage

# 4. Commit et push
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite
```

### 2. Migration de base de données

```bash
# 1. Modifier les modèles dans backend/app/db/models/
# 2. Générer la migration
alembic revision --autogenerate -m "description_changement"

# 3. Vérifier le fichier généré dans alembic/versions/
# 4. Tester la migration
alembic upgrade head
alembic downgrade -1  # Test rollback
alembic upgrade head

# 5. Tests avec nouvelle structure
make test
```

### 3. Nouveau endpoint API

```python
# 1. Définir le schéma (backend/app/schemas/)
class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemRead(ItemCreate):
    id: int
    created_at: datetime

# 2. Créer le modèle (backend/app/db/models/)
class Item(Base):
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

# 3. Ajouter les routes (backend/app/api/routes/)
@router.post("/", response_model=ItemRead)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Item:
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# 4. Tests (tests/)
def test_create_item():
    response = client.post("/api/v1/items/", json={
        "name": "Test Item",
        "description": "Test description"
    }, headers=auth_headers())
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"
```

## Tests

### Types de tests

#### Tests unitaires
```bash
# Tests spécifiques
pytest tests/test_auth.py -v

# Avec coverage
pytest --cov=backend --cov-report=html

# Tests en parallèle
pytest -n auto
```

#### Tests d'intégration
```python
# Exemple: test avec base de données
def test_user_creation_integration(db_session):
    user_data = {"email": "test@example.com", "password": "password"}
    user = create_user(db_session, user_data)
    
    # Vérification en base
    db_user = db_session.query(User).filter(User.email == "test@example.com").first()
    assert db_user is not None
    assert db_user.email == "test@example.com"
```

#### Tests E2E
```typescript
// frontend/tests-e2e/auth.spec.ts
test('complete auth flow', async ({ page }) => {
  await page.goto('/login');
  
  // Login
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');
  
  // Vérification redirection
  await expect(page).toHaveURL('/dashboard');
});
```

### Fixtures et helpers

```python
# conftest.py - fixtures communes
@pytest.fixture
def client():
    """Client de test FastAPI"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers():
    """Headers d'authentification pour tests"""
    def _get_headers(email="test@example.com"):
        token = create_test_token(email)
        return {"Authorization": f"Bearer {token}"}
    return _get_headers

@pytest.fixture
def db_session():
    """Session de base de données pour tests"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

## Debugging

### Configuration IDE

#### VS Code
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["backend.app.main:app", "--reload"],
            "console": "integratedTerminal",
            "env": {
                "DEBUG": "true"
            }
        }
    ]
}
```

#### PyCharm
- Configuration: Python → uvicorn
- Script path: `uvicorn`
- Parameters: `backend.app.main:app --reload`
- Environment: `DEBUG=true`

### Logs et debugging

```python
# Activation logs debug
import logging
logging.getLogger("backend").setLevel(logging.DEBUG)

# Breakpoint conditionnel
import pdb; pdb.set_trace() if DEBUG else None

# Logs structurés
from backend.app.core.logging import logger
logger.info("User action", user_id=user.id, action="create_policy")
```

### Profiling

```bash
# Profile des performances
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn backend.app.main:app

# Analyse mémoire
pip install memory-profiler
mprof run python -m uvicorn backend.app.main:app
mprof plot
```

## Outils de développement

### Makefile targets

```bash
# Développement
make install        # Installation dépendances
make dev           # Lancement dev avec reload
make test          # Tests unitaires
make coverage      # Tests avec coverage

# Qualité
make lint          # Linting (ruff)
make format        # Formatage auto
make type-check    # Vérification types (mypy)
make security      # Analyse sécurité (bandit)
make check-strict  # Validation complète

# Base de données
make db-migrate    # Nouvelle migration
make db-upgrade    # Appliquer migrations
make db-downgrade  # Rollback migration
make db-reset      # Reset complet

# Utilitaires
make clean         # Nettoyage caches
make docs          # Génération documentation
make docker-build  # Build image Docker
```

### Scripts utilitaires

```bash
# Génération de données de test
python scripts/seed_data.py

# Import dashboard Grafana
python scripts/import_grafana_dashboard.py

# Génération badge coverage
python scripts/gen_coverage_badge.py coverage.xml coverage_badge.svg
```

## Conventions de code

### Style Python

```python
# Imports organisation
from __future__ import annotations  # Python 3.11+

# Standard library
import os
from datetime import datetime
from typing import Any

# Third party
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String

# Local
from backend.app.core.config import get_settings
from backend.app.db.models.user import User

# Annotations de types modernes
def process_items(items: list[dict[str, Any]]) -> dict[str, int | str]:
    """Traite une liste d'éléments."""
    pass

# Docstrings style Google
def calculate_premium(
    age: int,
    risk_level: str,
    coverage_amount: float
) -> float:
    """Calcule la prime d'assurance.
    
    Args:
        age: Âge de l'assuré
        risk_level: Niveau de risque ('low', 'medium', 'high')
        coverage_amount: Montant de couverture en euros
        
    Returns:
        Prime mensuelle en euros
        
    Raises:
        ValueError: Si les paramètres sont invalides
    """
    pass
```

### Commits

```bash
# Format conventional commits
feat: nouvelle fonctionnalité
fix: correction de bug
docs: mise à jour documentation
style: formatage, lint
refactor: refactoring sans changement fonctionnel
test: ajout/modification tests
chore: maintenance, configuration

# Exemples
git commit -m "feat(auth): ajouter gestion sessions multiples"
git commit -m "fix(api): corriger validation email dans registration"
git commit -m "docs(readme): mettre à jour guide installation"
```

## Performance et optimisation

### Base de données

```python
# Requêtes optimisées avec eager loading
def get_user_with_policies(user_id: int) -> User:
    return db.query(User).options(
        joinedload(User.clients).joinedload(Client.policies)
    ).filter(User.id == user_id).first()

# Pagination efficace
def list_policies(skip: int = 0, limit: int = 100) -> list[Policy]:
    return db.query(Policy).offset(skip).limit(limit).all()

# Index pour requêtes fréquentes
class Policy(Base):
    __tablename__ = "policies"
    
    policy_number = Column(String, index=True)  # Recherche fréquente
    created_at = Column(DateTime, index=True)   # Tri chronologique
```

### Cache

```python
# Cache Redis pour données fréquentes
from backend.app.core.redis import get_redis

async def get_user_permissions(user_id: int) -> list[str]:
    redis = get_redis()
    cache_key = f"user_permissions:{user_id}"
    
    # Tentative cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Calcul et mise en cache
    permissions = calculate_user_permissions(user_id)
    await redis.setex(cache_key, 300, json.dumps(permissions))
    return permissions
```

### Monitoring

```python
# Métriques custom Prometheus
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('app_request_duration_seconds', 'Request duration')

@REQUEST_DURATION.time()
def process_request():
    REQUEST_COUNT.labels(method='POST', endpoint='/api/v1/policies').inc()
    # ... traitement
```

## Troubleshooting

### Problèmes courants

#### Base de données
```bash
# Erreur de connexion PostgreSQL
ERROR: could not connect to server
SOLUTION: Vérifier que PostgreSQL est démarré et accessible

# Migration en échec
ERROR: relation "table_name" already exists
SOLUTION: Vérifier l'état des migrations avec `alembic current`
          Faire un rollback si nécessaire: `alembic downgrade -1`
```

#### Tests
```bash
# Tests qui échouent après modification DB
SOLUTION: Recréer la base de test: `rm test.db && pytest`

# Coverage insuffisante
SOLUTION: Identifier les lignes non testées: `pytest --cov-report=html`
          Ouvrir htmlcov/index.html pour détails
```

#### Performance
```bash
# API lente
SOLUTION: 1. Vérifier les logs pour requêtes lentes
          2. Profiler avec `py-spy record`
          3. Optimiser les requêtes DB

# Mémoire élevée
SOLUTION: 1. Profiler avec `memory-profiler`
          2. Vérifier les connexions DB non fermées
          3. Optimiser les caches
```
