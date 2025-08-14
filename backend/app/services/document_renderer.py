from __future__ import annotations

"""Service de rendu de documents multi-format.

Fonctions:
 - render_template: produit un binaire selon le format (html, pdf, xlsx)
 - store_output: persiste le binaire sur disque avec nom déterministe (hash) + métadonnées
"""
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Template as JinjaTemplate
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)

MIME_MAP = {
    "html": "text/html",
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

class RenderResult:
    """Objet simple retourné après stockage du rendu."""

    def __init__(self, file_path: str, mime_type: str, size: int, checksum: str):
        self.file_path = file_path
        self.mime_type = mime_type
        self.size = size
        self.checksum = checksum

def render_template(content: str, context: dict[str, Any] | None, fmt: str) -> bytes:
    """Rend un template Jinja2 ou construit un document selon le format demandé.

    html: rendu direct du template.
    pdf: rendu texte puis conversion basique via reportlab (multi-page).
    xlsx: transformation du contexte en tableau clé/valeur.
    """
    ctx = context or {}
    if fmt == "html":
        template = JinjaTemplate(content)
        return template.render(**ctx).encode("utf-8")
    if fmt == "pdf":
        # Interpréter le content comme texte Jinja2 avant rendu PDF
        template = JinjaTemplate(content)
        rendered_text = template.render(**ctx)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        for line in rendered_text.splitlines() or [rendered_text]:
            c.drawString(40, y, line[:150])
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50
        c.save()
        return buffer.getvalue()
    if fmt == "xlsx":
        # content ignoré si vide: on transforme contexte en table clé/valeur
        wb = Workbook()
        ws = wb.active
        assert ws is not None
        ws.title = "Data"
        if ctx:
            ws.append(["Key", "Value"])
            for k, v in ctx.items():
                ws.append([k, str(v)])
        else:
            ws.append(["Empty"])
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
    # fallback brut
    template = JinjaTemplate(content)
    return template.render(**ctx).encode("utf-8")

def store_output(data: bytes, extension: str) -> RenderResult:
    """Stocke le flux généré sur disque dans OUTPUT_DIR.

    Le nom de fichier incorpore un préfixe du checksum pour éviter doublons.
    """
    checksum = hashlib.sha256(data).hexdigest()
    filename = f"doc_{checksum[:12]}.{extension}"
    path = OUTPUT_DIR / filename
    with open(path, "wb") as f:
        f.write(data)
    mime = MIME_MAP.get(extension, "application/octet-stream")
    return RenderResult(str(path), mime, len(data), checksum)
