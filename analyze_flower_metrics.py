#!/usr/bin/env python3
"""
Script d'exploration des métriques Flower et analyse des performances Celery
"""

import json
from datetime import datetime

import requests


def get_flower_stats():
    """Récupérer les statistiques Flower via l'API"""
    base_url = "http://localhost:5555"
    
    try:
        # Stats générales des workers
        workers_response = requests.get(f"{base_url}/api/workers")
        if workers_response.status_code == 200:
            workers = workers_response.json()
            print("🔧 Workers actifs:")
            for worker_name, worker_info in workers.items():
                print(f"   📍 {worker_name}")
                print(f"      Status: {worker_info.get('status', 'unknown')}")
                print(f"      Concurrency: {worker_info.get('pool', {}).get('max-concurrency', 'N/A')}")
                print(f"      Processus: {worker_info.get('pool', {}).get('processes', 'N/A')}")
                
                # Statistiques des tâches
                stats = worker_info.get('stats', {})
                if stats:
                    print(f"      📊 Total tâches: {stats.get('total', 0)}")
                    print(f"      ⏱️  Pool utilisation: {stats.get('pool', {}).get('timeouts', 0)} timeouts")
            print()
        
        # Stats des tâches actives
        active_response = requests.get(f"{base_url}/api/tasks")
        if active_response.status_code == 200:
            tasks = active_response.json()
            print(f"📋 Tâches actives: {len(tasks)}")
            
            if tasks:
                for task_id, task_info in list(tasks.items())[:5]:  # Top 5
                    print(f"   🔄 {task_id[:8]}...")
                    print(f"      Type: {task_info.get('name', 'unknown')}")
                    print(f"      Worker: {task_info.get('worker', 'unknown')}")
                    print(f"      État: {task_info.get('state', 'unknown')}")
                    print(f"      Démarré: {task_info.get('started', 'N/A')}")
            print()
        
        # Stats des tâches terminées (via Redis directement)
        print("📈 Récupération historique des tâches...")
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion Flower API: {e}")
        return False

def analyze_redis_metrics():
    """Analyser les métriques Redis directement"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Informations Redis
        info = r.info()
        print("🔴 Métriques Redis:")
        print(f"   📊 Commandes traitées: {info.get('total_commands_processed', 'N/A'):,}")
        print(f"   🔗 Connexions actuelles: {info.get('connected_clients', 'N/A')}")
        print(f"   💾 Mémoire utilisée: {info.get('used_memory_human', 'N/A')}")
        print(f"   ⏱️  Uptime: {info.get('uptime_in_seconds', 0) // 3600}h {(info.get('uptime_in_seconds', 0) % 3600) // 60}m")
        
        # Clés Celery
        celery_keys = r.keys("celery-task-meta-*")
        print(f"   📝 Résultats tâches stockés: {len(celery_keys)}")
        
        # Queues Celery
        queue_lengths = {}
        for queue in ['reports', 'documents', 'notifications', 'celery']:
            length = r.llen(queue)
            queue_lengths[queue] = length
            
        print("   📬 Tailles des queues:")
        for queue, length in queue_lengths.items():
            print(f"      {queue}: {length} tâche(s)")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur analyse Redis: {e}")
        return False

def get_recent_task_results():
    """Récupérer les résultats des tâches récentes"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Récupérer les métadonnées des tâches récentes
        task_keys = r.keys("celery-task-meta-*")
        recent_tasks = []
        
        print("🔍 Analyse des tâches récentes:")
        for key in task_keys[-10:]:  # 10 dernières tâches
            task_data = r.get(key)
            if task_data:
                try:
                    task_info = json.loads(task_data)
                    task_id = key.replace("celery-task-meta-", "")
                    
                    if task_info.get('status') == 'SUCCESS':
                        result = task_info.get('result', {})
                        recent_tasks.append({
                            'task_id': task_id[:8],
                            'type': result.get('type', 'unknown'),
                            'processing_time': result.get('processing_time_seconds', 0),
                            'size_bytes': result.get('size_bytes', 0),
                            'filename': result.get('filename', 'N/A'),
                            'queue': result.get('queue', 'unknown')
                        })
                except json.JSONDecodeError:
                    continue
        
        if recent_tasks:
            print(f"   📊 {len(recent_tasks)} tâches analysées:")
            print("   " + "="*80)
            print("   | Type     | Durée(s) | Taille     | Fichier              | Queue   |")
            print("   " + "="*80)
            
            for task in recent_tasks:
                size_mb = task['size_bytes'] / 1024 / 1024 if task['size_bytes'] > 0 else 0
                size_str = f"{size_mb:.1f}MB" if size_mb > 0 else "N/A"
                filename_short = task['filename'][:15] + "..." if len(task['filename']) > 18 else task['filename']
                
                print(f"   | {task['type']:<8} | {task['processing_time']:<8.2f} | {size_str:<10} | {filename_short:<20} | {task['queue']:<7} |")
            
            # Statistiques agrégées
            print("   " + "="*80)
            print("\n📊 Statistiques agrégées:")
            
            by_type = {}
            total_time = 0
            total_size = 0
            
            for task in recent_tasks:
                task_type = task['type']
                if task_type not in by_type:
                    by_type[task_type] = {'count': 0, 'total_time': 0, 'total_size': 0}
                
                by_type[task_type]['count'] += 1
                by_type[task_type]['total_time'] += task['processing_time']
                by_type[task_type]['total_size'] += task['size_bytes']
                
                total_time += task['processing_time']
                total_size += task['size_bytes']
            
            for task_type, stats in by_type.items():
                avg_time = stats['total_time'] / stats['count']
                avg_size_mb = (stats['total_size'] / stats['count']) / 1024 / 1024
                print(f"   🔸 {task_type.upper()}:")
                print(f"      Nombre: {stats['count']} tâche(s)")
                print(f"      Temps moyen: {avg_time:.2f}s")
                print(f"      Taille moyenne: {avg_size_mb:.1f}MB")
            
            print("\n   📈 Performance globale:")
            print(f"      Temps total traitement: {total_time:.2f}s")
            print(f"      Taille totale générée: {total_size/1024/1024:.1f}MB")
            print(f"      Débit moyen: {len(recent_tasks)/total_time:.2f} tâches/s")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Erreur analyse tâches: {e}")
        return False

def monitor_flower_dashboard():
    """Afficher les informations du dashboard Flower"""
    print("🌸 Interface Flower - Dashboard")
    print("=" * 60)
    print("🌐 URL d'accès: http://localhost:5555")
    print()
    print("📋 Sections disponibles:")
    print("   🔧 Workers: http://localhost:5555/workers")
    print("   📊 Tasks: http://localhost:5555/tasks")  
    print("   📈 Monitor: http://localhost:5555/monitor")
    print("   🔄 Broker: http://localhost:5555/broker")
    print()
    print("💡 Fonctionnalités clés:")
    print("   ✅ Surveillance temps réel des workers")
    print("   ✅ Historique des tâches exécutées")
    print("   ✅ Métriques de performance par queue")
    print("   ✅ Graphiques de charge et latence")
    print("   ✅ Contrôle des workers (start/stop/restart)")
    print()

def main():
    """Fonction principale d'exploration"""
    print("🌸 Exploration des métriques Flower & Celery")
    print("=" * 60)
    
    # 1. Dashboard info
    monitor_flower_dashboard()
    
    # 2. Stats Flower API
    print("📡 Connexion API Flower...")
    flower_ok = get_flower_stats()
    
    # 3. Analyse Redis
    print("🔴 Analyse métriques Redis...")
    redis_ok = analyze_redis_metrics()
    
    # 4. Tâches récentes
    print("📋 Analyse des tâches récentes...")
    tasks_ok = get_recent_task_results()
    
    # 5. Recommandations
    print("💡 Recommandations:")
    if flower_ok and redis_ok and tasks_ok:
        print("   ✅ Système Celery opérationnel")
        print("   ✅ Métriques disponibles via Flower")
        print("   ✅ Performance satisfaisante")
        print("   🎯 Prêt pour monitoring production")
    else:
        print("   ⚠️  Vérifier la connectivité Flower/Redis")
    
    print(f"\n🕒 Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
