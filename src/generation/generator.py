"""Claude API 内容生成引擎"""

import json
from src.config import load_config, get_client, call_with_retry

from src.generation.prompts import (
    GENERATION_SYSTEM_PROMPT,
    build_generation_prompt,
    build_multimodal_message,
)
from src.skills.schema import patterns_to_text
from src.database import get_session
from src.models import Skill, GeneratedNote, Note


def generate_note(
    skill_id: str,
    user_material: str,
    user_requirements: str = "",
    include_references: bool = True,
    images: list[dict] | None = None,
) -> GeneratedNote:
    """根据 Skill 生成一篇小红书笔记。images 为 [{'data': 'base64...', 'media_type': 'image/png'}]"""
    config = load_config()
    session = get_session()
    skill = session.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        session.close()
        raise ValueError("Skill 不存在")
    if skill.status != "ready":
        session.close()
        raise ValueError(f"Skill 状态为 {skill.status}，无法使用")

    patterns = json.loads(skill.patterns_json) if skill.patterns_json else {}
    patterns_text = patterns_to_text(patterns)

    reference_notes = None
    if include_references and skill.example_note_ids:
        try:
            example_ids = json.loads(skill.example_note_ids)
            refs = session.query(Note).filter(Note.id.in_(example_ids[:3])).all()
            reference_notes = [
                {"title": n.title, "content": n.content} for n in refs
            ]
        except (json.JSONDecodeError, TypeError):
            pass

    session.close()

    client = get_client()

    has_images = images and len(images) > 0
    if has_images:
        messages_content = build_multimodal_message(
            patterns_text, user_material, user_requirements, images, reference_notes
        )
        api_messages = [{"role": "user", "content": messages_content}]
    else:
        user_prompt = build_generation_prompt(
            patterns_text, user_material, user_requirements, reference_notes
        )
        api_messages = [{"role": "user", "content": user_prompt}]

    generated_text = call_with_retry(
        client,
        "generation",
        model=config["generation"]["model"],
        max_tokens=config["generation"]["max_tokens"],
        temperature=config["generation"].get("temperature", 0.8),
        system=GENERATION_SYSTEM_PROMPT,
        messages=api_messages,
    )

    session = get_session()
    gen_note = GeneratedNote(
        skill_id=skill_id,
        user_material=user_material,
        user_requirements=user_requirements,
        generated_content=generated_text,
    )
    session.add(gen_note)
    session.commit()
    session.refresh(gen_note)
    session.close()

    return gen_note
