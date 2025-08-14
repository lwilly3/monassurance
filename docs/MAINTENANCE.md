# Guide de maintenance MonAssurance

## 🔧 Opérations courantes

### Déploiement

#### Mise à jour de production

```bash
# 1. Vérification pré-déploiement
make check-strict
make test

# 2. Backup base de données
pg_dump monassurance > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Déploiement
git tag v1.2.3
git push origin v1.2.3

# 4. Migrations (si nécessaire)
alembic upgrade head

# 5. Redémarrage services
docker-compose restart backend
```

#### Rollback

```bash
# 1. Identifier la version précédente
git tag --sort=-version:refname | head -5

# 2. Rollback base de données (si nécessaire)
alembic downgrade <revision>

# 3. Rollback application
git checkout v1.2.2
docker-compose restart backend
```

### Gestion base de données

#### Migrations

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "add_new_field_to_policy"

# Appliquer les migrations
alembic upgrade head

# Vérifier l'état des migrations
alembic current
alembic history

# Rollback d'une migration
alembic downgrade -1
```

#### Maintenance base de données

```sql
-- Statistiques des tables
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Taille des tables
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name::regclass) DESC;

-- Requêtes lentes
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## 📊 Monitoring

### Métriques clés

#### Métriques applicatives

- **Latence des requêtes**: P50, P95, P99
- **Taux d'erreur**: 4xx, 5xx par endpoint
- **Throughput**: Requêtes par seconde
- **Authentification**: Tentatives, succès, échecs

#### Métriques métier

- **Utilisateurs actifs**: Quotidien, hebdomadaire, mensuel
- **Documents générés**: Par jour, par template
- **Polices créées**: Par utilisateur, par période
- **Stockage utilisé**: Par utilisateur, total

#### Métriques infrastructure

- **Base de données**: Connexions, requêtes lentes, taille
- **Redis**: Mémoire utilisée, hit rate, connexions
- **Système**: CPU, mémoire, disque, réseau

### Health checks

#### Endpoints de santé

```python
# backend/app/api/routes/health.py

@router.get("/health")
async def health_check():
    """Vérification santé générale"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.2.3",
        "environment": settings.environment
    }

@router.get("/health/detailed")
async def detailed_health():
    """Vérification santé détaillée"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "storage": await check_storage(),
        "external_apis": await check_external_apis()
    }
    
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 🚨 Gestion des incidents

### Procédures d'urgence

#### API indisponible

1. **Vérification rapide**
   ```bash
   # Status des services
   docker-compose ps
   
   # Logs récents
   docker-compose logs --tail=100 backend
   
   # Santé base de données
   curl http://localhost:8000/health/db
   ```

2. **Actions correctives**
   ```bash
   # Redémarrage service
   docker-compose restart backend
   
   # Vérification ressources
   docker stats
   free -h
   df -h
   ```

#### Performance dégradée

1. **Identification**
   ```sql
   -- Requêtes actives
   SELECT pid, state, query_start, query
   FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '30 seconds';
   ```

2. **Actions immédiates**
   ```sql
   -- Terminer requête problématique
   SELECT pg_terminate_backend(pid);
   
   -- Analyse requêtes lentes
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC;
   ```

## 🔧 Maintenance préventive

### Tâches quotidiennes

```bash
#!/bin/bash
# scripts/daily_maintenance.sh

# Nettoyage logs anciens (> 30 jours)
find /var/log/monassurance -name "*.log" -mtime +30 -delete

# Statistiques base de données
psql -d monassurance -c "ANALYZE;"

# Sauvegarde quotidienne
pg_dump monassurance | gzip > "/backup/daily/db_$(date +%Y%m%d).sql.gz"
```

### Tâches hebdomadaires

```bash
#!/bin/bash
# scripts/weekly_maintenance.sh

# Vacuum base de données
psql -d monassurance -c "VACUUM ANALYZE;"

# Nettoyage documents orphelins
python scripts/cleanup_orphaned_documents.py

# Rapport de santé
python scripts/generate_health_report.py
```

## 📈 Optimisation performances

### Base de données

#### Index optimisés

```sql
-- Index pour requêtes fréquentes
CREATE INDEX CONCURRENTLY idx_policies_client_id ON policies(client_id);
CREATE INDEX CONCURRENTLY idx_policies_created_at ON policies(created_at);
CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX CONCURRENTLY idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Index composites
CREATE INDEX CONCURRENTLY idx_policies_client_status 
ON policies(client_id, status) WHERE status = 'active';

-- Index partiels
CREATE INDEX CONCURRENTLY idx_users_active 
ON users(email) WHERE is_active = true;
```

## 🔐 Sécurité

### Audit sécurité

```bash
#!/bin/bash
# scripts/security_audit.sh

echo "=== Audit sécurité MonAssurance ==="

# Analyse dépendances vulnérables
pip audit

# Scan sécurité code
bandit -r backend/ -f json -o security_report.json

echo "Audit terminé - voir security_report.json"
```

## 📞 Contacts et escalade

### Équipe

| Rôle | Nom | Contact | Disponibilité |
|------|-----|---------|---------------|
| Tech Lead | John Doe | +33123456789 | 24/7 |
| DevOps | Jane Smith | +33987654321 | Heures ouvrées |
| DBA | Bob Wilson | +33456789123 | Sur appel |

### Procédure d'escalade

1. **Niveau 1** (0-15 min): Auto-résolution, documentation
2. **Niveau 2** (15-30 min): Équipe de développement
3. **Niveau 3** (30+ min): Tech Lead + Management
4. **Niveau 4** (critique): CEO + Communication externe
