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
from src.models import Skill, GeneratedNote, Note, Material

MULTI_SKILL_SYSTEM_PROMPT = """你是一个小红书内容创作专家。你的任务是基于多个博主的写作模式，融合他们的风格特点，根据用户提供的素材（文字和图片）和要求，创作一篇高质量的小红书笔记。

你需要融合以下博主的写作风格，取长补短：
- 吸收各博主标题、结构、语气、排版方面的优点
- 自然地融合不同风格，不要生硬拼凑
- 保持小红书平台的社区氛围

创作时请注意：
1. 内容要有真实感和代入感
2. 不要生搬硬套，要自然融入用户提供的素材
3. 如果用户提供了图片，请参考图片内容来创作
4. 输出时直接给出笔记全文，不要加额外说明"""


def _get_multi_skill_context(session, skill_ids: list[str]):
    """获取多个 Skill 的合并写作模式，返回 (combined_patterns_text, reference_notes, blogger_id)."""
    all_patterns = []
    all_refs = []
    blogger_id = ""

    for skill_id in skill_ids:
        skill = session.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            continue
        if skill.status != "ready":
            continue

        if not blogger_id:
            blogger_id = skill.blogger_id

        patterns = json.loads(skill.patterns_json) if skill.patterns_json else {}
        all_patterns.append(f"--- 写作模型: {skill.name} ---\n{patterns_to_text(patterns)}")

        if skill.example_note_ids:
            try:
                example_ids = json.loads(skill.example_note_ids)
                refs = session.query(Note).filter(Note.id.in_(example_ids[:2])).all()
                for n in refs:
                    all_refs.append({"title": n.title, "content": n.content})
            except (json.JSONDecodeError, TypeError):
                pass

    if not all_patterns:
        raise ValueError("没有可用的 Skill")

    combined = "\n\n".join(all_patterns)
    return combined, (all_refs if all_refs else None), blogger_id


def _build_api_messages(
    patterns_text: str,
    user_material: str,
    user_requirements: str,
    reference_notes: list | None,
    images: list[dict] | None,
    multi_skill: bool = False,
) -> list:
    """Build messages for Claude API, supporting multimodal if images present."""
    has_images = images and len(images) > 0
    if has_images:
        content = build_multimodal_message(
            patterns_text, user_material, user_requirements, images, reference_notes
        )
        return [{"role": "user", "content": content}]
    else:
        prompt = build_generation_prompt(
            patterns_text, user_material, user_requirements, reference_notes
        )
        return [{"role": "user", "content": prompt}]


def save_material(
    blogger_id: str,
    skill_id: str,
    material_text: str,
    requirements_text: str,
    file_names: list[str],
    image_count: int,
    generated_note_id: str,
) -> Material:
    """保存一次写作素材到历史记录。"""
    session = get_session()
    m = Material(
        blogger_id=blogger_id,
        skill_id=skill_id,
        material_text=material_text,
        requirements_text=requirements_text,
        file_names_json=json.dumps(file_names, ensure_ascii=False),
        image_count=image_count,
        generated_note_id=generated_note_id,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    session.close()
    return m


def generate_note(
    skill_ids: list[str],
    user_material: str,
    user_requirements: str = "",
    include_references: bool = True,
    images: list[dict] | None = None,
) -> GeneratedNote:
    """根据 Skill 列表生成一篇小红书笔记。支持单/多 Skill 融合。"""
    config = load_config()
    session = get_session()

    patterns_text, reference_notes, blogger_id = _get_multi_skill_context(
        session, skill_ids
    )
    session.close()

    multi = len(skill_ids) > 1
    system_prompt = MULTI_SKILL_SYSTEM_PROMPT if multi else GENERATION_SYSTEM_PROMPT

    client = get_client()
    api_messages = _build_api_messages(
        patterns_text, user_material, user_requirements, reference_notes, images
    )

    generated_text = call_with_retry(
        client,
        "generation",
        model=config["generation"]["model"],
        max_tokens=config["generation"]["max_tokens"],
        temperature=config["generation"].get("temperature", 0.8),
        system=system_prompt,
        messages=api_messages,
    )

    session = get_session()
    gen_note = GeneratedNote(
        skill_id=skill_ids[0],
        user_material=user_material,
        user_requirements=user_requirements,
        generated_content=generated_text,
    )
    session.add(gen_note)
    session.commit()
    session.refresh(gen_note)
    session.close()

    return gen_note


def refine_note(
    skill_ids: list[str],
    current_content: str,
    refinement_instruction: str,
    user_material: str = "",
    user_requirements: str = "",
    images: list[dict] | None = None,
    additional_material: str = "",
    additional_images: list[dict] | None = None,
) -> GeneratedNote:
    """根据用户修改意见 + 可选新素材，迭代优化已生成的笔记。"""
    config = load_config()
    session = get_session()
    patterns_text, reference_notes, _ = _get_multi_skill_context(session, skill_ids)
    session.close()

    multi = len(skill_ids) > 1
    system_prompt = MULTI_SKILL_SYSTEM_PROMPT if multi else GENERATION_SYSTEM_PROMPT

    client = get_client()

    refine_prompt_parts = [
        "你之前按照博主写作模式创作了以下笔记：",
        "",
        "=== 当前笔记内容 ===",
        current_content,
        "",
        "=== 用户修改意见 ===",
        refinement_instruction,
    ]

    if additional_material:
        refine_prompt_parts += [
            "",
            "=== 用户补充的新素材 ===",
            additional_material,
        ]

    refine_prompt_parts += [
        "",
        "请根据修改意见和新素材（如有）重新优化这篇笔记，保持博主写作风格不变。直接输出优化后的完整笔记，不要额外说明。",
    ]

    if user_material:
        refine_prompt_parts.insert(0, f"原始素材: {user_material}\n")
    if user_requirements:
        refine_prompt_parts.insert(0, f"额外要求: {user_requirements}\n")

    refine_text = "\n".join(refine_prompt_parts)

    # 合并所有图片
    all_images = []
    if images:
        all_images.extend(images)
    if additional_images:
        all_images.extend(additional_images)

    if all_images:
        content = [{"type": "text", "text": refine_text}]
        for img in all_images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img["media_type"],
                    "data": img["data"],
                },
            })
        api_messages = [{"role": "user", "content": content}]
    else:
        api_messages = [{"role": "user", "content": refine_text}]

    refined_text = call_with_retry(
        client,
        "generation",
        model=config["generation"]["model"],
        max_tokens=config["generation"]["max_tokens"],
        temperature=config["generation"].get("temperature", 0.8),
        system=system_prompt,
        messages=api_messages,
    )

    session = get_session()
    gen_note = GeneratedNote(
        skill_id=skill_ids[0],
        user_material=f"[REFINE] {refinement_instruction}",
        user_requirements=user_requirements,
        generated_content=refined_text,
    )
    session.add(gen_note)
    session.commit()
    session.refresh(gen_note)
    session.close()

    return gen_note
