# Architecture MonAssurance

## Vue d'ensemble

MonAssurance est une plateforme SaaS de gestion d'assurance construite avec une architecture moderne et scalable.

### Stack technologique

#### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11+)
- **Base de données**: PostgreSQL (développement SQLite)
- **ORM**: SQLAlchemy 2.x avec Alembic pour les migrations
- **Authentification**: JWT avec refresh tokens rotatifs
- **Cache/Queue**: Redis (avec fallback en mémoire)
- **Tests**: Pytest avec coverage 86%+
- **Qualité**: Ruff, MyPy, Bandit

#### Frontend
- **Framework**: Next.js 14+ avec TypeScript
- **Styling**: Tailwind CSS
- **Tests E2E**: Playwright

### Architecture hexagonale

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Layer                        │
│  FastAPI Routes │ REST API │ GraphQL (future)             │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                        │
│    Services │ Business Logic │ Use Cases                   │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                           │
│  Models │ Entities │ Business Rules │ Policies            │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                       │
│  Database │ External APIs │ File Storage │ Queue           │
└─────────────────────────────────────────────────────────────┘
```

## Modules principaux

### 1. Authentification & Autorisation

- **JWT avec refresh tokens rotatifs** pour sécurité renforcée
- **Gestion des sessions d'appareils** (device management)
- **Rate limiting** par IP et par compte
- **Rôles**: USER, MANAGER, ADMIN, SUPERADMIN

### 2. Gestion documentaire

- **Templates versionnés** avec stockage sécurisé
- **Génération PDF/Excel** avec pipeline de rendu
- **URLs signées** avec expiration configurable
- **Stockage multi-backend**: Local, S3, Google Drive

### 3. Système de rapports

- **Queue système** avec RQ (Redis) et fallback inline
- **Jobs asynchrones** pour génération de rapports
- **Métriques Prometheus** intégrées
- **Statuts temps réel** des tâches

### 4. Audit & Observabilité

- **Audit logs** complets avec filtrage et export CSV
- **Métriques applicatives** (requêtes, erreurs, performance)
- **Logs structurés** avec correlation IDs
- **Health checks** multi-niveaux

## Structure des données

### Modèles principaux

```python
# Utilisateurs et authentification
User → RefreshToken (1:N)
User → Client (1:N)

# Business domain
Client → Policy (1:N)
Company → Policy (1:N)
Policy → GeneratedDocument (1:N)

# Templates et documents
Template → TemplateVersion (1:N)
TemplateVersion → GeneratedDocument (1:N)

# Configuration
StorageConfig (singleton)
IntegrationConfig (par type)

# Audit
AuditLog (événements système)
ReportJob (tâches async)
```

### Relations clés

1. **Isolation des données**: Les utilisateurs ne voient que leurs clients/polices
2. **Versioning**: Templates avec versioning complet et historique
3. **Traçabilité**: Tous les événements critiques sont audités
4. **Flexibilité**: Configuration externalisée pour stockage et intégrations

## Patterns de conception

### 1. Repository Pattern
```python
# Encapsulation de l'accès aux données
class ClientRepository:
    def find_by_owner(self, user_id: int) -> list[Client]
    def create(self, client: ClientCreate) -> Client
```

### 2. Service Layer
```python
# Logique métier encapsulée
class DocumentService:
    def generate_report(self, template_id: int, data: dict) -> Document
    def sign_download_url(self, doc_id: int) -> str
```

### 3. Dependency Injection
```python
# FastAPI dependencies pour injection
def get_current_user(token: str = Depends(oauth2_scheme)) -> User
def get_storage_provider() -> StorageProvider
```

### 4. Strategy Pattern
```python
# Stockage multi-backend
class StorageProvider:
    def get_backend(self) -> StorageBackend  # Local|S3|GDrive
```

## Sécurité

### Authentification
- Mots de passe hashés avec bcrypt (12 rounds minimum)
- JWT avec expiration courte (15 minutes)
- Refresh tokens rotatifs avec révocation

### Autorisation
- RBAC (Role-Based Access Control)
- Isolation des données par propriétaire
- Validation stricte des permissions

### Protection des données
- Chiffrement en transit (HTTPS forcé)
- URLs signées pour téléchargements
- Validation stricte des entrées
- Sanitisation des chemins de fichiers

### Rate Limiting
- Protection brute-force sur login
- Limitation des téléchargements par utilisateur
- Throttling général configurable

## Performance

### Optimisations base de données
- Index optimisés sur les requêtes fréquentes
- Pagination systématique pour les listes
- Lazy loading pour les relations

### Cache et queue
- Redis pour cache et queue système
- Fallback en mémoire pour développement
- Métriques de performance temps réel

### Monitoring
- Health checks multi-niveaux (/health, /health/db)
- Métriques Prometheus exportées
- Logs structurés avec corrélation

## Évolutivité

### Architecture modulaire
- Séparation claire des responsabilités
- Interfaces bien définies entre modules
- Configuration externalisée

### Extensibilité
- Système de plugins pour stockage
- Intégrations configurables
- API versionnée pour compatibilité

### Scalabilité
- Queue asynchrone pour tâches lourdes
- Stockage distribué (S3, GDrive)
- Stateless pour scaling horizontal

## Tests et qualité

### Stratégie de test
- **Tests unitaires**: 40+ tests, 86%+ coverage
- **Tests d'intégration**: Base de données, APIs externes
- **Tests E2E**: Playwright pour workflows critiques

### Qualité du code
- **Linting**: Ruff avec règles strictes
- **Type checking**: MyPy avec validation complète
- **Sécurité**: Bandit pour analyse statique
- **CI/CD**: Pipeline complet avec quality gates

## Déploiement

### Environnements
- **Development**: SQLite, services mock
- **Staging**: PostgreSQL, Redis, S3
- **Production**: PostgreSQL HA, Redis Cluster, CDN

### Infrastructure
- Docker containers
- Kubernetes pour orchestration
- Helm charts pour déploiement
- Monitoring avec Prometheus/Grafana
