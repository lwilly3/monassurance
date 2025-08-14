#!/usr/bin/env python3
"""
Dashboard en temps réel pour monitoring Celery/Redis
Interface web simple avec mise à jour automatique
"""

import json
from datetime import datetime

import redis
from flask import Flask, jsonify, render_template

from backend.app.core.celery_app import celery_app

app = Flask(__name__)

# Configuration Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class CeleryMonitor:
    def __init__(self):
        self.metrics = {
            'workers': {},
            'tasks': {
                'total': 0,
                'success': 0,
                'failed': 0,
                'active': 0,
                'queue_lengths': {}
            },
            'performance': {
                'avg_task_time': 0,
                'tasks_per_minute': 0,
                'redis_memory': 0
            },
            'history': []
        }
        self.last_update = datetime.now()
    
    def get_worker_stats(self):
        """Récupérer les statistiques des workers"""
        try:
            inspect = celery_app.control.inspect()
            
            # Workers actifs
            active_workers = inspect.active()
            registered = inspect.registered()
            stats = inspect.stats()
            
            workers_info = {}
            if active_workers:
                for worker, tasks in active_workers.items():
                    workers_info[worker] = {
                        'active_tasks': len(tasks),
                        'status': 'online',
                        'registered_tasks': len(registered.get(worker, [])) if registered else 0
                    }
            
            if stats:
                for worker, stat in stats.items():
                    if worker in workers_info:
                        workers_info[worker].update({
                            'total_tasks': stat.get('total', {}),
                            'rusage': stat.get('rusage', {}),
                            'clock': stat.get('clock', 0)
                        })
            
            return workers_info
        except Exception as e:
            print(f"Erreur récupération workers: {e}")
            return {}
    
    def get_redis_stats(self):
        """Récupérer les statistiques Redis"""
        try:
            info = redis_client.info()
            
            # Longueurs des queues
            queue_lengths = {}
            for queue in ['reports', 'documents', 'notifications', 'celery']:
                length = redis_client.llen(queue)
                queue_lengths[queue] = length
            
            return {
                'memory_used': info.get('used_memory_human', '0B'),
                'memory_peak': info.get('used_memory_peak_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'queue_lengths': queue_lengths
            }
        except Exception as e:
            print(f"Erreur Redis stats: {e}")
            return {'queue_lengths': {}}
    
    def get_task_metrics(self):
        """Analyser les métriques des tâches via Redis"""
        try:
            # Compter les clés de résultats Celery
            celery_keys = redis_client.keys('celery-task-meta-*')
            
            success_count = 0
            failed_count = 0
            total_time = 0
            task_count = 0
            
            for key in celery_keys[-50:]:  # Analyser les 50 dernières tâches
                try:
                    result_data = redis_client.get(key)
                    if result_data:
                        result = json.loads(result_data)
                        status = result.get('status', 'UNKNOWN')
                        
                        if status == 'SUCCESS':
                            success_count += 1
                            # Estimer le temps d'exécution si disponible
                            if 'result' in result and isinstance(result['result'], dict):
                                proc_time = result['result'].get('processing_time_seconds', 0)
                                if proc_time:
                                    total_time += proc_time
                                    task_count += 1
                        elif status == 'FAILURE':
                            failed_count += 1
                except Exception:
                    continue
            
            avg_time = total_time / task_count if task_count > 0 else 0
            
            return {
                'total': len(celery_keys),
                'success': success_count,
                'failed': failed_count,
                'avg_time': round(avg_time, 2)
            }
        except Exception as e:
            print(f"Erreur task metrics: {e}")
            return {'total': 0, 'success': 0, 'failed': 0, 'avg_time': 0}
    
    def update_metrics(self):
        """Mettre à jour toutes les métriques"""
        try:
            # Workers
            self.metrics['workers'] = self.get_worker_stats()
            
            # Redis
            redis_stats = self.get_redis_stats()
            
            # Tâches
            task_metrics = self.get_task_metrics()
            self.metrics['tasks'].update(task_metrics)
            self.metrics['tasks']['queue_lengths'] = redis_stats.get('queue_lengths', {})
            
            # Performance
            self.metrics['performance'] = {
                'avg_task_time': task_metrics.get('avg_time', 0),
                'redis_memory': redis_stats.get('memory_used', '0B'),
                'redis_clients': redis_stats.get('connected_clients', 0),
                'queue_total': sum(redis_stats.get('queue_lengths', {}).values())
            }
            
            # Historique (garder les 100 derniers points)
            self.metrics['history'].append({
                'timestamp': datetime.now().isoformat(),
                'active_tasks': sum(w.get('active_tasks', 0) for w in self.metrics['workers'].values()),
                'queue_total': self.metrics['performance']['queue_total'],
                'success_rate': (
                    task_metrics.get('success', 0) / max(task_metrics.get('total', 1), 1) * 100
                )
            })
            
            if len(self.metrics['history']) > 100:
                self.metrics['history'] = self.metrics['history'][-100:]
            
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"Erreur update metrics: {e}")

# Instance globale du monitor
monitor = CeleryMonitor()

@app.route('/')
def dashboard():
    """Page principale du dashboard"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def api_metrics():
    """API pour récupérer les métriques en JSON"""
    monitor.update_metrics()
    return jsonify({
        'status': 'success',
        'timestamp': monitor.last_update.isoformat(),
        'data': monitor.metrics
    })

@app.route('/api/health')
def api_health():
    """Health check du dashboard"""
    try:
        # Test Redis
        redis_ok = redis_client.ping()
        
        # Test Celery
        celery_ok = True
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            celery_ok = stats is not None
        except Exception:
            celery_ok = False
        
        return jsonify({
            'status': 'healthy' if redis_ok and celery_ok else 'degraded',
            'redis': redis_ok,
            'celery': celery_ok,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Démarrage du dashboard Celery...")
    print("📊 Dashboard accessible sur http://localhost:3001")
    print("🔗 API metrics: http://localhost:3001/api/metrics")
    print("💊 Health check: http://localhost:3001/api/health")
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=3001, debug=False, threaded=True)
