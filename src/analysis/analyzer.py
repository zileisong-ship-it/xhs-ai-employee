"""Claude API 分析引擎"""

import json
from src.config import load_config, get_client, call_and_parse_json
from src.analysis.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_user_prompt
from src.database import get_session
from src.models import Note, Skill, Blogger


def analyze_blogger_notes(blogger_id: str) -> Skill:
    """分析博主的所有笔记，生成写作模式 Skill"""
    config = load_config()
    session = get_session()
    try:
        notes = session.query(Note).filter(Note.blogger_id == blogger_id).all()
        blogger = session.query(Blogger).filter(Blogger.id == blogger_id).first()

        if not notes:
            raise ValueError("该博主没有笔记，请先导入笔记")
        if len(notes) < 3:
            raise ValueError("至少需要 3 篇笔记才能进行分析")

        client = get_client()
        user_prompt = build_analysis_user_prompt(notes)

        patterns = call_and_parse_json(
            client,
            "analysis",
            model=config["analysis"]["model"],
            max_tokens=config["analysis"]["max_tokens"],
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        patterns["meta"] = {
            "analyzed_notes_count": len(notes),
            "high_performing_note_ids": _get_high_performing_note_ids(notes),
        }

        existing_skill = (
            session.query(Skill)
            .filter(Skill.blogger_id == blogger_id)
            .order_by(Skill.version.desc())
            .first()
        )

        new_version = (existing_skill.version + 1) if existing_skill else 1

        skill = Skill(
            blogger_id=blogger_id,
            name=f"{blogger.name}·写作模型 v{new_version}",
            version=new_version,
            patterns_json=json.dumps(patterns, ensure_ascii=False, indent=2),
            example_note_ids=json.dumps([n.id for n in notes], ensure_ascii=False),
            total_notes_used=len(notes),
            status="ready",
        )
        session.add(skill)
        session.commit()
        session.refresh(skill)
        return skill
    finally:
        session.close()


def _get_high_performing_note_ids(notes: list[Note]) -> list[str]:
    """选出指标最高的笔记 ID"""
    scored = []
    for n in notes:
        try:
            metrics = json.loads(n.metrics_json) if n.metrics_json else {}
            score = (
                metrics.get("likes", 0)
                + metrics.get("collects", 0) * 2
                + metrics.get("comments", 0) * 1.5
                + metrics.get("shares", 0) * 3
            )
        except (json.JSONDecodeError, TypeError):
            score = 0
        scored.append((n.id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    top_ids = [s[0] for s in scored[:3] if s[1] > 0]
    return top_ids
