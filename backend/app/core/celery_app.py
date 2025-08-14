"""Configuration Celery pour MonAssurance.

Remplacement du système RQ par Celery pour une gestion plus robuste
des tâches asynchrones, notamment pour la génération de rapports lourds.
"""
from __future__ import annotations

import os

from celery import Celery
from celery.signals import worker_ready

from backend.app.core.config import get_settings

# Support Redis alternatif pour développement
try:
    import fakeredis  # noqa: F401
    USE_FAKE_REDIS = os.getenv("USE_FAKE_REDIS", "false").lower() == "true"
except ImportError:
    USE_FAKE_REDIS = False

# Configuration Celery
settings = get_settings()

# Configuration Redis
redis_url = settings.redis_url
if USE_FAKE_REDIS:
    # Utiliser FakeRedis pour les tests de développement
    redis_url = "redis://localhost:6379/0"  # FakeRedis utilise cette URL par défaut

# Instance Celery
celery_app = Celery(
    "monassurance",
    broker=redis_url,
    backend=redis_url,
    include=[
        "backend.app.services.report_tasks",
        "backend.app.services.celery_report_tasks",
        "backend.app.services.document_tasks",
        "backend.app.services.notification_tasks",
        "backend.app.services.monitoring_tasks"
    ]
)

# Configuration avancée
celery_app.conf.update(
    # Sérialisation JSON pour la sécurité
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Gestion des erreurs et retries
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Routing des tâches
    task_routes={
        "backend.app.services.report_tasks.*": {"queue": "reports"},
        "backend.app.services.document_tasks.*": {"queue": "documents"},
        "backend.app.services.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Limits par tâche
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes warning
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Résultats
    result_expires=3600,  # 1 heure
    result_persistent=True,
    
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule (pour tâches périodiques futures)
    beat_schedule={
        'cleanup-old-jobs': {
            'task': 'backend.app.services.maintenance_tasks.cleanup_old_report_jobs',
            'schedule': 3600.0,  # Chaque heure
        },
        'health-check': {
            'task': 'backend.app.services.monitoring_tasks.system_health_check',
            'schedule': 300.0,  # Toutes les 5 minutes
        },
    },
)

# Configuration spécifique par environnement
if settings.environment == "development":
    celery_app.conf.update(
        task_always_eager=False,  # Pas d'exécution immédiate en dev
        worker_log_level="DEBUG",
    )
elif settings.environment == "test":
    celery_app.conf.update(
        task_always_eager=True,  # Exécution immédiate pour les tests
        task_eager_propagates=True,
    )
elif settings.environment == "production":
    celery_app.conf.update(
        worker_log_level="INFO",
        task_compression="gzip",
        result_compression="gzip",
    )


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Signal envoyé quand un worker est prêt."""
    print(f"Celery worker {sender} is ready")


# Création des queues
CELERY_QUEUES = {
    "reports": {
        "routing_key": "reports",
        "priority": 5,
        "description": "Génération de rapports lourds"
    },
    "documents": {
        "routing_key": "documents", 
        "priority": 7,
        "description": "Traitement de documents"
    },
    "notifications": {
        "routing_key": "notifications",
        "priority": 3,
        "description": "Envoi de notifications"
    },
    "celery": {
        "routing_key": "celery",
        "priority": 6,
        "description": "Tâches système par défaut"
    }
}

# Auto-discovery des tâches
celery_app.autodiscover_tasks()
