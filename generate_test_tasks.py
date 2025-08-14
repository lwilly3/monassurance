#!/usr/bin/env python3
"""
Générateur de tâches pour tester le dashboard en temps réel
"""

import random
import time

from backend.app.services.celery_report_tasks import generate_dummy_report, generate_heavy_report


def generate_test_tasks():
    """Générer des tâches de test pour alimenter le dashboard"""
    print("🚀 Génération de tâches de test pour le dashboard")
    print("=" * 50)
    
    # Types de rapports
    report_types = ['pdf', 'excel', 'analysis']
    
    for i in range(10):
        # Générer un rapport lourd aléatoire
        report_type = random.choice(report_types)
        params = {
            'pages': random.randint(5, 20),
            'processing_time': random.randint(2, 8)
        }
        
        print(f"\n📋 Tâche {i+1}/10: Rapport {report_type}")
        print(f"   Pages: {params['pages']}")
        print(f"   Temps: {params['processing_time']}s")
        
        try:
            # Lancer la tâche
            task = generate_heavy_report.delay(report_type, params, i+1)
            print(f"   ✅ Tâche créée: {task.id}")
            
            # Attendre un peu entre les tâches
            wait_time = random.uniform(1, 3)
            print(f"   ⏳ Attente {wait_time:.1f}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n🎉 Toutes les tâches ont été générées !")
    print("📊 Consultez le dashboard pour voir l'activité")

def generate_dummy_tasks():
    """Générer des tâches factices rapides"""
    print("\n🔧 Génération de tâches factices...")
    
    for i in range(5):
        try:
            task = generate_dummy_report.delay(f"test_report_{i}")
            print(f"✅ Tâche factice {i+1}: {task.id}")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Erreur tâche factice {i+1}: {e}")

if __name__ == "__main__":
    print("🎯 Générateur de tâches pour dashboard Celery")
    print("\nQuel type de tâches voulez-vous générer ?")
    print("1. Rapports lourds (pour voir les métriques de performance)")
    print("2. Tâches factices (pour tester rapidement)")
    print("3. Les deux")
    
    choice = input("\nChoix (1/2/3): ").strip()
    
    if choice == "1":
        generate_test_tasks()
    elif choice == "2":
        generate_dummy_tasks()
    elif choice == "3":
        generate_dummy_tasks()
        time.sleep(2)
        generate_test_tasks()
    else:
        print("❌ Choix invalide")
