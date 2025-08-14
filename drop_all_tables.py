#!/usr/bin/env python3
"""
Script pour supprimer toutes les tables de la base de données PostgreSQL
"""
from sqlalchemy import create_engine, text

from backend.app.core.config import get_settings


def drop_all_tables():
    """Supprime toutes les tables de la base de données"""
    print("🗑️ Suppression de toutes les tables...")
    
    settings = get_settings()
    # Utiliser l'URL synchrone pour cette opération
    sync_url = settings.database_url
    
    engine = create_engine(sync_url)
    
    try:
        with engine.begin() as conn:
            # Désactiver les contraintes de clés étrangères temporairement
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Obtenir toutes les tables
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tables trouvées: {', '.join(tables)}")
            
            # Supprimer chaque table
            for table in tables:
                print(f"🗑️ Suppression de la table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            # Réactiver les contraintes
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            
            print("✅ Toutes les tables ont été supprimées!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False
    finally:
        engine.dispose()

def verify_empty_database():
    """Vérifie que la base est bien vide"""
    print("\n🔍 Vérification de l'état de la base...")
    
    settings = get_settings()
    sync_url = settings.database_url
    engine = create_engine(sync_url)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            
            print(f"📊 Nombre de tables restantes: {table_count}")
            
            if table_count == 0:
                print("✅ Base de données complètement vide!")
            else:
                # Lister les tables restantes
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                remaining_tables = [row[0] for row in result.fetchall()]
                print(f"⚠️ Tables restantes: {', '.join(remaining_tables)}")
            
            return table_count == 0
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🚨 ATTENTION: Cette opération va supprimer TOUTES les tables!")
    print("📋 Cela inclut les utilisateurs, données, et configuration.")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        pass  # Force mode, skip confirmation
    else:
        confirm = input("\n⚡ Êtes-vous sûr de vouloir continuer? (tapez 'OUI' pour confirmer): ")
        if confirm != "OUI":
            print("❌ Opération annulée")
            sys.exit(1)
    
    success = drop_all_tables()
    if success:
        verify_empty_database()
        print("\n🎯 Base de données prête pour une reconstruction complète!")
    else:
        print("\n❌ Échec de la suppression des tables")
        sys.exit(1)
