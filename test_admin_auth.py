#!/usr/bin/env python3
"""
Test de l'authentification avec l'utilisateur admin par défaut.
"""


import requests


def test_admin_login():
    """Test de connexion avec l'utilisateur admin."""
    
    # URL de l'API d'authentification
    login_url = "http://localhost:8002/api/v1/auth/login"
    
    # Données de connexion
    credentials = {
        "username": "admin@monassurance.com",
        "password": "D3faultpass"
    }
    
    try:
        print("🔐 Test de connexion administrateur...")
        print(f"   URL: {login_url}")
        print(f"   Email: {credentials['username']}")
        print(f"   Mot de passe: {credentials['password']}")
        print()
        
        # Tentative de connexion
        response = requests.post(
            login_url,
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print("📊 Réponse du serveur:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Connexion réussie !")
            print(f"   Access token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   Token type: {data.get('token_type', 'N/A')}")
            return True
        else:
            print("❌ Connexion échouée !")
            print(f"   Contenu: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur !")
        print("   Assurez-vous que le serveur backend est démarré sur le port 8002")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


def test_protected_endpoint():
    """Test d'un endpoint protégé avec le token d'authentification."""
    
    # D'abord, obtenir un token
    login_url = "http://localhost:8002/api/v1/auth/login"
    credentials = {
        "username": "admin@monassurance.com",
        "password": "D3faultpass"
    }
    
    try:
        # Connexion
        response = requests.post(
            login_url,
            data=credentials,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code != 200:
            print("❌ Impossible d'obtenir un token d'authentification")
            return False
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("❌ Token d'accès manquant dans la réponse")
            return False
        
        # Test d'un endpoint protégé
        protected_url = "http://localhost:8002/api/v1/users/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print("🔒 Test endpoint protégé /users/me...")
        response = requests.get(protected_url, headers=headers, timeout=10)
        
        print("📊 Réponse:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Données utilisateur récupérées !")
            print(f"   ID: {user_data.get('id', 'N/A')}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            print(f"   Nom: {user_data.get('full_name', 'N/A')}")
            print(f"   Rôle: {user_data.get('role', 'N/A')}")
            return True
        else:
            print("❌ Accès à l'endpoint protégé échoué !")
            print(f"   Contenu: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Test de l'utilisateur administrateur par défaut")
    print("=" * 60)
    
    # Test 1: Connexion
    if test_admin_login():
        print("\n" + "=" * 60)
        
        # Test 2: Endpoint protégé
        test_protected_endpoint()
    
    print("\n" + "=" * 60)
    print("✨ Tests terminés !")
