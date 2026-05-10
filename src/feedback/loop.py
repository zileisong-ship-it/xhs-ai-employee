"""反馈自成长：评分收集 & Skill 增量优化"""

import json
from datetime import datetime as dt
from src.config import load_config, get_client, call_and_parse_json

from src.database import get_session
from src.models import GeneratedNote, Skill


def submit_feedback(generated_id: str, rating: int, feedback_text: str = ""):
    """提交对生成笔记的评分和反馈"""
    session = get_session()
    gen_note = session.query(GeneratedNote).filter(GeneratedNote.id == generated_id).first()
    if not gen_note:
        session.close()
        raise ValueError("笔记不存在")

    gen_note.rating = rating
    gen_note.feedback_text = feedback_text
    session.commit()
    session.close()


def get_feedback_for_skill(skill_id: str) -> list[dict]:
    """获取某 Skill 的所有带评分反馈"""
    session = get_session()
    gen_notes = (
        session.query(GeneratedNote)
        .filter(
            GeneratedNote.skill_id == skill_id,
            GeneratedNote.rating.isnot(None),
        )
        .order_by(GeneratedNote.created_at.desc())
        .all()
    )
    result = [
        {
            "id": gn.id,
            "rating": gn.rating,
            "feedback": gn.feedback_text,
            "material": gn.user_material,
            "requirements": gn.user_requirements,
            "generated": gn.generated_content[:300],
        }
        for gn in gen_notes
    ]
    session.close()
    return result


def optimize_skill(skill_id: str) -> Skill:
    """基于用户反馈增量优化 Skill"""
    session = get_session()
    skill = session.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        session.close()
        raise ValueError("Skill 不存在")

    feedbacks = get_feedback_for_skill(skill_id)
    rated = [f for f in feedbacks if f["rating"] is not None]

    if len(rated) < 3:
        session.close()
        raise ValueError(f"至少需要 3 条评分反馈才能优化，当前仅有 {len(rated)} 条")

    patterns = json.loads(skill.patterns_json) if skill.patterns_json else {}
    session.close()

    # 构建反馈摘要
    feedback_summary_parts = []
    avg_rating = sum(f["rating"] for f in rated) / len(rated)
    feedback_summary_parts.append(f"平均评分: {avg_rating:.1f}/5")
    feedback_summary_parts.append(f"共 {len(rated)} 条反馈\n")

    for f in rated:
        fb = f["feedback"] if f["feedback"] else "（无文字反馈）"
        feedback_summary_parts.append(
            f"- 评分 {f['rating']}/5 | 素材: {f['material'][:80]}... | 反馈: {fb[:200]}"
        )

    feedback_text = "\n".join(feedback_summary_parts)

    client = get_client()

    optimization_prompt = f"""你是一个小红书写作模式优化专家。

以下是一个博主的当前写作模式 JSON，以及用户对 AI 生成笔记的反馈。

请根据用户反馈，优化写作模式 JSON。如果反馈说生成的内容哪里不好，就调整对应的参数。输出完整的优化后 JSON（保持原结构）。

=== 当前写作模式 ===
{json.dumps(patterns, ensure_ascii=False, indent=2)}

=== 用户反馈 ===
{feedback_text}

请输出优化后的完整 JSON（不要 markdown 代码块标记，只输出纯 JSON）。"""

    config = load_config()
    new_patterns = call_and_parse_json(
        client,
        "analysis",
        model=config["analysis"]["model"],
        max_tokens=config["analysis"]["max_tokens"],
        messages=[{"role": "user", "content": optimization_prompt}],
    )

    session = get_session()
    new_version = (session.query(Skill).filter(Skill.blogger_id == skill.blogger_id).count()) + 1
    old_skill = session.query(Skill).filter(Skill.id == skill_id).first()
    old_skill.status = "outdated"
    old_skill.updated_at = dt.utcnow()

    optimized = Skill(
        blogger_id=skill.blogger_id,
        name=f"{old_skill.blogger.name}·写作模型 v{new_version}",
        version=new_version,
        patterns_json=json.dumps(new_patterns, ensure_ascii=False, indent=2),
        example_note_ids=old_skill.example_note_ids,
        total_notes_used=old_skill.total_notes_used,
        status="ready",
    )
    session.add(optimized)
    session.commit()
    session.refresh(optimized)
    session.close()

    return optimized
