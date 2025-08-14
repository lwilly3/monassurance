# Migration vers Celery pour MonAssurance

## 🎯 Objectif

Remplacer le système de queue RQ actuel par Celery pour une gestion plus robuste des tâches asynchrones, notamment pour la génération de rapports lourds.

## 🏗️ Architecture Celery

### Composants principaux

1. **Celery App** (`backend/app/core/celery_app.py`)
   - Configuration centralisée
   - Routing des tâches par queue
   - Gestion des retries et timeouts
   - Beat scheduler pour tâches périodiques

2. **Workers spécialisés**
   - **reports**: Génération de rapports lourds (2 workers)
   - **documents**: Traitement de documents (1 worker)  
   - **notifications**: Envoi de notifications (1 worker)
   - **celery**: Tâches système générales (1 worker)

3. **Monitoring**
   - **Flower**: Interface web sur port 5555
   - **Métriques Prometheus**: Intégrées dans les tâches
   - **Health checks**: Surveillance automatique

## 🔄 Migration RQ → Celery

### Changements principaux

1. **Nouveau système de tâches**
   ```python
   # Ancien (RQ)
   @task
   def generate_dummy_report(report_id: str):
       return {"report_id": report_id}
   
   # Nouveau (Celery)
   @celery_app.task(bind=True, queue="reports", max_retries=3)
   def generate_dummy_report(self, report_id: str, job_id: int = None):
       # Gestion avancée des erreurs et retry
       # Métriques Prometheus
       # Mise à jour statut en base
   ```

2. **API routes hybrides**
   - Détection automatique Celery/RQ
   - Fallback gracieux vers RQ si Celery indisponible
   - Nouvelles routes pour rapports lourds

3. **Types de rapports supportés**
   - **dummy**: Rapport factice (existant)
   - **heavy**: Nouveaux rapports lourds (PDF, Excel, Analysis)

## 🚀 Déploiement

### Docker Compose

```bash
# Démarrage avec Celery
docker-compose -f docker-compose.celery.yml up -d

# Services démarrés:
# - backend (API FastAPI)
# - celery-worker-reports (2 workers pour rapports)
# - celery-worker-documents (1 worker pour documents)
# - celery-worker-general (1 worker général)
# - celery-beat (scheduler)
# - celery-flower (monitoring web)
# - db (PostgreSQL)
# - redis (broker)
```

### Commandes de gestion

```bash
# Via le script manager
python celery_manager.py worker reports 4    # 4 workers pour rapports
python celery_manager.py beat                # Scheduler
python celery_manager.py flower 5555         # Interface web
python celery_manager.py status              # Statut workers

# Via manage.py
python manage.py celery-worker reports 2
python manage.py celery-beat
python manage.py celery-flower
python manage.py celery-status
```

## 📊 Nouvelles fonctionnalités

### 1. Rapports lourds

```bash
# API pour rapports lourds
POST /api/v1/reports/heavy?report_type=pdf&pages=50&processing_time=30

# Types supportés:
# - pdf: Rapport PDF avec pagination
# - excel: Rapport Excel multi-feuilles  
# - analysis: Rapport d'analyse avec graphiques
```

### 2. Gestion avancée des jobs

```bash
# Annulation de jobs
DELETE /api/v1/reports/jobs/{job_id}

# Listage avec filtres
GET /api/v1/reports/jobs?status=completed&limit=20

# Statut des queues
GET /api/v1/reports/queues/status
```

### 3. Monitoring Flower

Interface web disponible sur `http://localhost:5555`:
- Vue en temps réel des workers
- Statut des tâches en cours
- Historique et statistiques
- Graphiques de performance

## 🔧 Configuration

### Variables d'environnement

```bash
# Redis (broker et backend)
REDIS_URL=redis://localhost:6379/0

# Base de données pour persistance jobs
DATABASE_URL=postgresql://user:pass@localhost/monassurance

# Environnement (affecte config Celery)
ENVIRONMENT=development|test|production
```

### Queues et priorités

| Queue | Priorité | Concurrency | Usage |
|-------|----------|-------------|--------|
| reports | 5 | 2 | Rapports lourds |
| documents | 7 | 1 | Traitement docs |
| notifications | 3 | 1 | Notifications |
| celery | 6 | 1 | Tâches système |

## 📈 Métriques et monitoring

### Métriques Prometheus

```python
# Nouvelles métriques Celery
report_jobs_total{job_type, status, queue}          # Compteur total
report_jobs_duration_seconds{job_type, queue}       # Histogramme durées
report_jobs_active{job_type, queue}                 # Gauge jobs actifs
report_jobs_retries_total{job_type, queue}          # Compteur retries
```

### Tâches périodiques (Beat)

- **Nettoyage jobs**: Supprime jobs > 7 jours (chaque heure)
- **Health check**: Vérification système (toutes les 5 min)
- **Métriques quotidiennes**: Rapport journalier (à minuit)

## 🧪 Tests

### Nouveaux tests Celery

```python
# Test avec Celery activé
def test_celery_heavy_report():
    with patch('CELERY_AVAILABLE', True):
        resp = client.post("/api/v1/reports/heavy?report_type=pdf")
        assert resp.status_code == 200

# Test fallback RQ
def test_celery_unavailable_fallback():
    with patch('CELERY_AVAILABLE', False):
        resp = client.post("/api/v1/reports/dummy")
        # Devrait utiliser RQ
```

## 🔄 Compatibilité

### Rétrocompatibilité

- **API existante**: Toutes les routes `/reports/dummy` fonctionnent
- **Tests existants**: Passent sans modification
- **Fallback RQ**: Activé si Celery indisponible
- **Jobs inline**: Supportés pour les tests

### Migration progressive

1. **Phase 1**: Déploiement parallèle (RQ + Celery)
2. **Phase 2**: Migration trafic vers Celery
3. **Phase 3**: Suppression code RQ (future)

## ⚠️ Considérations

### Dépendances

- **Celery 5.4.0**: Ajouté aux requirements
- **Flower**: Optionnel pour monitoring
- **Redis**: Broker partagé RQ/Celery

### Performance

- **Overhead**: Léger overhead Celery vs RQ
- **Scalabilité**: Meilleure avec workers spécialisés
- **Monitoring**: Plus riche avec Flower + métriques

### Sécurité

- **Sérialisation JSON**: Plus sûre que pickle
- **Validation tâches**: Par queue et type
- **Isolation workers**: Par fonction métier

## 🎯 Prochaines étapes

1. **Tests de charge**: Valider performance sous charge
2. **Alertes**: Intégrer alertes Prometheus/Grafana  
3. **Callbacks**: Webhooks post-génération
4. **Stockage**: Intégration S3 pour gros fichiers
5. **Nettoyage**: Suppression code RQ legacy
