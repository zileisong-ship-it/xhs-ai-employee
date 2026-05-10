"""Skill 管理：CRUD、版本管理、导入导出"""

import json
import os
import yaml
from datetime import datetime
from src.database import get_session
from src.models import Skill, Blogger
from src.skills.schema import validate_patterns


def get_all_skills() -> list[Skill]:
    """获取所有 Skill 列表"""
    session = get_session()
    skills = session.query(Skill).order_by(Skill.updated_at.desc()).all()
    session.close()
    return skills


def get_skill(skill_id: str) -> Skill | None:
    """获取单个 Skill"""
    session = get_session()
    skill = session.query(Skill).filter(Skill.id == skill_id).first()
    session.close()
    return skill


def get_latest_skill_for_blogger(blogger_id: str) -> Skill | None:
    """获取博主的最新版 Skill"""
    session = get_session()
    skill = (
        session.query(Skill)
        .filter(Skill.blogger_id == blogger_id)
        .order_by(Skill.version.desc())
        .first()
    )
    session.close()
    return skill


def get_skill_versions(blogger_id: str) -> list[Skill]:
    """获取某博主的所有 Skill 版本"""
    session = get_session()
    skills = (
        session.query(Skill)
        .filter(Skill.blogger_id == blogger_id)
        .order_by(Skill.version.desc())
        .all()
    )
    session.close()
    return skills


def delete_skill(skill_id: str):
    """删除一个 Skill"""
    session = get_session()
    session.query(Skill).filter(Skill.id == skill_id).delete()
    session.commit()
    session.close()


def export_skill_to_file(skill_id: str) -> str:
    """导出 Skill 为 JSON 文件，返回文件路径"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    export_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        config["skills"]["export_dir"],
    )
    os.makedirs(export_dir, exist_ok=True)

    skill = get_skill(skill)
    if not skill:
        raise ValueError("Skill 不存在")

    export_data = {
        "name": skill.name,
        "version": skill.version,
        "blogger_name": skill.blogger.name if skill.blogger else "",
        "patterns": json.loads(skill.patterns_json),
        "total_notes_used": skill.total_notes_used,
        "exported_at": datetime.utcnow().isoformat(),
    }

    filename = f"{skill.blogger.name if skill.blogger else 'unknown'}_v{skill.version}.json"
    filepath = os.path.join(export_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return filepath


def import_skill_from_file(filepath: str, blogger_id: str) -> Skill:
    """从 JSON 文件导入 Skill"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    patterns = data.get("patterns", {})
    if not validate_patterns(patterns):
        raise ValueError("Skill 文件格式不正确，缺少必要字段")

    session = get_session()
    skill = Skill(
        blogger_id=blogger_id,
        name=data.get("name", "Imported Skill"),
        version=1,
        patterns_json=json.dumps(patterns, ensure_ascii=False, indent=2),
        total_notes_used=data.get("total_notes_used", 0),
        status="ready",
    )
    session.add(skill)
    session.commit()
    session.refresh(skill)
    session.close()
    return skill
