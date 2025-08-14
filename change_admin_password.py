#!/usr/bin/env python3
"""
Script pour changer le mot de passe de l'administrateur par défaut.
Usage: python change_admin_password.py
"""

import sys
import getpass
from sqlalchemy.orm import sessionmaker
from backend.app.db.session import engine
from backend.app.db.models.user import User
from backend.app.core.security import get_password_hash, verify_password


def change_admin_password():
    """Change le mot de passe de l'utilisateur administrateur."""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Rechercher l'utilisateur admin
        admin_user = session.query(User).filter(User.email == 'admin@monassurance.com').first()
        
        if not admin_user:
            print("❌ Utilisateur administrateur non trouvé !")
            print("   Assurez-vous que la migration pour créer l'admin a été exécutée.")
            return False
        
        print("🔑 Changement du mot de passe administrateur")
        print(f"   Utilisateur: {admin_user.email} ({admin_user.full_name})")
        print()
        
        # Vérification du mot de passe actuel
        current_password = getpass.getpass("Mot de passe actuel: ")
        
        if not verify_password(current_password, admin_user.hashed_password):
            print("❌ Mot de passe actuel incorrect !")
            return False
        
        # Saisie du nouveau mot de passe
        new_password = getpass.getpass("Nouveau mot de passe: ")
        
        if len(new_password) < 8:
            print("❌ Le mot de passe doit contenir au moins 8 caractères !")
            return False
        
        # Confirmation du nouveau mot de passe
        confirm_password = getpass.getpass("Confirmer le nouveau mot de passe: ")
        
        if new_password != confirm_password:
            print("❌ Les mots de passe ne correspondent pas !")
            return False
        
        # Mise à jour du mot de passe
        admin_user.hashed_password = get_password_hash(new_password)
        session.commit()
        
        print("✅ Mot de passe administrateur mis à jour avec succès !")
        print("   Vous pouvez maintenant vous connecter avec le nouveau mot de passe.")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du changement de mot de passe: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()


def reset_to_default():
    """Remet le mot de passe admin par défaut (D3faultpass)."""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Rechercher l'utilisateur admin
        admin_user = session.query(User).filter(User.email == 'admin@monassurance.com').first()
        
        if not admin_user:
            print("❌ Utilisateur administrateur non trouvé !")
            return False
        
        # Confirmation de la réinitialisation
        confirm = input("⚠️  Voulez-vous vraiment remettre le mot de passe par défaut ? (oui/non): ")
        
        if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Réinitialisation annulée.")
            return False
        
        # Réinitialisation du mot de passe
        admin_user.hashed_password = get_password_hash("D3faultpass")
        session.commit()
        
        print("✅ Mot de passe administrateur réinitialisé !")
        print("   Email: admin@monassurance.com")
        print("   Mot de passe: D3faultpass")
        print("   ⚠️  CHANGEZ ce mot de passe dès que possible !")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()


if __name__ == "__main__":
    print("🔐 Gestion du mot de passe administrateur")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_to_default()
    else:
        change_admin_password()
