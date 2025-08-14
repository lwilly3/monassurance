#!/usr/bin/env python3
"""
Script de migration SQLite vers PostgreSQL pour MonAssurance
"""
import asyncio
import sqlite3

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings


async def migrate_data():
    """Migre les données de SQLite vers PostgreSQL"""
    print("🔄 Début de la migration SQLite → PostgreSQL")
    
    # Configuration
    settings = get_settings()
    sqlite_path = "./monassurance.db"
    postgres_url = settings.database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    
    # Connexion SQLite
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
        sqlite_cursor = sqlite_conn.cursor()
        print("✅ Connexion SQLite réussie")
    except Exception as e:
        print(f"❌ Erreur SQLite: {e}")
        return
    
    # Connexion PostgreSQL
    try:
        pg_engine = create_async_engine(postgres_url)
        print("✅ Connexion PostgreSQL réussie")
    except Exception as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return
    
    try:
        async with pg_engine.begin() as pg_conn:
            # Migration des refresh_tokens (seulement les actifs)
            print("\n📋 Migration des refresh_tokens...")
            sqlite_cursor.execute("""
                SELECT token_hash, user_id, expires_at, issued_at, revoked_at, parent_id, device_label, ip_address, user_agent 
                FROM refresh_tokens 
                WHERE expires_at > datetime('now') AND revoked_at IS NULL
            """)
            tokens = sqlite_cursor.fetchall()
            
            migrated_tokens = 0
            for token in tokens:
                try:
                    await pg_conn.execute(text("""
                        INSERT INTO refresh_tokens (token_hash, user_id, expires_at, issued_at, revoked_at, parent_id, device_label, ip_address, user_agent)
                        VALUES (:token_hash, :user_id, :expires_at, :issued_at, :revoked_at, :parent_id, :device_label, :ip_address, :user_agent)
                        ON CONFLICT (token_hash) DO NOTHING
                    """), {
                        'token_hash': token['token_hash'],
                        'user_id': token['user_id'],
                        'expires_at': token['expires_at'],
                        'issued_at': token['issued_at'],
                        'revoked_at': token['revoked_at'],
                        'parent_id': token['parent_id'],
                        'device_label': token['device_label'],
                        'ip_address': token['ip_address'],
                        'user_agent': token['user_agent']
                    })
                    migrated_tokens += 1
                except Exception as e:
                    print(f"⚠️  Erreur migration token: {e}")
            
            print(f"✅ {migrated_tokens} refresh_tokens migrés")
            
            # Vérification finale
            print("\n📊 Vérification de la migration...")
            result = await pg_conn.execute(text("SELECT COUNT(*) FROM refresh_tokens"))
            pg_tokens_count = result.scalar()
            print(f"📋 Tokens dans PostgreSQL: {pg_tokens_count}")
            
            # Stats utilisateurs
            result = await pg_conn.execute(text("SELECT COUNT(*) FROM users"))
            users_count = result.scalar()
            print(f"👤 Utilisateurs dans PostgreSQL: {users_count}")
            
        await pg_engine.dispose()
        sqlite_conn.close()
        
        print("\n🎉 Migration terminée avec succès!")
        print("💡 Vous pouvez maintenant supprimer le fichier SQLite si vous le souhaitez")
        
    except Exception as e:
        print(f"❌ Erreur durant la migration: {e}")
        await pg_engine.dispose()
        sqlite_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
