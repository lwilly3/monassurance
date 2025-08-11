from __future__ import annotations

"""Service de stockage des templates (fichiers) côté backend.

Fournit des helpers pour:
 - Enregistrer un fichier de template de manière sûre dans un répertoire dédié
 - Charger le contenu texte (UTF-8) d'un template (depuis DB ou fichier)
 - Calculer le checksum SHA-256
"""
import hashlib
from pathlib import Path

TEMPLATES_DIR = Path("templates_store")
TEMPLATES_DIR.mkdir(exist_ok=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_ext(filename: str | None, content_type: str | None) -> str:
    """Détermine une extension sûre pour stockage.

    Autorise .html et .txt par défaut. Utilise le content-type pour fallback.
    """
    allowed = {".html", ".txt"}
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in allowed:
            return ext
    if content_type == "text/html":
        return ".html"
    return ".txt"


def store_template_bytes(data: bytes, filename: str | None = None, content_type: str | None = None) -> str:
    """Stocke les octets d'un template dans le répertoire dédié et renvoie le chemin.

    Le nom contient un préfixe du checksum + extension sûre.
    """
    checksum = sha256_hex(data)
    ext = _safe_ext(filename, content_type)
    safe_name = f"tpl_{checksum[:12]}{ext}"
    path = TEMPLATES_DIR / safe_name
    with open(path, "wb") as f:
        f.write(data)
    return str(path)


def read_template_text_from_file(path: str) -> str:
    p = Path(path)
    # Vérifie confinement dans TEMPLATES_DIR
    try:
        if not p.resolve().is_relative_to(TEMPLATES_DIR.resolve()):
            raise ValueError("Chemin hors répertoire autorisé")
    except AttributeError:
        root = str(TEMPLATES_DIR.resolve())
        if not str(p.resolve()).startswith(root):
            raise ValueError("Chemin hors répertoire autorisé")
    data = p.read_bytes()
    # On tente UTF-8 strict; si échec -> erreur explicite
    return data.decode("utf-8")
