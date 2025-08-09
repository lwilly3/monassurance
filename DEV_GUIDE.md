# MONASSURANCE – Dev Guide

Ce guide décrit l’architecture interne, les flux critiques (auth, génération documentaire), les conventions et les étapes pour étendre la plateforme.

## 1. Architecture Globale

Couche | Contenu | Localisation
-------|---------|-------------
API (Routes) | Endpoints REST FastAPI versionnés | `backend/app/api/routes/*.py`
Dépendances | Auth, session DB, rôle | `backend/app/api/deps.py`
Core | Config, sécurité, logging, erreurs, Redis | `backend/app/core/*`
Services | Rendu documents multi-format | `backend/app/services/`
ORM | Modèles SQLAlchemy (un fichier / modèle) | `backend/app/db/models/`
Schémas | Pydantic (I/O API) | `backend/app/schemas/`
Persistence | Session / Engine | `backend/app/db/session.py`
Migrations | Alembic + versions | `alembic/`
Générés | Fichiers rendus (HTML/PDF/XLSX) | `generated/`
Tests | Pytest (intégration) | `tests/`

## 2. Flux d’Authentification & Tokens

1. `POST /auth/register` : création user + hash (bcrypt via Passlib).
2. `POST /auth/login` : vérification mot de passe -> génération:
   - Access token JWT (court terme) subject = email.
   - Refresh token *opaque* aléatoire : stocké **hashé (SHA-256)** dans table `refresh_tokens`.
3. `POST /auth/refresh` : consommation d’un refresh token:
   - Validation: hash présent, non révoqué, pas expiré.
   - Rotation: ancien marqu révoqué (champ `revoked_at`), nouveau token émis.
4. `POST /auth/logout` : révocation explicite du token fourni.

Raisons de conception:
- Refresh opaque évite réutilisation frauduleuse si DB compromise partiellement.
- Rotation systématique limite la fenêtre d’usage d’un token intercepté.

Fichier clé: `core/security.py`.

## 3. Contrôles d’Accès & Ownership

Niveaux de rôles: `admin` > `manager` > `agent` > (utilisation basique). 
- Gestion des templates: admin + manager.
- Génération documentaire: admin, manager, agent.
- Purge orpheline: admin uniquement.
- Ownership clients/policies: restriction par `client.owner_id` pour lecture & mutation.

Vérifications réparties dans les routes et `deps.require_role`.

## 4. Modélisation Principale

Entité | Rôle
-------|-----
`User` | Authentification + rôle + propriétaire de clients
`Client` | Assuré (lié à un user)
`Company` | Compagnie / partenaire
`Policy` | Police d’assurance (client + compagnie)
`Template` | Modèle logique (métadonnées)
`TemplateVersion` | Variante immuable (contenu / fichier / checksum)
`GeneratedDocument` | Document rendu (path + mime + meta compression/chiffrement)
`RefreshToken` | Jeton de rafraîchissement hashé + chaine parent
`AuditLog` | Trace sécurité / conformité (action, objet, metadata)

## 5. Génération de Documents

Endpoint: `POST /documents/generate`
Entrée: `DocumentGenerateRequest` (template_version_id, output_format, inline_context, etc.)
Étapes:
1. Sélection de version ou dernière version du template.
2. Choix format (html/pdf/xlsx) – validations.
3. Rendu via `services/document_renderer.render_template()`:
   - HTML: Jinja2 -> bytes UTF-8.
   - PDF: Jinja2 -> texte -> ReportLab (pagination naïve).
   - XLSX: Contexte clé/valeur -> feuille.
4. Compression optionnelle (`_compress` dans `inline_context`).
5. Chiffrement optionnel (`_encrypt`) via Fernet dérivé de la clé de signature active.
6. Calcul checksum SHA-256, stockage fichier dans `generated/` (nom déterministe `doc_<hashPrefix>.ext`).
7. Persistance `GeneratedDocument` (flags compression/chiffrement + kid).
8. Audit log `generate_document`.

## 6. Téléchargement Sécurisé & URLs Signées

Deux modes:
1. Accès authentifié classique (rôle suffisant + ownership sur policy le cas échéant).
2. Lien signé temporaire: `POST /documents/{id}/signed-url` -> URL `download?exp=...&sig=...`.

Signature:
- Format: `kid.signatureBase64`
- HMAC-SHA256 sur `"kid:doc_id:expires"` avec la clé correspondant à `kid` dans `Settings.signature_keys`.
- Vérification: expiration + comparaison constante.

Rotation de clés: changer `signature_active_kid`, ajouter nouvelle clé dans `signature_keys`, garder l’ancienne jusqu’à expiration des liens.

## 7. Rate Limiting Téléchargements

Fonction `_rate_limit` dans `documents.py`:
- Clé Redis `dl:<scope>:<minuteBucket>` via `INCR` + `EXPIRE 65s`.
- Fallback mémoire (_dict_) si Redis indisponible (tests/local offline).
- Limite par défaut: 3 téléchargements/minute (configurable dans code constant).

## 8. Compression & Chiffrement

- Compression: zlib (gain taille, sans entête spécifique) avant chiffrement.
- Chiffrement: Fernet (symétrique) avec clé dérivée: `sha256(secret)[:32]` puis base64 urlsafe -> stable pour un `kid` donné.
- Métadonnées:
  - `compressed: bool`
  - `encrypted: bool`
  - `enc_kid`: identifiant de clé active utilisée.

Client consommateur doit détecter via headers et métadonnées s’il doit décompresser/décrypter.

## 9. Audit Logging

Table `audit_logs` pour actions:
- `generate_document`
- `download_document` (flag signed vs direct)
- `purge_orphans`

Colonne `audit_metadata` (JSON) flexible pour flags format, compression, encryption, etc.

## 10. Purge de Fichiers Orphelins

Endpoint: `POST /documents/purge-orphans` (admin). Compare liste des fichiers présents vs paths en DB. Supprime ceux absents en base + audit.

## 11. Redis

Usage actuel: rate limiting. Wrapper: `core/redis.get_redis()` (singleton). Prévoir évolutions (circuit breaker, caching keys rotation, file locks).

## 12. Gestion des Migrations

- Dev SQLite : auto-création + petit rattrapage structurel dans `startup`.
- Prod/PostgreSQL : Alembic requis.
- Process:
```bash
aalembic revision --autogenerate -m "desc"
alembic upgrade head
```
Vérifier toujours diff généré avant commit (relations/cascades).

## 13. Tests

Type | Fichiers | Couvre
-----|----------|-------
CRUD Policies/Companies | `tests/test_companies_policies.py` | CRUD + auth
Templates | `tests/test_templates.py` | Versions, restrictions rôle
Documents | `tests/test_documents.py` | Génération, formats, URL signée, rate limit, purge, encryption/compression
Santé | `tests/test_health.py` | Endpoint `/health`

Exécution: `pytest -q` (reset SQLite simplifié via suppression fichier DB en pré-commande).

## 14. Ajout d’un Nouvel Endpoint (Checklist)

1. Définir schémas Pydantic (input/output) dans `schemas/`.
2. Créer route dans `api/routes/` ou module dédié.
3. Ajouter dépendances (auth/role) si nécessaire.
4. Mettre à jour tests (nouveau fichier ou extension d’un existant).
5. Documenter docstring module + fonction.
6. Ajouter migration si nouveau modèle.
7. Exécuter `pytest -q`.

## 15. Ajout d’un Nouveau Modèle

1. Créer fichier `db/models/<nom>.py` (hérite Base).
2. Migration Alembic autogenerate.
3. Mettre à jour imports globaux si nécessaire (souvent déjà wildcard dans `session.py`).
4. Créer schémas Pydantic pour sérialisation.
5. Tests CRUD & constraints.

## 16. Sécurité – Points de Vigilance

Aspect | Protection actuelle | Améliorations futures
-------|---------------------|----------------------
JWT | Secret fort + expiration | JTI + revoke list
Refresh Tokens | Opaques hashés + rotation | LRU pruning / IP bind
URL Signées | HMAC + TTL + rotation clé | Limite de scope (ex: IP), usage unique
Rate Limit | Redis minute window | Token bucket + cluster sync
Stockage Fichiers | Path confinement + noms hashés | Antivirus / ClamAV hook
Audit | Table centralisée | Export SIEM / alerting
Chiffrement | Sym métrique Fernet | Différencier clés par type de doc

## 17. Conventions de Code

- Un modèle = un fichier.
- Docstrings module + classe + fonctions exposées.
- Noms explicites anglais, messages d’erreurs localisés FR.
- Datetimes timezone-aware (UTC).
- Pas de logique métier dans les schémas Pydantic.

## 18. Stratégie de Rotation de Clés (Signatures / Chiffrement Docs)

1. Ajouter nouvelle entrée dans `Settings.signature_keys` (ex: `k2`).
2. Changer `signature_active_kid` -> `k2`.
3. Garder l’ancienne clé tant que des URLs signées `k1` peuvent être encore valides (TTL max).
4. Une fois expirées: retirer `k1` (purge).

## 19. Journalisation

`core/logging.py`: Log minimal HTTP (méthode + path) et capture exceptions non gérées.
Peut être étendu (corrélation request-id, niveau DEBUG conditionnel via settings).

## 20. Roadmap Technique (Propositions)

- File d’attente (Celery/RQ) pour génération lourde asynchrone.
- Webhook / callback post-génération (report_job / integration_config).
- Stockage objet (S3 / MinIO) + présignature native.
- Chiffrement différencié par Company (KMS).
- Observabilité: Prometheus metrics, tracing OpenTelemetry.
- Endpoint d’inspection des `AuditLog` avec filtres et pagination.

## 21. Dépannage Rapide

Symptôme | Piste
---------|------
Import SQLAlchemy échoue | Vérifier venv actif, `pip install -r requirements.txt`
Redis refusé | Démarrer `redis-server` ou ajuster `redis_url` -> fallback mémoire active quand même
PDF vide | Vérifier contenu template/version & contexte fourni
URL signée 401 | Expiration TTL dépassée ou clé retirée
Rate limit 429 | Attendre 60s ou réduire appels

## 22. Scripts Utiles

- ER Diagram: `python scripts/generate_er_diagram.py`

## 23. Qualité & CI (à implémenter)

- Lint: ruff/flake8 + mypy (proposé)
- SAST: bandit
- Tests parallèles: pytest-xdist
- Coverage gating (>=85%)

---
Ce guide doit vivre : mettre à jour à chaque ajout majeur (nouvel endpoint critique, modèle ou flux de sécurité).

## 24. Outils Qualité & Maintenance

Cet ensemble standardise la qualité du code et facilite l'automatisation CI/CD.

### Ruff (Lint & Format)
- Config: `ruff.toml` (sélection de règles E,F,I,B,UP,N,ASYNC,S,C4).
- Ignorés ciblés: `E203` (compatibilité black style slicing), `E501` (géré par format), `S311` (usage de secrets pseudo-aléatoires acceptable pour tests / génération clé interne), etc.
- Usage local: `python manage.py lint` (auto-fix puis mypy).

### Mypy (Typage Strict)
- Config: `mypy.ini` stricte (`disallow_untyped_defs`, `warn_return_any`).
- Exceptions: répertoire `tests` assoupli (`disallow_untyped_defs = False`).
- Objectif: prévenir régressions silencieuses (contrats stables sur services / sécurité).

### Pytest & Couverture
- Commandes: `python manage.py test` et `python manage.py testcov`.
- Intégration future: seuil coverage >=85% (gate CI).

### Script utilitaire `manage.py`
Commande | Rôle
---------|-----
`lint` | Ruff auto-fix + mypy
`test` | Tests rapides
`testcov` | Tests + couverture
`rotate-keys <kid>` | Génération nouvelle clé signature (affiche étapes .env)
`show-settings` | Debug configuration chargée

#### Exemple sortie `rotate-keys`
```
$ python manage.py rotate-keys k2
Nouvelle clé (kid=k2) -> Zm9vYmFyR0hKS0xNTk9QUVJTVFVWV1g=
Étapes:
1. Ajouter dans .env: SIGNATURE_KEYS__k2=Zm9vYmFyR0hKS0xNTk9QUVJTVFVWV1g=
2. Mettre à jour SIGNATURE_ACTIVE_KID=k2
3. Redéployer
```

### Recommandations CI (GitHub Actions futur)
1. Cache pip (clé = hash requirements.txt)
2. Étapes: lint -> mypy -> tests -> coverage -> build image -> scan sécurité
3. Artifacts: rapport couverture, logs ruff, rapport vulnérabilités.
4. Badges README: build, coverage, quality (optionnel Sonar / Codecov).

### Politique de Merge
- PR bloquée si: lint KO, mypy KO, couverture < seuil, tests échoués.
- Review obligatoire: 1 backend + 1 sécurité pour modifications touchant `core/security.py`.

### Évolutions futures
- Activation bandit (SAST) + blocage high severity.
- Ajout pre-commit hooks (local) pour ruff + mypy partiel.
- Génération docs OpenAPI versionnée et diff automatique (contrôle breaking changes).
