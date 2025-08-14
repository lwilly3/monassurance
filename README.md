# MonAssurance SaaS Platform

![Coverage](coverage_badge.svg)
![CI](https://github.com/lwilly3/monassurance/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/lwilly3/monassurance/branch/main/graph/badge.svg)](https://codecov.io/gh/lwilly3/monassurance)

## 🏢 Vue d'ensemble

**MonAssurance** est une plateforme SaaS moderne de gestion d'assurance qui permet aux professionnels de gérer leurs clients, polices d'assurance, et de générer automatiquement des documents contractuels.

### ✨ Fonctionnalités principales

- 🔐 **Authentification sécurisée** avec JWT et refresh tokens rotatifs
- 👥 **Gestion multi-utilisateurs** avec système de rôles (USER, MANAGER, ADMIN, SUPERADMIN)
- 📋 **Gestion clients et polices** avec interface intuitive
- 📄 **Templates versionnés** pour génération de documents
- 🚀 **Génération PDF/Excel** automatisée et asynchrone
- 🔗 **URLs signées** pour téléchargements sécurisés
- 📊 **Audit complet** de toutes les actions
- 🛡️ **Rate limiting** et protection contre les attaques
- 📈 **Métriques Prometheus** intégrées
- 🔄 **Stockage multi-backend** (Local, S3, Google Drive)

## 🏗️ Architecture

### Stack technologique

**Backend:**
- FastAPI (Python 3.11+) - API REST haute performance
- SQLAlchemy 2.x - ORM moderne avec support async
- PostgreSQL - Base de données principale
- Redis - Cache et queue système
- Alembic - Migrations de base de données

**Frontend:**
- Next.js 14+ - Framework React full-stack
- TypeScript - Typage statique
- Tailwind CSS - Framework CSS utilitaire
- Playwright - Tests end-to-end

**DevOps:**
- Docker - Containerisation
- GitHub Actions - CI/CD
- Pytest - Tests avec 86%+ de couverture
- Ruff, MyPy, Bandit - Qualité de code

### Architecture modulaire

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                        │
│              Interface utilisateur                         │
├─────────────────────────────────────────────────────────────┤
│                 API Layer (FastAPI)                        │
│            Routes REST │ Authentification                  │
├─────────────────────────────────────────────────────────────┤
│                Business Logic Layer                        │
│        Services │ Templates │ Documents                    │
├─────────────────────────────────────────────────────────────┤
│                  Storage Layer                             │
│     PostgreSQL │ Redis │ File Storage                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Démarrage rapide

### Prérequis

- Python 3.11+
- Node.js 18+ (pour le frontend)
- PostgreSQL 14+ (optionnel, SQLite pour développement)
- Redis 6+ (optionnel, fallback en mémoire)

### Installation

1. **Cloner le repository**
```bash
git clone https://github.com/lwilly3/monassurance.git
cd monassurance
```

2. **Setup Backend**
```bash
# Environnement virtuel Python
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installation des dépendances
pip install -r requirements-dev.txt

# Configuration
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

# Appliquer les migrations
alembic upgrade head
```

4. **Lancer l'application**
```bash
# Backend API
make dev
# ou: uvicorn backend.app.main:app --reload

# Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

### Accès

- **API Documentation**: http://localhost:8000/docs
- **Interface Web**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | Vue d'ensemble de l'architecture système |
| [Guide développement](docs/DEVELOPMENT.md) | Setup environnement et workflows |
| [Documentation API](docs/API.md) | Référence complète de l'API REST |
| [Workflow](docs/WORKFLOW.md) | Processus métier et cas d'usage |
| [Maintenance](docs/MAINTENANCE.md) | Guide d'exploitation et monitoring |

## 🛠️ Commandes utiles

### Développement
```bash
make install        # Installation complète
make dev           # Lancement avec reload
make test          # Tests unitaires
make coverage      # Tests avec couverture
```

### Qualité de code
```bash
make lint          # Vérification syntaxe (Ruff)
make format        # Formatage automatique
make type-check    # Vérification types (MyPy)
make security      # Analyse sécurité (Bandit)
make check-strict  # Validation complète (CI)
```

### Base de données
```bash
make db-migrate    # Nouvelle migration
make db-upgrade    # Appliquer migrations
make db-downgrade  # Rollback migration
make db-reset      # Reset complet
```

## 🧪 Tests
### Stratégie de test

- **Tests unitaires**: 40+ tests avec 86%+ de couverture
- **Tests d'intégration**: API endpoints et base de données
- **Tests E2E**: Workflows complets avec Playwright
- **Tests de sécurité**: Analyse statique avec Bandit

```bash
# Tests unitaires
pytest tests/ -v

# Tests avec couverture
pytest --cov=backend --cov-report=html

# Tests E2E
cd frontend
npm run test:e2e

# Tests de sécurité
make security
```

## 🔒 Sécurité

### Authentification
- **JWT avec refresh tokens rotatifs** pour prévenir la compromission
- **Hachage bcrypt** des mots de passe (12 rounds minimum)
- **Sessions multi-appareils** avec gestion granulaire
- **Révocation de tokens** individuelle ou globale

### Protection des données
- **URLs signées** pour téléchargements sécurisés
- **Rate limiting** configurable par endpoint
- **Validation stricte** des entrées utilisateur
- **Isolation des données** par utilisateur/organisation

### Monitoring et audit
- **Logs d'audit** complets de toutes les actions
- **Métriques de sécurité** avec alerting
- **Headers de sécurité** (HSTS, CSP, etc.)
- **Protection CSRF/XSS** intégrée

## 📊 Observabilité

### Métriques Prometheus

- **Métriques applicatives**: requêtes, erreurs, latence
- **Métriques métier**: polices créées, documents générés
- **Métriques infrastructure**: base de données, Redis, file storage

```bash
# Export des métriques
curl http://localhost:8000/metrics
```

### Logs structurés

```json
{
  "timestamp": "2024-01-15T10:00:00Z",
  "level": "INFO",
  "message": "Policy created",
  "request_id": "req_abc123",
  "user_id": 1,
  "policy_id": 456,
  "duration_ms": 125
}
```

### Health checks

```bash
# Santé générale
curl http://localhost:8000/health

# Santé base de données
curl http://localhost:8000/health/db
```

## 🚀 Déploiement

### Environnements

| Environnement | Base de données | Cache | Stockage |
|---------------|----------------|-------|----------|
| **Development** | SQLite | Mémoire | Local |
| **Staging** | PostgreSQL | Redis | S3 |
| **Production** | PostgreSQL HA | Redis Cluster | S3 + CDN |

### Docker

```bash
# Build de l'image
docker build -t monassurance:latest .

# Lancement avec Docker Compose
docker-compose up -d

# Variables d'environnement
docker run -e DATABASE_URL=postgresql://... monassurance:latest
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL de connexion PostgreSQL | SQLite local |
| `REDIS_URL` | URL de connexion Redis | Fallback mémoire |
| `SECRET_KEY` | Clé secrète JWT | Généré |
| `CORS_ORIGINS` | Origines CORS autorisées | localhost |
| `LOG_LEVEL` | Niveau de logs | INFO |

## 🤝 Contribution

### Workflow

1. **Fork** du repository
2. **Branche** pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. **Commit** avec messages conventionnels (`git commit -m 'feat: add amazing feature'`)
4. **Tests** et validation qualité (`make check-strict`)
5. **Push** vers votre branche (`git push origin feature/amazing-feature`)
6. **Pull Request** avec description détaillée

### Standards de code

- **Python**: PEP 8 avec Ruff
- **TypeScript**: Standard avec ESLint
- **Commits**: Conventional Commits
- **Tests**: Couverture minimale 85%
- **Documentation**: Docstrings et README à jour

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

## 🆘 Support

### Issues et bugs
- [GitHub Issues](https://github.com/lwilly3/monassurance/issues)

### Documentation
- [Wiki du projet](https://github.com/lwilly3/monassurance/wiki)
- [API Reference](docs/API.md)

### Contact
- Email: support@monassurance.com
- Slack: [#monassurance](https://workspace.slack.com/channels/monassurance)

---

**MonAssurance** - Simplifiez la gestion de vos assurances avec une plateforme moderne et sécurisée.

## 🗂️ Structure du projet

```
monassurance/
├── 📁 backend/                 # API FastAPI
│   ├── 📁 app/
│   │   ├── 📁 api/            # Routes et endpoints
│   │   ├── 📁 core/           # Configuration et sécurité
│   │   ├── 📁 db/             # Modèles et base de données
│   │   ├── 📁 schemas/        # Schémas Pydantic
│   │   ├── 📁 services/       # Logique métier
│   │   └── 📄 main.py         # Point d'entrée API
│   └── 📁 tests/              # Tests backend
├── 📁 frontend/               # Interface Next.js
│   ├── 📁 src/
│   │   ├── 📁 app/           # App Router Next.js
│   │   ├── 📁 components/    # Composants React
│   │   └── 📁 lib/           # Utilitaires
│   └── 📁 tests-e2e/         # Tests Playwright
├── 📁 docs/                   # Documentation
├── 📁 scripts/               # Scripts utilitaires
├── 📁 alembic/               # Migrations DB
├── 📄 Makefile               # Commandes de développement
├── 📄 docker-compose.yml     # Services Docker
└── 📄 README.md              # Ce fichier
```
	- Seuils configurables: `SLOW_QUERY_MS` (requêtes SQL lentes), `HTTP_WARN_MS` (latence HTTP). `DEBUG_SQL` active l’echo SQLAlchemy (dev).
- Health
	- `GET /health`: ping simple.
	- `GET /health/db`: statut détaillé `{status: ok|degraded, database: bool, redis: bool}`.
- Metrics (Prometheus)
	- `GET /metrics` (activable avec `ENABLE_METRICS=true`, activé par défaut) expose des compteurs HTTP (totaux et erreurs).
	- Exemple de scrape Prometheus:

```yaml
scrape_configs:
	- job_name: monassurance
		metrics_path: /metrics
		static_configs:
			- targets: ["localhost:8000"]
```

#### Try it — Health & Metrics (local)

```bash
# Health simple
curl -s http://127.0.0.1:8000/health | jq

# Health détaillé DB + Redis
curl -s http://127.0.0.1:8000/health/db | jq

# Metrics Prometheus
curl -s http://127.0.0.1:8000/metrics | head -n 20
```

Notes maintenance:
- Variables d’environnement utiles (voir .env.example): LOG_JSON, REQUEST_ID_HEADER, ENABLE_METRICS, SLOW_QUERY_MS, HTTP_WARN_MS, DEBUG_SQL.
- Pour la corrélation, envoyez `X-Request-ID` dans la requête: il sera renvoyé en réponse et inclus dans les logs.

## Variables d'environnement principales

| Nom | Description | Défaut |
|-----|-------------|--------|
| `DATABASE_URL` | URL SQLAlchemy PostgreSQL/SQLite | `sqlite:///./monassurance.db` |
| `JWT_SECRET_KEY` | Clé secrète JWT | (générer) |
| `JWT_ALGORITHM` | Algo token | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée tokens | 30 |

## Modèles initiaux

- Utilisateur (User) avec rôles (Role)
- Compagnie (Company)
- Client (Client)
- Police d'assurance (Policy)

## Migrations

L'initialisation crée les tables de base. Ajouter de nouveaux modèles => générer migration:
```bash
alembic revision --autogenerate -m "ajout nouvelle table"
alembic upgrade head
```

## Docker (backend + PostgreSQL)

```bash
docker compose build
docker compose up -d
```

API: http://localhost:8000/docs

Arrêt:
```bash
docker compose down
```

Regénérer migrations dans le conteneur:
```bash
docker compose exec backend alembic revision --autogenerate -m "change"
docker compose exec backend alembic upgrade head
```

CI avec PostgreSQL:
- Un job GitHub Actions démarre un service Postgres 16, applique `alembic upgrade head`, puis exécute les tests sur Postgres. La couverture est uploadée avec un flag `postgres`.

## Migration SQLite → PostgreSQL (dev/staging)

Étapes recommandées:

1) Préparer l'environnement
- Copier `.env.example` vers `.env` et définir `DATABASE_URL=postgresql+psycopg2://monassurance:devpass@localhost:5432/monassurance`.
- Démarrer Postgres local: `docker compose up -d db` (ou votre instance managée).

2) Appliquer le schéma sur Postgres
- Exécuter les migrations Alembic sur la nouvelle base:
	```bash
	alembic upgrade head
	```

3) Démarrage de l'API avec Postgres
- Lancer l'API avec la même `DATABASE_URL` Postgres. Avec Docker Compose, le service backend exécute `alembic upgrade head` automatiquement au démarrage.

4) Données existantes (optionnel)
- Pour migrer les données SQLite → Postgres, utilisez un outil dédié (ex: `sqlite3` dump + `pgloader`) ou un script ETL application.

Notes Postgres:
- Les colonnes `sa.JSON()` sont stockées en JSONB sur PostgreSQL et peuvent bénéficier d'index GIN si vous filtrez par clés.
- Un index composite existe sur `audit_logs(action, object_type, created_at)` pour accélérer les filtres fréquents.


## Diagramme ER

Génération (nécessite graphviz):
```bash
python scripts/generate_er_diagram.py
```
Image: `docs/er_diagram.png`

## Frontend (à initier)

Prochain ajout: Next.js + TypeScript avec pages d'authentification consommant l'API.

## Tests
```bash
pytest -q
```

### Helpers de tests

Des utilitaires centralisés se trouvent dans `tests/utils.py` :

- `auth_headers(email, role=None)` génère un header Authorization pour un utilisateur (admin par défaut, `role="user"` pour user standard).
- `admin_headers(email="admin@example.com")` raccourci pour un admin.
- `bearer(headers)` extrait le token pur.
- `ensure_admin / ensure_user` (internes) créent l'utilisateur s'il n'existe pas.
- Fixtures Pytest:
	- `admin_headers_factory` (session) et `admin_headers` (scope fonction) pour réutiliser un header admin sans relogin.

Objectif: réduire la duplication de création/login dans les tests (refactor appliqué aux suites templates, documents, reports, storage, audit).

### Metrics de jobs rapports

Les tâches de rapports exposent des métriques Prometheus additionnelles:

- `report_jobs_total{job_type, status}`: compteur (status = `success` | `error`).
- `report_jobs_active{job_type}`: gauge du nombre de jobs en cours (retombe à 0 après exécution).

Couvert par des tests:
- Succès (génération inline): vérifie compteur `success` et gauge=0.
- Erreur (monkeypatch de l'horodatage pour provoquer une exception): vérifie apparition du label `status="error"`.

### File d'attente & fallback

Les jobs sont enqueued via RQ si Redis est disponible, sinon exécutés inline. Les tests simulent:
- Job queued (monkeypatch de la queue).
- Job terminé (fetch simulé renvoyant `finished`).
- Statut `unknown` pour un ID inexistant.

#### Inline fallback détaillé

Le décorateur `@task` (voir `backend/app/core/queue.py`) choisit dynamiquement:
- Si Redis + RQ importables: `queue.enqueue(fn, *args)`.
- Sinon (import impossible, connexion Redis KO, exception d'enqueue): exécution immédiate (inline) de la fonction cible.

Conséquences:
- Les tests et environnements de dev fonctionnent sans Redis.
- Les métriques de jobs rapport reflètent immédiatement l'état (gauge retombe à 0) pour l'exécution inline.
- L'endpoint `POST /api/v1/reports/dummy` renvoie alors `job_id="inline"`.

Pour activer la vraie file: lancer un Redis local (ex: `docker run -p 6379:6379 redis:7`) et vérifier `settings.redis_url`.

#### Typage RQ & stubs

Pour ne pas imposer la dépendance RQ aux outils de typage quand Redis est absent, le code utilise `TYPE_CHECKING` + imports conditionnels. Une classe stub minimale est fournie comme fallback pour permettre les monkeypatch dans les tests.

Si vous souhaitez renforcer le typage, vous pouvez ajouter un fichier stub `.pyi` séparé exposant seulement les signatures `enqueue(...)` et `Job.fetch(...)` nécessaires.

### Exécution partielle

Pour lancer uniquement les tests rapports:
```bash
pytest -q tests/test_reports_*.py
```
Pour exécuter une seule fonction de test:
```bash
pytest -q tests/test_reports_metrics_errors.py::test_metrics_error_counter
```

### Dashboard Grafana exemple

Un exemple minimal de dashboard se trouve dans `docs/grafana_dashboard_example.json` avec:
- Throughput & taux d'erreurs HTTP (PromQL rate() & increase())
- Compteurs succès/erreur des jobs rapports
- Gauge jobs actifs

Import: Grafana -> Dashboards -> Import -> coller JSON.

### Makefile

Des cibles pratiques:
```bash
make test           # tous les tests
make test-reports   # seulement rapports
make test-fast      # sélection rapide (k=reports)
```

## Documentation complémentaire

| Document | Description |
|----------|-------------|
| `DEV_GUIDE.md` | Architecture interne détaillée (auth, sécurité, flux documents). |
| `docs/WORKFLOW.md` | Workflow projet unifié (phases, RACI, backlog, DoD). |
| `docs/MAINTENANCE.md` | Guide maintenance & exploitation (DB, migrations, observabilité, CI). |
| `scripts/generate_er_diagram.py` | Génération diagramme entité-relation. |

## État fonctionnel actuel

Fonctionnalités implémentées :
- Auth JWT + refresh tokens hashés avec rotation
- CRUD: Users (register/login), Companies, Clients, Policies, Templates (versions)
- Génération documents HTML/PDF/XLSX (compression + chiffrement facultatifs)
- Téléchargement sécurisé + URLs signées HMAC (rotation de clés)
- Rate limiting téléchargements (Redis + fallback mémoire)
- Audit log (génération, téléchargement, purge orphelins)
- Purge fichiers orphelins

Backlog prioritaire (extrait) dans `docs/WORKFLOW.md` (audit listing, queue async, S3, CI lint+types…).

---
Ce squelette est prêt pour itérations rapides. Contributions via branches fonctionnelles.

