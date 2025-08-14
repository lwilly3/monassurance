#!/usr/bin/env python3
"""
Configuration Celery avec FakeRedis intégré pour les tests
"""

import fakeredis

# Patcher Redis pour utiliser FakeRedis
import redis

redis_server = fakeredis.FakeServer()
original_redis = redis.Redis

def patched_redis(*args, **kwargs):
    # Utiliser FakeRedis au lieu de Redis réel
    return fakeredis.FakeRedis(server=redis_server, decode_responses=True)

# Appliquer le patch
redis.Redis = patched_redis
redis.StrictRedis = patched_redis

# Maintenant importer Celery après le patch
from backend.app.core.celery_app import celery_app

if __name__ == "__main__":
    print("✅ FakeRedis configuré pour Celery")
    print(f"📍 Celery app: {celery_app.main}")
    print(f"📍 Broker: {celery_app.conf.broker_url}")
    
    # Tester la connexion
    try:
        # Importer une tâche pour tester
        from backend.app.services.celery_report_tasks import generate_dummy_report
        
        # Envoyer une tâche test
        result = generate_dummy_report.delay("test")
        print(f"✅ Tâche envoyée: {result.id}")
        
        # Vérifier le statut
        print(f"📊 Statut: {result.status}")
        
    except Exception as e:
        print(f"❌ Erreur test tâche: {e}")
