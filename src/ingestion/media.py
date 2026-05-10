"""Media file handling, video frame extraction, and MCP-ready content fetching."""

import base64
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Protocol

from src.generation.file_parser import parse_uploaded_file

# ============================================================
# Media storage
# ============================================================

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "media")


def save_media_files(files: list[tuple[bytes, str]]) -> list[dict]:
    """Save uploaded media files to disk. Returns list of attachment metadata dicts."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    attachments = []
    for file_bytes, filename in files:
        file_id = str(uuid.uuid4())[:8]
        ext = Path(filename).suffix
        saved_name = f"{file_id}{ext}"
        saved_path = os.path.join(MEDIA_DIR, saved_name)
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
        attachments.append({
            "id": file_id,
            "original_name": filename,
            "saved_path": saved_path,
            "type": _media_type(ext),
        })
    return attachments


def load_attachments_as_images(attachments_json: str) -> list[dict]:
    """Load saved attachments and convert to Claude-compatible image list."""
    try:
        attachments = json.loads(attachments_json) if attachments_json else []
    except (json.JSONDecodeError, TypeError):
        return []

    images = []
    for att in attachments:
        path = att.get("saved_path", "")
        if not path or not os.path.exists(path):
            continue
        media_type = att.get("type", "")
        if media_type in ("image", "video_frame"):
            with open(path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode("utf-8")
            mime = _mime_for_ext(Path(path).suffix)
            images.append({"data": b64, "media_type": mime})
        elif media_type == "video":
            # Extract frames from saved video
            with open(path, "rb") as f:
                video_bytes = f.read()
            parsed = parse_uploaded_file(video_bytes, att.get("original_name", "video.mp4"))
            images.extend(parsed.get("images", []))
    return images


def _media_type(ext: str) -> str:
    ext = ext.lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return "image"
    elif ext in (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"):
        return "video"
    return "file"


def _mime_for_ext(ext: str) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext.lower(), "image/jpeg")


# ============================================================
# MCP-ready content fetching abstraction
# ============================================================

class ContentFetcher(Protocol):
    """Protocol for fetching external content (MCP or other integrations).

    When an MCP tool becomes available (e.g., reading 小红书 notes directly),
    implement this protocol and set it as the active fetcher via set_fetcher().
    """

    def fetch_note(self, url: str) -> dict:
        """Fetch a note from a URL. Returns {'title': str, 'content': str, 'images': [...], 'metrics': {...}}."""
        ...

    def fetch_blogger_notes(self, blogger_url: str, max_notes: int = 50) -> list[dict]:
        """Fetch all notes from a blogger. Returns list of note dicts."""
        ...


_active_fetcher: ContentFetcher | None = None


def set_fetcher(fetcher: ContentFetcher):
    """Register an MCP or custom content fetcher."""
    global _active_fetcher
    _active_fetcher = fetcher


def get_fetcher() -> ContentFetcher | None:
    """Get the currently active content fetcher, if any."""
    return _active_fetcher


def is_fetcher_available() -> bool:
    return _active_fetcher is not None


def auto_fetch_note(url: str) -> dict | None:
    """Try to fetch a note via registered fetcher. Returns None if unavailable."""
    if _active_fetcher is None:
        return None
    return _active_fetcher.fetch_note(url)


def auto_fetch_blogger(url: str, max_notes: int = 50) -> list[dict] | None:
    """Try to fetch all notes of a blogger via registered fetcher."""
    if _active_fetcher is None:
        return None
    return _active_fetcher.fetch_blogger_notes(url, max_notes)
