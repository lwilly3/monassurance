# MONASSURANCE – Backend

![CI](https://github.com/lwilly3/monassurance/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/lwilly3/monassurance/branch/main/graph/badge.svg)](https://codecov.io/gh/lwilly3/monassurance)

Backend FastAPI du SaaS **MONASSURANCE** (auth, templates versionnés, génération documents PDF/Excel, URLs signées, rate limiting, audit, chiffrement & compression optionnels).

## Stack

- Python 3.11+
- FastAPI / Uvicorn
- SQLAlchemy 2.x
- Alembic (migrations)
- PostgreSQL (dev possible en SQLite)
- JWT (auth) via `python-jose`
- Hash mots de passe via `passlib[bcrypt]`

## Structure

```
backend/
	app/
		api/
			routes/        # Endpoints versionnés
			deps.py        # Dépendances (DB, auth, etc.)
		core/            # Config & sécurité
		db/              # Session, base, modèles
		schemas/         # Schémas Pydantic
		main.py          # Point d'entrée FastAPI
alembic/
	versions/          # Scripts de migration
alembic.ini
.env.example
```

## Démarrage rapide (développement local)

1. Créer l'environnement virtuel
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
2. Copier le fichier d'exemple d'environnement
```bash
cp .env.example .env
```
3. (Optionnel) Lancer une base PostgreSQL locale (ex: Docker)
```bash
docker run -d --name monassurance-db -e POSTGRES_PASSWORD=devpass -e POSTGRES_USER=monassurance -e POSTGRES_DB=monassurance -p 5432:5432 postgres:16
```
4. Ajuster `DATABASE_URL` dans `.env` si besoin.
5. Créer les tables (dev SQLite ou après config Postgres)
```bash
alembic upgrade head
```
6. Lancer l'API
```bash
uvicorn backend.app.main:app --reload
```

Accès docs: http://127.0.0.1:8000/docs

Health:
- /health: statut général
- /health/db: ping base de données

## Sécurité & robustesse

- Rotation complète des refresh tokens: utilisation du refresh révoque l'ancien et émet un nouveau.
- Endpoints:
	- `POST /api/v1/auth/logout` et `POST /api/v1/auth/revoke` — révoquent un refresh token passé.
	- `POST /api/v1/auth/revoke-all` — révoque tous les refresh tokens de l'utilisateur courant.
- Rate limiting générique (désactivé par défaut): activable via `RATE_LIMIT_ENABLED=true`. Limites/minute configurables (`DEFAULT_RATE_LIMIT_PER_MINUTE`, `AUTH_RATE_LIMIT_PER_MINUTE`). Redis utilisé si dispo, sinon fallback mémoire.
- Limitation spécifique téléchargement de documents déjà en place (par utilisateur/lien signé).
- CORS configurable via variables d'environnement (`CORS_ORIGINS`, `CORS_ALLOW_*`).
- En-têtes de sécurité par défaut: `X-Frame-Options`, `Referrer-Policy`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy` (si `SECURITY_CSP` défini), `Strict-Transport-Security` (si `SECURITY_HSTS=true`).

### Sessions d'appareils (refresh tokens)

Les refresh tokens sont stockés hashés en base, avec rotation à chaque usage. Nous exposons des endpoints pour que l'utilisateur gère ses sessions ("mes appareils"):

- `GET /api/v1/auth/devices` — liste les sessions actives (non révoquées et non expirées) avec métadonnées:
	- `device_label`, `ip_address`, `user_agent`, `issued_at`, `expires_at`.
- `DELETE /api/v1/auth/devices/{id}` — révoque la session identifiée si elle appartient à l'utilisateur courant.

Pendant `POST /api/v1/auth/login` et `POST /api/v1/auth/refresh`, des métadonnées d'appareil sont enregistrées (label, IP, user-agent) pour alimenter cette liste.

Protection brute-force: le login est limité par IP et par compte (Redis si disponible, sinon fallback mémoire) avec erreurs 429 au-delà du seuil minute.

#### Try it — Mes appareils (local)

Prérequis: API locale sur http://127.0.0.1:8000 et `jq` installé.

1) Enregistrer un utilisateur de test

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
	-H "Content-Type: application/json" \
	-d '{"email":"deviceuser@example.com","password":"pass"}' | jq
```

2) Se connecter et récupérer les tokens

```bash
RESP=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
	-H "Content-Type: application/json" \
	-d '{"email":"deviceuser@example.com","password":"pass"}')
ACCESS=$(echo "$RESP" | jq -r .access_token)
REFRESH=$(echo "$RESP" | jq -r .refresh_token)
echo "ACCESS=$ACCESS"
echo "REFRESH=$REFRESH"
```

3) Lister les appareils (sessions actives)

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/devices \
	-H "Authorization: Bearer $ACCESS" | jq
```

4) Révoquer le premier appareil de la liste

```bash
DEVICE_ID=$(curl -s http://127.0.0.1:8000/api/v1/auth/devices \
	-H "Authorization: Bearer $ACCESS" | jq -r '.[0].id')
curl -i -X DELETE http://127.0.0.1:8000/api/v1/auth/devices/$DEVICE_ID \
	-H "Authorization: Bearer $ACCESS"
```

5) Vérifier qu'il a disparu

```bash
curl -s http://127.0.0.1:8000/api/v1/auth/devices \
	-H "Authorization: Bearer $ACCESS" | jq
```

## Observabilité (logs & metrics)

- Logs
	- Format JSON optionnel: activer avec `LOG_JSON=true` (stdout). Les logs incluent `X-Request-ID` (corrélation) si fourni, sinon un identifiant est généré et renvoyé en en-tête réponse.
	- En-tête `X-Response-Time` ajouté sur chaque réponse.
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

