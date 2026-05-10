"""笔记导入逻辑"""

import json
from datetime import datetime
from src.database import get_session
from src.models import Blogger, Note
from src.ingestion.parser import parse_note_text, parse_batch_file, clean_content


def import_single_note(
    blogger_id: str,
    raw_text: str,
    source_url: str = "",
    metrics: dict | None = None,
    published_at: str | None = None,
) -> Note:
    """导入单篇笔记"""
    session = get_session()
    parsed = parse_note_text(raw_text)
    note = Note(
        blogger_id=blogger_id,
        title=parsed["title"],
        content=clean_content(parsed["content"]),
        source_url=source_url,
        metrics_json=json.dumps(metrics or {}, ensure_ascii=False),
        published_at=datetime.fromisoformat(published_at) if published_at else None,
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    session.close()
    return note


def import_batch_notes(
    blogger_id: str, file_content: str
) -> list[Note]:
    """批量导入笔记（从文本文件）"""
    session = get_session()
    parsed_notes = parse_batch_file(file_content)
    notes = []
    for pn in parsed_notes:
        note = Note(
            blogger_id=blogger_id,
            title=pn["title"],
            content=clean_content(pn["content"]),
        )
        session.add(note)
        notes.append(note)
    session.commit()
    for n in notes:
        session.refresh(n)
    session.close()
    return notes


def get_notes_by_blogger(blogger_id: str) -> list[Note]:
    """获取某博主的所有笔记"""
    session = get_session()
    notes = (
        session.query(Note)
        .filter(Note.blogger_id == blogger_id)
        .order_by(Note.imported_at.desc())
        .all()
    )
    session.close()
    return notes


def delete_note(note_id: str):
    """删除单篇笔记"""
    session = get_session()
    session.query(Note).filter(Note.id == note_id).delete()
    session.commit()
    session.close()


def get_note_count(blogger_id: str) -> int:
    """获取某博主的笔记数量"""
    session = get_session()
    count = session.query(Note).filter(Note.blogger_id == blogger_id).count()
    session.close()
    return count
