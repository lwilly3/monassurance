# MONASSURANCE – Backend

![CI](https://github.com/lwilly3/monassurance/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/lwilly3/monassurance/branch/main/graph/badge.svg)](https://codecov.io/gh/lwilly3/monassurance)

Backend FastAPI du SaaS **MONASSURANCE** (auth, templates versionnés, génération documents PDF/Excel, URLs signées, rate limiting, audit, chiffrement & compression optionnels).
# MONASSURANCE – Backend

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

