 #!/usr/bin/env python3
"""
Dashboard simplifié en ligne de commande pour Celery
"""

import json
import os
import time
from datetime import datetime

import redis

from backend.app.core.celery_app import celery_app


def clear_screen():
    """Nettoyer l'écran"""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_celery_metrics():
    """Récupérer les métriques Celery/Redis"""
    metrics = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'workers': {},
        'tasks': {'total': 0, 'success': 0, 'failed': 0},
        'queues': {},
        'redis': {}
    }
    
    try:
        # Redis connection
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test Redis
        metrics['redis']['status'] = r.ping()
        redis_info = r.info()
        metrics['redis']['memory'] = redis_info.get('used_memory_human', '0B')
        metrics['redis']['clients'] = redis_info.get('connected_clients', 0)
        
        # Queue lengths
        for queue in ['reports', 'documents', 'notifications', 'celery']:
            length = r.llen(queue)
            metrics['queues'][queue] = length
        
        # Analyze Celery task results
        celery_keys = r.keys('celery-task-meta-*')
        metrics['tasks']['total'] = len(celery_keys)
        
        success_count = 0
        failed_count = 0
        total_time = 0
        time_count = 0
        
        for key in celery_keys[-20:]:  # Last 20 tasks
            try:
                result_data = r.get(key)
                if result_data:
                    result = json.loads(result_data)
                    status = result.get('status', 'UNKNOWN')
                    
                    if status == 'SUCCESS':
                        success_count += 1
                        if 'result' in result and isinstance(result['result'], dict):
                            proc_time = result['result'].get('processing_time_seconds', 0)
                            if proc_time:
                                total_time += proc_time
                                time_count += 1
                    elif status == 'FAILURE':
                        failed_count += 1
            except Exception:
                continue
        
        metrics['tasks']['success'] = success_count
        metrics['tasks']['failed'] = failed_count
        metrics['tasks']['avg_time'] = round(total_time / time_count, 2) if time_count > 0 else 0
        
        # Worker stats
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            if active_workers:
                for worker, tasks in active_workers.items():
                    metrics['workers'][worker] = {
                        'active_tasks': len(tasks),
                        'status': 'online'
                    }
        except Exception:
            pass
        
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics

def display_dashboard(metrics):
    """Afficher le dashboard"""
    clear_screen()
    
    print("🚀 " + "="*60)
    print("   DASHBOARD CELERY MONASSURANCE - TEMPS RÉEL")
    print("="*60 + " 🚀")
    print(f"🕐 Dernière mise à jour: {metrics['timestamp']}")
    print()
    
    # Status général
    redis_status = "✅ Opérationnel" if metrics.get('redis', {}).get('status') else "❌ Hors ligne"
    workers_count = len(metrics.get('workers', {}))
    worker_status = f"✅ {workers_count} actif(s)" if workers_count > 0 else "❌ Aucun worker"
    
    print("🔶 STATUT GÉNÉRAL")
    print(f"   Redis:    {redis_status}")
    print(f"   Workers:  {worker_status}")
    print()
    
    # Workers détail
    print("👷 WORKERS CELERY")
    workers = metrics.get('workers', {})
    if workers:
        for worker, info in workers.items():
            active = info.get('active_tasks', 0)
            status = info.get('status', 'unknown')
            print(f"   📍 {worker}")
            print(f"      Status: {status.upper()}")
            print(f"      Tâches actives: {active}")
    else:
        print("   ⚠️  Aucun worker actif")
    print()
    
    # Files d'attente
    print("📬 FILES D'ATTENTE")
    queues = metrics.get('queues', {})
    total_queued = sum(queues.values())
    for queue, length in queues.items():
        bar = "█" * min(length, 20) + "░" * max(0, 20-length)
        print(f"   {queue:12} [{bar}] {length:3d}")
    print(f"   {'TOTAL':12} {'':21} {total_queued:3d}")
    print()
    
    # Statistiques tâches
    print("📊 STATISTIQUES TÂCHES")
    tasks = metrics.get('tasks', {})
    total = tasks.get('total', 0)
    success = tasks.get('success', 0)
    failed = tasks.get('failed', 0)
    avg_time = tasks.get('avg_time', 0)
    
    success_rate = round(success / total * 100, 1) if total > 0 else 0
    
    print(f"   Total traités:     {total:6d}")
    print(f"   Succès:           {success:6d} ({success_rate:5.1f}%)")
    print(f"   Échecs:           {failed:6d}")
    print(f"   Temps moyen:      {avg_time:6.2f}s")
    print()
    
    # Redis info
    print("⚡ PERFORMANCE REDIS")
    redis_info = metrics.get('redis', {})
    memory = redis_info.get('memory', '0B')
    clients = redis_info.get('clients', 0)
    print(f"   Mémoire utilisée:  {memory:>10}")
    print(f"   Clients connectés: {clients:>10}")
    print()
    
    # Instructions
    print("🎮 COMMANDES")
    print("   [Ctrl+C] Quitter")
    print("   [Space]  Actualiser manuellement")
    print("="*60)
    
    if 'error' in metrics:
        print(f"❌ ERREUR: {metrics['error']}")

def main():
    """Fonction principale du dashboard"""
    print("🚀 Démarrage du dashboard Celery en temps réel...")
    print("📊 Surveillance des workers, queues et performances")
    print("⏳ Mise à jour automatique toutes les 5 secondes")
    print("\nAppuyez sur Ctrl+C pour quitter")
    time.sleep(3)
    
    try:
        while True:
            metrics = get_celery_metrics()
            display_dashboard(metrics)
            
            # Attendre 5 secondes
            for _i in range(50):  # 50 * 0.1 = 5 secondes
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        clear_screen()
        print("🛑 Dashboard arrêté")
        print("✅ Merci d'avoir utilisé le dashboard Celery !")

if __name__ == "__main__":
    main()
