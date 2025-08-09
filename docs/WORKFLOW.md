# Workflow Complet MONASSURANCE

Ce document consolide et operationalise les prompts de cadrage (UI, a11y, animations, frontend, backend, DB & templates) en un flux unique exécutable par l'équipe et les agents IA.

## Vue d'ensemble Phasée

Phase | Objectif principal | Durée indicative | Critère de sortie
-----|--------------------|------------------|------------------
0. Préparation | Repo, tooling, CI basique | 0.5 sem | Repo initial + pipeline lint/test
1. Design UI & Accessibilité | Maquettes + design system + specs a11y | 1.5 sem | Figma validé + rapport a11y initial
2. Animations & Micro-interactions | Catalogue transitions & règles a11y motion | 0.5 sem | Doc animations + prototypes validés
3. Bibliothèque Composants | Base Button/Input/Form/Table/Layout | 2 sem | 80% composants core + tests + docs
4. Backend Core | Auth, Users, Companies, Clients, Policies | 1 sem | Endpoints CRUD + tests verts
5. Templates & Génération Docs | CRUD templates + rendu PDF/XLSX | 1 sem | Génération multi-format fiable
6. Sécurité Avancée & Observabilité | URLs signées, audit, rate limit, logging | 0.5 sem | Tests sécurité passent + logs exploitables
7. Rapports & Déclarations | Batch génération + historique | 1 sem | MVP batch + stockage rapports
8. Intégrations Compagnies | Connecteurs API / export | 1-2 sem | 1 connecteur réel en prod
9. D durabilité & Scalabilité | S3/MinIO, queue, metrics | continu | SLOs atteints

Les phases peuvent se chevaucher (ex: composants parallèles au backend core).

## Rôles & Responsabilités (RACI simplifié)

Domaine | Responsable (R) | Appui (A) | Consulté (C) | Informé (I)
--------|-----------------|----------|--------------|------------
UI Design | UX Lead | Front Dev | PO | Équipe entière
Accessibilité | A11y Expert | Front Dev | UX Lead | PO
Backend Auth & Sécurité | Backend Lead | SecOps | PO | Front Dev
Templates & Docs | Backend Lead | Front Dev | PO | Support
Composants UI | Front Dev Lead | UX Lead | A11y Expert | PO
Intégrations API | Backend Lead | DevOps | PO | Support
Infra & CI/CD | DevOps | Backend Lead | SecOps | Équipe
Reporting & Analytics | Data/Backend | Front Dev | PO | Équipe

## Environnements

Type | But | Nom | Outils
-----|-----|-----|------
Local | Dev isolé | dev-* | venv, SQLite, docker compose
Intégration | Tests partagés | ci | PostgreSQL, Redis, headless
Pré-production | Validation quasi-prod | staging | Postgres managé, MinIO
Production | Utilisateurs finaux | prod | Postgres HA, S3, Redis cluster

## Gestion Base de Données

- Modélisation initiale -> ERD via `scripts/generate_er_diagram.py`.
- Convention: une entité = un fichier sous `backend/app/db/models/`.
- Migration: `alembic revision --autogenerate -m "desc"` puis revue manuelle.
- Politique: pas de suppression de colonne en prod sans phase de dépréciation (ajout colonne_nouvelle -> migration données -> suppression ancienne plus tard).

## Stratégie Templates

Type | Stockage | Format | Notes
-----|----------|--------|------
HTML | DB (TemplateVersion.content) | Jinja2 | Variables nommées snake_case
Excel | Fichier binaire en DB ou FS (selon escalade) | XLSX | openpyxl, injection par nom
Email (futur) | DB | MJML/HTML | Compilation build step

## Sécurité (Checklists incrémentales)

Catégorie | Sprint 4 | Sprint 6 | Futur
---------|----------|----------|------
Auth | JWT + refresh | Rotation clés signatures | JTI + revoke list cluster
Stockage docs | Hash nom + option chiffrement | Clés rotatives | KMS par compagnie
Réseau | HTTPS (staging/prod) | CSP headers | mTLS intégrations
Audit | Génération / téléchargement | Purge orphelins | Export SIEM + alertes
Rate limiting | Téléchargements | Auth brute force | Global token bucket

## Qualité & CI

Pipeline (ordre):
1. Install deps
2. Lint (ruff/flake8) + mypy
3. Tests (pytest -q) + coverage (fail <85%)
4. Build image (prod tags)
5. Scan (trivy / bandit)
6. Deploy (staging) -> tests smoke -> prod canary

## Observabilité

- Logs structurés JSON (à introduire) => ship vers Loki/ELK.
- Metrics Prometheus: requêtes, latence p95, erreurs 4xx/5xx, documents générés/min.
- Tracing (OpenTelemetry) sur endpoints critiques: génération document, refresh token.

## Frontend <-> Backend (Contrat Types)

- Génération client TS via OpenAPI JSON (`/openapi.json`).
- Version API: préfixe `/api/v1`. Breaking change => `v2` parallèle.
- Politique de compatibilité: maintenir endpoints vN-1 min 2 cycles.

## Backlog Priorisé (extraits)

ID | Item | Priorité | Effort | Notes
---|------|----------|--------|------
B1 | Endpoint audit log list + filtres | Haute | M | Conformité
B2 | Queue asynchrone génération lourde | Haute | L | Celery/Redis
B3 | Passage stockage documents vers S3 | Haute | M | Préparer multi instance
B4 | Lint + mypy + coverage CI | Haute | S | Santé code
B5 | URL signée usage unique | Moyenne | S | Renforcer sécurité
B6 | JTI + revoke list JWT | Moyenne | M | Sécurité sessions
B7 | Observabilité (metrics + traces) | Moyenne | M | Scalabilité
B8 | Intégration API Compagnie X | Moyenne | L | Client pilote
B9 | Table job + retry | Moyenne | M | Robustesse
B10 | Export audit CSV | Basse | S | Outil conformité

## Plan de Release (exemple semestriel)

Release | Contenu clé | Date cible | Gate qualité
--------|-------------|-----------|-------------
R1 | Auth + CRUD + Templates + Docs gen | M1 fin | Tests verts + coverage 80%
R2 | Sécurité avancée + Reporting | M2 fin | Pas de vuln High
R3 | Intégrations + Observabilité | M3 fin | Uptime 99% staging
R4 | Scalabilité stockage + Queue | M4 fin | Tests charge OK
R5 | A11y complète + Animations | M5 fin | Audit AA >95%
R6 | Hardening + export conformité | M6 fin | Audit sécu externe

## Gestion des Tickets

Format titre: `[B/E/F][Type] Courte description` (ex: `[B][SEC] Rotation clé signatures`).
Description: Contexte, Done criteria, Tests impactés, Risques.
Labels: `backend`, `frontend`, `security`, `a11y`, `infra`, `tech-debt`.

## Definition of Done (extraits)

- Code + tests + docstrings.
- Pas d'erreur linter / types.
- Coverage global >= seuil.
- Changelog ou notes de version mises à jour.
- Secrets hors code (env / vault).

## Risques & Mitigations

Risque | Impact | Mitigation
-------|--------|-----------
Multi-instance sans stockage partagé | Documents incohérents | Passage S3 + sticky sessions temporaire
Fuite refresh token | Session prolongée | Hash + rotation + révocation
Explosion taille binaire DB | Performance | Externaliser (FS/S3) + TTL purge
Non-conformité a11y tardive | Retard release | Audit précoce + contrôle continu
Dette tests | Régressions silencieuses | Budget test / sprint + couverture

## Scripts & Automatisation Futurs

Script | But
-------|----
`manage.py rotate-keys` | Générer / activer nouvelle clé signature
`manage.py purge-old-logs` | Nettoyage audit > N jours
`manage.py export-audit --format=csv` | Export conformité
`manage.py enqueue-report --company=X` | Génération async

## Annexes

- Voir `DEV_GUIDE.md` pour détails d'implémentation interne backend.
- Voir design system Figma (lien à insérer).
- Voir rapport a11y initial (lien à insérer).

---
Document évolutif : réviser à chaque fin de release.
