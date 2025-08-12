# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

## 2025-08-12

### Ajouté
- Frontend: page d’administration `/admin/storage-config` (sélection backend `local` ou `google_drive`, champs conditionnels Google Drive, toast de feedback, overlay de chargement, i18n minimal fr/en).
- Hook `useStorageConfig` centralisant chargement initial (GET), validation minimale et sauvegarde (PUT) de la configuration de stockage.
- Tests E2E (Playwright) `storage-config.spec.ts` avec mocks réseau (GET/PUT) vérifiant affichage et mise à jour (payload PUT asserté).
- Attributs `data-testid` pour robustesse des sélecteurs tests (`storage-config-*`).
- Bypass middleware d’auth pour tests via variable `NEXT_PUBLIC_DISABLE_AUTH=1` (documenté dans `ARCHITECTURE.md`).
- Documentation mise à jour: sections dédiées dans `docs/MAINTENANCE.md`, `frontend/ARCHITECTURE.md` et `frontend/README.md`.

### Modifié
- `frontend/src/middleware.ts`: ajout court-circuit authentification si `NEXT_PUBLIC_DISABLE_AUTH=1` (usage test uniquement).
- Légères améliorations d’accessibilité sur la page (rôles `alert` / `status`, aria-busy overlay).

### Notes
- Instrumentation console/response dans le test E2E conservée pour stabilisation initiale; pourra être épurée ultérieurement.
- Prochaines optimisations identifiées: optimistic update avec rollback, test d’erreur serveur PUT, externalisation i18n.

## 2025-08-09

### Ajouté
- Endpoints "mes appareils": `GET /api/v1/auth/devices` (liste des sessions actives) et `DELETE /api/v1/auth/devices/{id}` (révocation par id). Stockage des métadonnées d'appareil (`device_label`, `ip_address`, `user_agent`).
- Throttling des tentatives de login par IP et par compte (Redis si présent, sinon fallback mémoire) avec réponses 429 au-delà des seuils/minute.
- Support PostgreSQL prêt pour dev/staging: variables d’environnement, service docker-compose, Alembic `env.py` piloté par `DATABASE_URL`.
- Migrations Alembic spécifiques PostgreSQL (no-op sous SQLite):
  - 20250809_0005: conversion JSON → JSONB + index GIN sur colonnes JSONB.
  - 20250809_0006: extensions `pg_trgm` et `citext`, index sur FKs fréquents, index partiel `generated_documents(status='ready')`.
  - 20250809_0007: `CITEXT` pour `users.email` et `clients.email` (unicité insensible à la casse) + nettoyage index redondant.
  - 20250809_0008: index GIN trigram sur `clients.email` et `clients.phone`.
  - 20250809_0009: index GIN trigram sur `companies.name`.
- Observabilité
  - Endpoint `/health/db` (503 si indisponible); `/health` conservé.
  - En-tête `X-Response-Time` injecté sur chaque réponse.
  - Seuils configurables: `SLOW_QUERY_MS` (requêtes SQL lentes), `HTTP_WARN_MS` (latence HTTP), `DEBUG_SQL` (echo SQLAlchemy en dev).
  - Endpoint `/metrics` (Prometheus) activable via `ENABLE_METRICS`; compteurs HTTP et erreurs exposés.
  - Logs JSON optionnels (`LOG_JSON=true`) et corrélation `X-Request-ID` (injecté si absent).
- Robustesse DB
  - Pooling SQLAlchemy (Postgres): `pool_pre_ping`, `pool_size`, `max_overflow`, `pool_recycle` paramétrables.
- CI/CD
  - Job GitHub Actions PostgreSQL: service `postgres:16`, `alembic upgrade head`, tests, health check DB, upload couverture (flag `postgres`).
- Documentation
  - `docs/MAINTENANCE.md` (maintenance/exploitation, DB, observabilité, CI).
  - `README.md` enrichi (procédure migration PG, health, CI PG) et `.env.example` (nouveaux paramètres).
  - Sécurité: ajout de l’en-tête `X-Content-Type-Options: nosniff` à la configuration par défaut.

### Modifié
- Middleware de log HTTP: journalise statut + durée; WARNING si durée > `http_warn_ms`.
- Logger requêtes SQL lentes: WARNING si durée > `slow_query_ms`.

### Qualité
- Lint (ruff) et tests (pytest) passent; migrations no-op sous SQLite, actives sous PostgreSQL.

---

Historique antérieur: voir les commits initiaux (structure FastAPI, auth, CRUD, génération de documents, audit, tests, CI de base).
