# Maintenance & Exploitation – MONASSURANCE

Ce document synthétise les améliorations mises en place pour fiabiliser, maintenir et comprendre le backend.

## 1) Base de données & migrations
- Passage SQLite → PostgreSQL documenté (README) et outillé (docker-compose, Alembic override via settings).
- Migrations Alembic ciblées (no-op sur SQLite, actives sur Postgres):
  - 20250808_0004: index composite audit_logs(action, object_type, created_at).
  - 20250809_0005: JSON → JSONB + index GIN sur colonnes JSONB (integration_configs.extra, generated_documents.doc_metadata, declaration_items.data, report_jobs.params, audit_logs.audit_metadata).
  - 20250809_0006: extensions pg_trgm & citext; index FK fréquents; index partiel generated_documents(created_at) WHERE status='ready'.
  - 20250809_0007: emails en CITEXT (users.email, clients.email) + nettoyage index redondant.
  - 20250809_0008: index trigram (GIN) sur clients.email et clients.phone.
  - 20250809_0009: index trigram (GIN) sur companies.name.
- Modèles: SQLAlchemy JSON conservé pour portabilité; migration force JSONB en PG.
- Indices: composites, partiels et GIN pour répondre aux filtres/LIKE fréquents.

### Politique de migrations (model-first)

Objectif: garantir que le schéma de la base soit toujours dérivé des modèles SQLAlchemy et appliqué via Alembic (cohérence code ⇄ DB).

Règles:
- Ne jamais corriger un schéma en modifiant un fichier de migration déjà existant.
- Toute modification (colonne, type, défaut, contrainte) se fait d’abord dans le modèle SQLAlchemy.
- Toujours utiliser `server_default=text("...")` pour les valeurs par défaut côté serveur (ex: `text("TRUE")`, `text("now()")`).
- Après modification de modèle:
  1) Générer une migration: `alembic revision --autogenerate -m "description"`
  2) Relire la migration (types, `server_default`, contraintes) et l’ajuster si besoin.
  3) Appliquer: `alembic upgrade head`.
- En cas d’erreur (dialecte PG/SQLite/MySQL), revenir au modèle, corriger, régénérer la migration.
- Ne jamais patcher directement la base sans migration correspondante.

Bénéfices:
- Cohérence totale entre modèles, migrations et base.
- Migrations reproductibles, compatibles multi-environnements.
- Réduction des incidents en production liés aux écarts de schéma.

Procédure Postgres (dev/staging):
- Copier .env.example → .env; définir DATABASE_URL Postgres.
- Démarrer la DB: `docker compose up -d db`.
- Appliquer le schéma: `alembic upgrade head`.
- Démarrer l’API: uvicorn ou `docker compose up -d backend` (exécute upgrade automatiquement).

## 2) Observabilité & santé
- Endpoints:
  - /health: disponibilité générale.
  - /health/db: ping SQL (retourne 503 si indisponible).
- Latence HTTP:
  - Middleware trace la durée et ajoute l’en-tête X-Response-Time.
  - Alerte WARNING si > http_warn_ms (def. 1000ms).
- Requêtes SQL lentes:
  - Log WARNING si > slow_query_ms (def. 500ms).
  - DEBUG_SQL: echo SQLAlchemy activable (dev uniquement).
- Paramètres (.env):
  - SLOW_QUERY_MS, DEBUG_SQL, HTTP_WARN_MS, ENABLE_METRICS, LOG_JSON, REQUEST_ID_HEADER.

## 3) Pooling & robustesse DB
- Engine SQLAlchemy Postgres avec: pool_pre_ping, pool_size, max_overflow, pool_recycle.
- Branche SQLite inchangée (connect_args check_same_thread pour tests/dev).

## 4) CI/CD
- Job SQLite: lint (ruff), types (mypy), tests + couverture, upload Codecov; build Docker (job séparé).
- Job Postgres: service postgres:16, alembic upgrade head, tests sur PostgreSQL, upload couverture (flag postgres), health check DB.
- Codecov: badges et OIDC configurés; étape non bloquante.

## 5) Bonnes pratiques & opérations
- Migrations:
  - Générer: `alembic revision --autogenerate -m "message"`.
  - Appliquer: `alembic upgrade head`.
  - Downgrade: `alembic downgrade -1` (prudence en prod).
- Indexation:
  - Ajouter GIN sur JSONB si requêtes par clés; trigram (pg_trgm) pour LIKE/ILIKE; partiels pour filtres stables.
- Backups:
  - Utiliser pg_dump/pg_restore; prévoir une stratégie de rétention côté infra.
- Secrets:
  - Gestion via secrets CI/CD et orchestrateur (ne jamais committer JWT_SECRET_KEY/credentials DB).

## 6) Dépannage rapide
- /health/db → 503: vérifier DATABASE_URL, réseau, droits Postgres.
- Alembic: vérifier que alembic/env.py lit settings.database_url; `alembic history` puis `alembic upgrade head`.
- Lenteurs: baisser SLOW_QUERY_MS et HTTP_WARN_MS en dev; vérifier index manquants; activer DEBUG_SQL si nécessaire.

## 7) Références utiles
## 8) Sécurité (CORS, en-têtes, rate limiting)

- CORS: configurable via `CORS_ORIGINS`, `CORS_ALLOW_METHODS`, `CORS_ALLOW_HEADERS`, `CORS_ALLOW_CREDENTIALS`.
- En-têtes sécurité: `X-Frame-Options`, `Referrer-Policy`, `X-Content-Type-Options: nosniff` ajoutés par défaut. `Content-Security-Policy` via `SECURITY_CSP`. `Strict-Transport-Security` via `SECURITY_HSTS` (activer uniquement en HTTPS).
- Rate limiting global (désactivé par défaut): par IP + chemin. Activation par `RATE_LIMIT_ENABLED=true`. Seuils: `DEFAULT_RATE_LIMIT_PER_MINUTE`, `AUTH_RATE_LIMIT_PER_MINUTE`. Backing Redis auto si dispo, sinon fallback mémoire.
- Throttling login: limites par IP et par compte par minute pour `POST /auth/login`. Redis préféré, fallback mémoire si indisponible.

## 9) Sessions d'appareils (refresh tokens)

- Schéma: `refresh_tokens` avec `device_label`, `ip_address`, `user_agent`.
- Endpoints:
  - `GET /api/v1/auth/devices`: liste les sessions actives de l'utilisateur courant.
  - `DELETE /api/v1/auth/devices/{id}`: révoque une session spécifique si propriété vérifiée.
- Rotation: `POST /api/v1/auth/refresh` révoque le token consommé et en émet un nouveau.
- Migrations: une migration Alembic ajoute les colonnes device aux anciennes bases (aucun backfill runtime n'est conservé; exécuter `alembic upgrade head`).

### À curer (dettes techniques)

- Supprimer le backfill SQLite au démarrage une fois toutes les DB locales régénérées/migrées (ne garder que les migrations Alembic).
- Consolider la définition du modèle `RefreshToken` en un seul module (aujourd'hui présent dans `backend/app/db/models.py` et `backend/app/db/models/refresh_token.py`) et harmoniser les imports.
- Démarrage dev: `uvicorn backend.app.main:app --reload` (après `alembic upgrade head`).
- Docker Compose: `docker compose up -d` (DB + backend).
- Tests: `pytest -q`.
- Lint: `ruff check .`; Types: `mypy --config-file mypy.ini .`.

## 10) Administration – Configuration stockage (Frontend + Backend)

Objectif: Permettre à un administrateur de définir dynamiquement le backend de stockage des documents (local ou Google Drive) via l'UI.

Backend:
- Endpoint lecture: `GET /api/v1/admin/storage-config` (retourne backend courant + éventuels paramètres GDrive).
- Endpoint mise à jour: `PUT /api/v1/admin/storage-config` (valide et persiste la configuration).
- Types exposés dans l'OpenAPI: `StorageConfigRead`, `StorageConfigUpdate`.
- Validation serveur: si `backend=google_drive`, nécessite `gdrive_folder_id` et `gdrive_service_account_json_path` non vides.

Frontend:
- Page: `frontend/src/app/admin/storage-config/page.tsx` (client component).
- Logique métier isolée dans le hook `frontend/src/hooks/useStorageConfig.ts` (chargement initial, validation basique, PUT, état succès/erreur, auto-reset succès après 4s).
- Sauvegarde optimiste: le hook marque `success=true` immédiatement, puis rollback (restaure les valeurs précédentes + affiche erreur) si la requête PUT échoue.
- Accessibilité: libellés associés, feedback rôle `alert` / `status`, overlay de chargement avec `aria-busy`.
- I18n minimal embarqué (fr/en) – à externaliser ultérieurement.
- Toast (Radix) pour feedback de sauvegarde.
- Champs masqués: GDrive uniquement si backend sélectionné = google_drive.

Tests E2E (Playwright):
- Fichier: `frontend/tests-e2e/storage-config.spec.ts`.
- Mock réseau sur `**/api/v1/admin/storage-config` pour isoler l'UI du backend pendant les tests UI.
- Scénarios:
  1. Affichage de la page (GET mock) + présence des éléments principaux.
  2. Mise à jour (sélection Google Drive, saisie des champs, PUT mock) + assertion sur payload.
- Sélecteurs robustes: attributs `data-testid` (`storage-config-*`).
- Instrumentation (logs console/réponses) encore présente pour diagnostic – peut être allégée quand la stabilité est confirmée.

Bypass Auth pour tests:
- Middleware `frontend/src/middleware.ts` court-circuite la redirection login si la variable `NEXT_PUBLIC_DISABLE_AUTH=1` est définie (utilisée dans la config Playwright `webServer.env`).
- Permet d'éviter d'orchestrer un vrai flux d'auth dans les tests de pages admin isolées.

Améliorations futures suggérées:
- Optimistic update avec rollback visuel si échec.
- Test e2e scénario d'erreur serveur (PUT 500).
- Externalisation dictionnaire i18n + sélection langue dynamique.
- Suppression instrumentation verbose une fois CI fiable.

### Extension S3 & File d'attente (Étape 8)

Backend de stockage étendu pour supporter `s3` (champs ajoutés dans `storage_config`: `s3_bucket` obligatoire, `s3_region`, `s3_endpoint_url` optionnels). Migration: révision `20250812_0003`.

Frontend: page admin mise à jour (sélecteur S3 + champs dynamiques). Hook `useStorageConfig` enrichi pour envoyer/recevoir les champs S3.

File de tâches: introduction d'une couche minimale RQ (`backend/app/core/queue.py`) avec décorateur `@task` (méthode `.delay()`). Fallback inline si Redis absent ou indisponible.

Endpoint de démonstration reporting: `POST /api/v1/reports/dummy?report_id=...` renvoie un job_id (ou `inline`). Tâche exemple: `generate_dummy_report`.

Prochaines étapes recommandées:
1. Ajouter un worker dédié (ex: script entrée `python -m rq worker default`).
2. Persister l'état des jobs dans la table `report_jobs` (déjà dans le schéma initial), relier l'ID RQ.
3. Endpoint de suivi: `GET /api/v1/reports/{job_id}`.
4. Retenter (retries) + backoff: config RQ ou wrapper custom.
5. Observabilité: métriques Prometheus (compteur jobs, durées) + logs structurés.
6. Sécurité: quotas d'enqueue par utilisateur/admin sur une fenêtre de temps.

Notes opérationnelles:
- Exécuter `alembic upgrade head` après pull pour disposer des colonnes S3.
- Sans Redis: les tâches s'exécutent inline (utile pour tests unitaires rapides).

