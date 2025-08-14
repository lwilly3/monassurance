#!/usr/bin/env python3
"""Script de gestion Celery pour MonAssurance.

Commandes disponibles:
- worker: Démarre un worker Celery
- beat: Démarre le scheduler Celery Beat
- flower: Démarre l'interface web Flower
- purge: Purge toutes les queues
- status: Affiche le statut des workers
"""
import subprocess
import sys


def run_celery_worker(args: list[str]) -> None:
    """Démarre un worker Celery."""
    queue = args[0] if args else "celery,reports,documents,notifications"
    concurrency = args[1] if len(args) > 1 else "2"
    
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "worker",
        "--loglevel=info",
        f"--queues={queue}",
        f"--concurrency={concurrency}",
        "--prefetch-multiplier=1"
    ]
    
    print(f"Démarrage worker Celery - Queue: {queue}, Concurrency: {concurrency}")
    subprocess.run(cmd)  # noqa: S603


def run_celery_beat(args: list[str]) -> None:
    """Démarre le scheduler Celery Beat."""
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "beat",
        "--loglevel=info"
    ]
    
    print("Démarrage Celery Beat (scheduler)")
    subprocess.run(cmd)  # noqa: S603


def run_flower(args: list[str]) -> None:
    """Démarre l'interface web Flower."""
    port = args[0] if args else "5555"
    
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "flower",
        f"--port={port}"
    ]
    
    print(f"Démarrage Flower sur http://localhost:{port}")
    subprocess.run(cmd)  # noqa: S603


def purge_queues(args: list[str]) -> None:
    """Purge toutes les queues Celery."""
    confirm = input("Êtes-vous sûr de vouloir purger toutes les queues ? (y/N): ")
    if confirm.lower() != 'y':
        print("Annulé")
        return
    
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "purge",
        "-f"  # force
    ]
    
    print("Purge des queues Celery...")
    subprocess.run(cmd)  # noqa: S603


def show_status(args: list[str]) -> None:
    """Affiche le statut des workers Celery."""
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "status"
    ]
    
    print("Statut des workers Celery:")
    subprocess.run(cmd)  # noqa: S603


def show_stats(args: list[str]) -> None:
    """Affiche les statistiques détaillées."""
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "inspect", "stats"
    ]
    
    print("Statistiques des workers:")
    subprocess.run(cmd)  # noqa: S603


def show_active_tasks(args: list[str]) -> None:
    """Affiche les tâches actives."""
    cmd = [
        "celery", "-A", "backend.app.core.celery_app:celery_app",
        "inspect", "active"
    ]
    
    print("Tâches actives:")
    subprocess.run(cmd)  # noqa: S603


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print("Usage: python celery_manager.py <command> [args...]")
        print("\nCommandes disponibles:")
        print("  worker [queue] [concurrency]  - Démarre un worker")
        print("  beat                          - Démarre le scheduler")
        print("  flower [port]                 - Démarre l'interface web")
        print("  purge                         - Purge toutes les queues")
        print("  status                        - Statut des workers")
        print("  stats                         - Statistiques détaillées")
        print("  active                        - Tâches actives")
        print("\nExemples:")
        print("  python celery_manager.py worker reports 4")
        print("  python celery_manager.py flower 5556")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        "worker": run_celery_worker,
        "beat": run_celery_beat,
        "flower": run_flower,
        "purge": purge_queues,
        "status": show_status,
        "stats": show_stats,
        "active": show_active_tasks,
    }
    
    if command not in commands:
        print(f"Commande inconnue: {command}")
        print(f"Commandes disponibles: {', '.join(commands.keys())}")
        sys.exit(1)
    
    try:
        commands[command](args)
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
