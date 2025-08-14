#!/usr/bin/env python3
"""
Test simple des rapports lourds sans Celery - test du fallback
"""

import sys
import time

import requests


def test_heavy_reports():
    """Test des rapports lourds via l'API"""
    base_url = "http://localhost:8000"
    
    print("🧪 Test des rapports lourds (mode fallback)")
    print("=" * 50)
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code != 200:
            print(f"❌ API non accessible: {response.status_code}")
            return False
        print("✅ API accessible")
    except Exception as e:
        print(f"❌ Erreur connexion API: {e}")
        return False
    
    # Test 1: Rapport PDF lourd
    print("\n📄 Test 1: Rapport PDF lourd")
    try:
        params = {
            "report_type": "pdf",
            "pages": 10,
            "processing_time": 5
        }
        
        response = requests.post(
            f"{base_url}/reports/heavy",
            params=params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data.get("job_id")
            print(f"   ✅ Job créé: {job_id}")
            
            # Suivre le statut du job
            for i in range(5):
                time.sleep(2)
                try:
                    status_response = requests.get(f"{base_url}/reports/jobs/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status")
                        print(f"   📊 Statut ({i+1}/5): {status}")
                        
                        if status in ["completed", "failed"]:
                            if status == "completed":
                                print("   ✅ Job terminé avec succès!")
                                print(f"   📁 Fichier: {status_data.get('result', {}).get('file_path')}")
                            else:
                                print(f"   ❌ Job échoué: {status_data.get('error')}")
                            break
                    else:
                        print(f"   ⚠️  Erreur statut: {status_response.status_code}")
                except Exception as e:
                    print(f"   ⚠️  Erreur suivi: {e}")
        elif response.status_code == 503:
            print("   ⚠️  Celery indisponible (comportement attendu)")
        else:
            print(f"   ❌ Erreur inattendue: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Erreur test PDF: {e}")
    
    # Test 2: Rapport Excel lourd
    print("\n📊 Test 2: Rapport Excel lourd")
    try:
        params = {
            "report_type": "excel",
            "pages": 5,
            "processing_time": 3
        }
        
        response = requests.post(
            f"{base_url}/reports/heavy",
            params=params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 202:
            job_data = response.json()
            print(f"   ✅ Job Excel créé: {job_data.get('job_id')}")
        elif response.status_code == 503:
            print("   ⚠️  Celery indisponible (comportement attendu)")
    
    except Exception as e:
        print(f"   ❌ Erreur test Excel: {e}")
    
    # Test 3: Rapport Analysis lourd
    print("\n🔬 Test 3: Rapport Analysis lourd")
    try:
        params = {
            "report_type": "analysis",
            "pages": 15,
            "processing_time": 8
        }
        
        response = requests.post(
            f"{base_url}/reports/heavy",
            params=params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 202:
            job_data = response.json()
            print(f"   ✅ Job Analysis créé: {job_data.get('job_id')}")
        elif response.status_code == 503:
            print("   ⚠️  Celery indisponible (comportement attendu)")
    
    except Exception as e:
        print(f"   ❌ Erreur test Analysis: {e}")
    
    # Test 4: Type de rapport invalide
    print("\n❌ Test 4: Type de rapport invalide")
    try:
        params = {
            "report_type": "invalid",
            "pages": 1,
            "processing_time": 1
        }
        
        response = requests.post(
            f"{base_url}/reports/heavy",
            params=params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Validation échoue comme attendu")
        else:
            print(f"   ⚠️  Status inattendu: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Erreur test validation: {e}")
    
    print("\n🎯 Tests terminés!")
    return True

if __name__ == "__main__":
    # Lancer le serveur API en arrière-plan
    import subprocess
    
    def start_api_server():
        cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            return process
        except Exception as e:
            print(f"❌ Erreur démarrage API: {e}")
            return None
    
    print("🚀 Démarrage du serveur API...")
    api_process = start_api_server()
    
    if api_process:
        # Attendre que l'API démarre
        print("⏳ Attente démarrage API...")
        time.sleep(5)
        
        try:
            # Exécuter les tests
            success = test_heavy_reports()
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrompus")
            success = False
        
        finally:
            # Arrêter le serveur API
            print("\n🛑 Arrêt du serveur API...")
            api_process.terminate()
            api_process.wait()
            print("✅ Serveur arrêté")
        
        sys.exit(0 if success else 1)
    else:
        print("❌ Impossible de démarrer le serveur API")
        sys.exit(1)
