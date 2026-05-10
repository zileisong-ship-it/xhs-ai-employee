"""Parse uploaded files into text and image data for the generation pipeline."""

import base64
import io
from pathlib import Path

from docx import Document
from openpyxl import load_workbook


def parse_uploaded_file(file_bytes: bytes, filename: str) -> dict:
    """Parse an uploaded file, returning {'type': 'text'|'image', 'text': str, 'images': list}."""
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        return _parse_docx(file_bytes)
    elif ext in (".xlsx", ".xls"):
        return _parse_xlsx(file_bytes)
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return _parse_image(file_bytes, ext)
    elif ext == ".txt":
        return {"type": "text", "text": file_bytes.decode("utf-8"), "images": []}
    else:
        return {"type": "text", "text": "", "images": []}


def _parse_docx(file_bytes: bytes) -> dict:
    doc = Document(io.BytesIO(file_bytes))

    # Extract text paragraphs
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)

    # Extract images embedded in the document
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                image_data = rel.target_part.blob
                ext = Path(rel.target_part.partname).suffix.lower()
                mime = _mime_type(ext)
                b64 = base64.b64encode(image_data).decode("utf-8")
                images.append({"data": b64, "media_type": mime})
            except Exception:
                pass

    return {"type": "text", "text": text, "images": images}


def _parse_xlsx(file_bytes: bytes) -> dict:
    wb = load_workbook(io.BytesIO(file_bytes), read_only=True)
    parts = []
    for name in wb.sheetnames:
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        parts.append(f"--- Sheet: {name} ---")
        for row in rows:
            cells = [str(c) if c is not None else "" for c in row]
            parts.append(" | ".join(cells))
    wb.close()
    return {"type": "text", "text": "\n".join(parts), "images": []}


def _parse_image(file_bytes: bytes, ext: str) -> dict:
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return {
        "type": "image",
        "text": "",
        "images": [{"data": b64, "media_type": _mime_type(ext)}],
    }


def _mime_type(ext: str) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")
