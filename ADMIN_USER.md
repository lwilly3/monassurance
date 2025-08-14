# 👨‍💼 Utilisateur Administrateur Par Défaut

## 📋 Vue d'ensemble

Un utilisateur administrateur est automatiquement créé lors de l'application des migrations de base de données. Cet utilisateur permet un accès immédiat à l'application sans avoir besoin de créer manuellement un compte administrateur.

## 🔑 Informations de connexion par défaut

```
Email:        admin@monassurance.com
Mot de passe: D3faultpass
Rôle:         ADMIN
```

> ⚠️ **IMPORTANT**: Changez ce mot de passe dès la première connexion pour des raisons de sécurité !

## 🚀 Utilisation

### 1. Première connexion

Après avoir démarré l'application, vous pouvez vous connecter avec :
- **Email**: `admin@monassurance.com`
- **Mot de passe**: `D3faultpass`

### 2. Changement du mot de passe

#### Via le script utilitaire
```bash
python change_admin_password.py
```

#### Réinitialisation au mot de passe par défaut
```bash
python change_admin_password.py --reset
```

### 3. Test de l'authentification

Pour vérifier que l'utilisateur admin fonctionne :
```bash
python test_admin_auth.py
```

## 📁 Fichiers associés

| Fichier | Description |
|---------|-------------|
| `alembic/versions/993d20339d96_add_default_admin_user.py` | Migration créant l'utilisateur admin |
| `change_admin_password.py` | Script pour changer le mot de passe admin |
| `test_admin_auth.py` | Script de test de l'authentification |

## 🔧 Détails techniques

### Migration automatique

L'utilisateur administrateur est créé automatiquement lors de l'exécution de :
```bash
alembic upgrade head
```

### Hash du mot de passe

Le mot de passe est hashé en utilisant bcrypt via Passlib, garantissant une sécurité optimale.

### Privilèges

L'utilisateur admin a le rôle `ADMIN` qui lui donne accès à toutes les fonctionnalités de l'application :
- Gestion des utilisateurs
- Configuration du système
- Accès aux rapports et métriques
- Administration complète

## 🔒 Sécurité

### Recommandations

1. **Changez le mot de passe immédiatement** après la première connexion
2. **Utilisez un mot de passe fort** (minimum 12 caractères, mélange de majuscules, minuscules, chiffres et symboles)
3. **Activez l'authentification à deux facteurs** si disponible
4. **Surveillez les connexions** de l'utilisateur admin dans les logs

### Suppression

Si vous souhaitez supprimer l'utilisateur admin par défaut :
```bash
alembic downgrade -1
```

> ⚠️ **Attention**: Assurez-vous d'avoir créé un autre utilisateur admin avant de supprimer celui par défaut !

## 🆘 Dépannage

### Utilisateur admin non trouvé

Si l'utilisateur admin n'existe pas :
1. Vérifiez que les migrations ont été appliquées : `alembic current`
2. Appliquez les migrations : `alembic upgrade head`

### Mot de passe oublié

Réinitialisez le mot de passe par défaut :
```bash
python change_admin_password.py --reset
```

### Erreur d'authentification

1. Vérifiez que le serveur backend est démarré
2. Testez avec : `python test_admin_auth.py`
3. Vérifiez les logs du serveur pour plus de détails

## 📈 Monitoring

Les connexions de l'utilisateur admin sont loggées dans les audit logs de l'application. Vous pouvez les consulter via l'interface d'administration ou les endpoints API appropriés.
