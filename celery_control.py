#!/usr/bin/env python3
"""
Gestionnaire simple pour démarrer le dashboard et générer des tâches
"""

import subprocess
import sys
import time


def check_services():
    """Vérifier l'état des services"""
    print("🔍 Vérification des services...")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_ok = r.ping()
        print(f"   Redis: {'✅' if redis_ok else '❌'}")
    except Exception:
        redis_ok = False
        print("   Redis: ❌")
    
    # Check Celery workers
    try:
        from backend.app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active = inspect.active()
        worker_count = len(active) if active else 0
        print(f"   Workers: {'✅' if worker_count > 0 else '❌'} ({worker_count} actif(s))")
    except Exception:
        worker_count = 0
        print("   Workers: ❌")
    
    return redis_ok and worker_count > 0

def start_dashboard():
    """Démarrer le dashboard en temps réel"""
    print("📊 Démarrage du dashboard...")
    try:
        subprocess.run([sys.executable, "live_dashboard.py"])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard arrêté")

def generate_tasks():
    """Générer des tâches de test"""
    print("🎯 Génération de tâches de test...")
    try:
        subprocess.run([sys.executable, "generate_test_tasks.py"])
    except KeyboardInterrupt:
        print("\n🛑 Génération interrompue")

def main():
    """Menu principal"""
    print("🚀 GESTIONNAIRE DASHBOARD CELERY")
    print("=" * 50)
    
    # Vérifier les services
    if not check_services():
        print("\n⚠️  Services manquants. Assurez-vous que:")
        print("   1. Redis est démarré: brew services start redis")
        print("   2. Worker Celery est actif")
        print("   3. API FastAPI fonctionne")
        return
    
    print("\n✅ Tous les services sont opérationnels!")
    print("\nQue voulez-vous faire ?")
    print("1. 📊 Lancer le dashboard en temps réel")
    print("2. 🎯 Générer des tâches de test")
    print("3. 🚀 Les deux (dashboard + tâches)")
    
    choice = input("\nChoix (1/2/3): ").strip()
    
    if choice == "1":
        start_dashboard()
    elif choice == "2":
        generate_tasks()
    elif choice == "3":
        print("\n🚀 Mode complet: Dashboard + Génération de tâches")
        print("📊 Le dashboard va démarrer dans 3 secondes...")
        print("🎯 Utilisez un autre terminal pour générer des tâches avec:")
        print("   python generate_test_tasks.py")
        time.sleep(3)
        start_dashboard()
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main()
