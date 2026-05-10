"""Skill JSON Schema 定义和校验"""

import json

SKILL_SCHEMA_TEMPLATE = {
    "title": {"patterns": [], "avg_length": 0, "common_keywords": []},
    "structure": {"sections": [], "avg_total_length": "", "paragraph_style": ""},
    "tone": {"voice": "", "formality": 0, "pronouns": ""},
    "hooks": {"opening": [], "closing": []},
    "formatting": {
        "emoji_density": "",
        "emoji_position": "",
        "hashtag_count_range": [0, 0],
        "uses_numbered_list": False,
        "uses_bold": False,
    },
    "vocabulary": {"signature_phrases": [], "buzzwords": [], "avoid_words": []},
    "content_themes": [],
    "viral_factors": {"common_triggers": [], "interaction_patterns": []},
    "meta": {"analyzed_notes_count": 0, "high_performing_note_ids": []},
}


def get_empty_patterns() -> dict:
    """返回空的 patterns 模板"""
    return json.loads(json.dumps(SKILL_SCHEMA_TEMPLATE))


def validate_patterns(patterns: dict) -> bool:
    """校验 patterns 是否包含必要字段"""
    required_top = [
        "title", "structure", "tone", "hooks",
        "formatting", "vocabulary", "content_themes", "viral_factors"
    ]
    for key in required_top:
        if key not in patterns:
            return False
    return True


def patterns_to_text(patterns: dict) -> str:
    """将 patterns JSON 转为可读文本，用于构建 prompt"""
    p = patterns
    lines = [
        "【标题模式】",
        f"  常见套路: {', '.join(p['title']['patterns'])}",
        f"  平均长度: {p['title']['avg_length']}字",
        f"  高频词: {', '.join(p['title']['common_keywords'])}",
        "",
        "【内容结构】",
        f"  典型段落: {' → '.join(p['structure']['sections'])}",
        f"  平均总长度: {p['structure']['avg_total_length']}",
        f"  段落风格: {p['structure']['paragraph_style']}",
        "",
        "【语气人设】",
        f"  口吻: {p['tone']['voice']}",
        f"  正式度(1-5): {p['tone']['formality']}",
        f"  常用人称: {p['tone']['pronouns']}",
        "",
        "【开头结尾技巧】",
        f"  开头: {', '.join(p['hooks']['opening'])}",
        f"  结尾: {', '.join(p['hooks']['closing'])}",
        "",
        "【排版习惯】",
        f"  Emoji密度: {p['formatting']['emoji_density']}",
        f"  Emoji位置: {p['formatting']['emoji_position']}",
        f"  Hashtag数量: {p['formatting']['hashtag_count_range'][0]}-{p['formatting']['hashtag_count_range'][1]}个",
        f"  使用编号列表: {p['formatting']['uses_numbered_list']}",
        f"  使用加粗: {p['formatting']['uses_bold']}",
        "",
        "【词汇特征】",
        f"  标志性口头禅: {', '.join(p['vocabulary']['signature_phrases'])}",
        f"  高频热词: {', '.join(p['vocabulary']['buzzwords'])}",
        f"  避免使用: {', '.join(p['vocabulary']['avoid_words'])}",
        "",
        "【内容主题】",
        f"  {', '.join(p['content_themes'])}",
        "",
        "【爆款因素】",
        f"  触发点: {', '.join(p['viral_factors']['common_triggers'])}",
        f"  互动模式: {', '.join(p['viral_factors']['interaction_patterns'])}",
    ]
    return "\n".join(lines)
