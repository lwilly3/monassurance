#!/usr/bin/env python3
"""
Script de données de remplissage pour MonAssurance
Génère des données de test réalistes pour le développement
"""
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.models.client import Client
from backend.app.db.models.company import Company
from backend.app.db.models.policy import Policy
from backend.app.db.models.storage_config import StorageConfig

# Données de test
COMPANIES_DATA = [
    {
        "name": "AXA France",
        "code": "AXA_FR"
    },
    {
        "name": "Allianz France", 
        "code": "ALLIANZ_FR"
    },
    {
        "name": "Generali France",
        "code": "GENERALI_FR"
    },
    {
        "name": "MAIF",
        "code": "MAIF_FR"
    },
    {
        "name": "MACIF",
        "code": "MACIF_FR"
    },
    {
        "name": "Groupama",
        "code": "GROUPAMA_FR"
    }
]

CLIENTS_DATA = [
    {
        "first_name": "Jean",
        "last_name": "Dupont", 
        "email": "jean.dupont@email.com",
        "phone": "01 23 45 67 89",
        "address": "123 Rue de la Paix, 75001 Paris"
    },
    {
        "first_name": "Marie",
        "last_name": "Martin",
        "email": "marie.martin@email.com", 
        "phone": "01 98 76 54 32",
        "address": "456 Avenue des Champs, 75008 Paris"
    },
    {
        "first_name": "Pierre",
        "last_name": "Durand",
        "email": "pierre.durand@email.com",
        "phone": "01 11 22 33 44",
        "address": "789 Boulevard Saint-Germain, 75006 Paris"
    },
    {
        "first_name": "Sophie",
        "last_name": "Leroy",
        "email": "sophie.leroy@email.com",
        "phone": "01 55 66 77 88",
        "address": "321 Rue de Rivoli, 75004 Paris"
    },
    {
        "first_name": "Antoine",
        "last_name": "Moreau",
        "email": "antoine.moreau@email.com",
        "phone": "01 77 88 99 00",
        "address": "654 Avenue Montaigne, 75008 Paris"
    },
    {
        "first_name": "Isabelle",
        "last_name": "Simon",
        "email": "isabelle.simon@email.com",
        "phone": "01 44 55 66 77",
        "address": "987 Rue du Faubourg Saint-Honoré, 75008 Paris"
    },
    {
        "first_name": "Thomas",
        "last_name": "Petit",
        "email": "thomas.petit@email.com", 
        "phone": "01 88 99 00 11",
        "address": "147 Boulevard Haussmann, 75008 Paris"
    },
    {
        "first_name": "Catherine",
        "last_name": "Roux",
        "email": "catherine.roux@email.com",
        "phone": "01 22 33 44 55",
        "address": "258 Rue de la République, 69002 Lyon"
    }
]

POLICY_TYPES = [
    "Assurance Auto",
    "Assurance Habitation", 
    "Assurance Santé",
    "Assurance Vie",
    "Assurance Professionnelle",
    "Assurance Voyage",
    "Assurance Multirisque"
]

async def seed_database():
    """Remplit la base de données avec des données de test"""
    print("🌱 Début du remplissage de la base de données...")
    
    settings = get_settings()
    async_url = settings.database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(async_url)
    async_session_factory = sessionmaker(engine, class_=AsyncSession)
    
    try:
        async with async_session_factory() as session:
            # 1. Créer les compagnies
            print("🏢 Création des compagnies d'assurance...")
            companies = []
            for company_data in COMPANIES_DATA:
                company = Company(**company_data)
                session.add(company)
                companies.append(company)
            
            await session.flush()  # Pour obtenir les IDs
            print(f"✅ {len(companies)} compagnies créées")
            
            # 2. Créer les clients
            print("👥 Création des clients...")
            clients = []
            for client_data in CLIENTS_DATA:
                client = Client(**client_data)
                session.add(client)
                clients.append(client)
            
            await session.flush()
            print(f"✅ {len(clients)} clients créés")
            
            # 3. Créer les polices
            print("📋 Création des polices d'assurance...")
            policies = []
            policy_counter = 1
            
            for _i, client in enumerate(clients):
                # Chaque client a 1-3 polices
                num_policies = random.randint(1, 3)
                
                for _j in range(num_policies):
                    company = random.choice(companies)
                    policy_type = random.choice(POLICY_TYPES)
                    
                    # Dates
                    effective_date = datetime.now() - timedelta(days=random.randint(30, 365))
                    expiry_date = effective_date + timedelta(days=365)
                    
                    # Montant prime (entre 300€ et 3000€)
                    premium_amount = Decimal(str(random.randint(300, 3000)))
                    
                    policy = Policy(
                        policy_number=f"P-2024-{policy_counter:03d}",
                        client_id=client.id,
                        company_id=company.id,
                        product_name=policy_type,
                        premium_amount=premium_amount,
                        effective_date=effective_date,
                        expiry_date=expiry_date
                    )
                    
                    session.add(policy)
                    policies.append(policy)
                    policy_counter += 1
            
            await session.flush()
            print(f"✅ {len(policies)} polices créées")
            
            # 4. Configuration de stockage par défaut
            print("⚙️ Configuration du stockage...")
            existing_config = await session.execute(
                text("SELECT COUNT(*) FROM storage_config")
            )
            config_count = existing_config.scalar()
            
            if config_count == 0:
                storage_config = StorageConfig(
                    backend="local",
                    gdrive_folder_id=None,
                    gdrive_service_account_json_path=None,
                    s3_bucket=None,
                    s3_region=None,
                    s3_endpoint_url=None
                )
                session.add(storage_config)
                print("✅ Configuration de stockage créée")
            else:
                print("ℹ️ Configuration de stockage déjà existante")
            
            # Commit final
            await session.commit()
            
            # 5. Statistiques finales
            print("\n📊 Statistiques des données créées:")
            print(f"   🏢 Compagnies: {len(companies)}")
            print(f"   👥 Clients: {len(clients)}")
            print(f"   📋 Polices: {len(policies)}")
            
            print("\n🎉 Données de remplissage créées avec succès!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du remplissage: {e}")
        return False
    finally:
        await engine.dispose()

async def clear_data():
    """Supprime toutes les données de test (garde les utilisateurs et config)"""
    print("🧹 Nettoyage des données de test...")
    
    settings = get_settings()
    async_url = settings.database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(async_url)
    
    try:
        async with engine.begin() as conn:
            # Ordre important à cause des clés étrangères
            await conn.execute(text("DELETE FROM policies"))
            await conn.execute(text("DELETE FROM clients"))
            await conn.execute(text("DELETE FROM companies"))
            print("✅ Données de test supprimées")
            return True
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_data())
    else:
        asyncio.run(seed_database())
