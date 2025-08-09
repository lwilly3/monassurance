#!/usr/bin/env python
"""Script utilitaire de gestion (maintenance & tâches récurrentes).

Objectif
========
Centraliser des commandes de **qualité**, **tests**, et **maintenance sécurité** afin
de simplifier l'usage local et future intégration CI/CD.

Usage
=====
    python manage.py <commande> [options]

Commandes disponibles
=====================
lint
    1. Exécute **ruff** en mode auto-fix (format + lint).
    2. Lance **mypy** en typage strict sur `backend/app`.
test
    Exécute la suite Pytest en mode silencieux (`-q`).
testcov
    Exécute Pytest avec rapport de couverture (affiche lignes manquantes).
rotate-keys <kid>
    Génére un nouveau matériel de clé pseudo-aléatoire pour les URLs signées.
    N'écrit rien dans les settings automatiquement: l'opérateur met à jour `.env`.
show-settings
    Charge les settings Pydantic effectifs (après `.env`) et les affiche (debug).

Exemples
========
    python manage.py lint
    python manage.py rotate-keys k2

Remarques
=========
- Aucune dépendance externe autre que l'environnement Python courant.
- Le script privilégie la simplicité (pas de click/typer) pour rester léger.
- Les sorties sont orientées pipeline CI (codes retour explicites).
"""
from __future__ import annotations
import os
import sys
import base64
import secrets
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd: list[str]) -> int:
    """Exécute une commande subprocess et retourne le code retour.

    Ne capture pas la sortie (stream direct) pour transparence dans CI.
    """
    return subprocess.call(cmd)


def cmd_lint() -> int:
    """Lance ruff (auto-fix) puis mypy.

    Convention: échec immédiat si ruff échoue (évite compilation mypy inutile).
    Retourne le premier code de sortie non nul rencontré.
    """
    code = run([sys.executable, "-m", "ruff", "check", "--fix", "."])  # type: ignore[list-item]
    if code != 0:
        return code
    return run([sys.executable, "-m", "mypy", "backend/app"])  # type: ignore[list-item]


def cmd_test() -> int:
    """Exécute la suite de tests en mode silencieux.

    Utilisé pour feedback rapide local ou étape CI.
    """
    return run([sys.executable, "-m", "pytest", "-q"])  # type: ignore[list-item]


def cmd_testcov() -> int:
    """Exécute tests avec couverture affichant lignes manquantes.

    Idéal pour gate de qualité (> seuil défini dans pipeline).
    """
    return run([
        sys.executable,
        "-m",
        "pytest",
        "--cov=backend/app",
        "--cov-report=term-missing",
        "-q",
    ])  # type: ignore[list-item]


def cmd_rotate_keys(new_kid: str | None) -> int:
        """Génère du matériel de clé pour un nouveau *kid*.

        Étapes post-exécution (manuel):
            1. Ajouter variable hiérarchique dans `.env` (format SIGNATURE_KEYS__<kid>=clé)
            2. Mettre à jour SIGNATURE_ACTIVE_KID
            3. Redéployer (rolling update) – conserver anciennes clés jusqu'à expiration liens existants.
        """
        if not new_kid:
                print("Spécifier un identifiant de clé: python manage.py rotate-keys k2", file=sys.stderr)
                return 1
        raw = secrets.token_urlsafe(32)
        # Normaliser en 32 bytes base64 urlsafe (compatible dérivations HMAC/Fernet)
        key_material = base64.urlsafe_b64encode(raw.encode())[:32].decode()
        print(f"Nouvelle clé (kid={new_kid}) -> {key_material}")
        print("Étapes:")
        print(f"1. Ajouter dans .env: SIGNATURE_KEYS__{new_kid}={key_material}")
        print(f"2. Mettre à jour SIGNATURE_ACTIVE_KID={new_kid}")
        print("3. Redéployer")
        return 0


def cmd_show_settings() -> int:
    """Affiche le dictionnaire des settings chargés.

    Utile pour diagnostiquer lecture `.env` / variables environnements en CI.
    """
    from backend.app.core.config import get_settings  # lazy import pour démarrage rapide

    s = get_settings()
    print(s.model_dump())
    return 0


COMMANDS = {
    "lint": lambda args: cmd_lint(),
    "test": lambda args: cmd_test(),
    "testcov": lambda args: cmd_testcov(),
    "rotate-keys": lambda args: cmd_rotate_keys(args[0] if args else None),
    "show-settings": lambda args: cmd_show_settings(),
}


def main() -> int:
    """Point d'entrée CLI.

    Parse la commande, exécute la fonction correspondante et propage le code retour.
    """
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Commande inconnue: {cmd}", file=sys.stderr)
        return 1
    return COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
