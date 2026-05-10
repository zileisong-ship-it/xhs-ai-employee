"""AI 分析用的 Prompt 模板"""

ANALYSIS_SYSTEM_PROMPT = """你是一个专业的小红书内容分析专家。你的任务是根据多个笔记样本，提取博主的写作模式。

你需要分析以下维度并输出严格的 JSON（不要有任何额外文字）：

1. **title** (标题模式): 分析标题的常见套路、平均长度、高频关键词
2. **structure** (内容结构): 笔记的典型段落划分、平均总长度、段落风格
3. **tone** (语气人设): 博主的口吻、正式度(1-5)、常用人称代词
4. **hooks** (开头结尾): 开头的抓人技巧、结尾的互动/收尾方式
5. **formatting** (排版习惯): emoji 使用密度和位置、hashtag 数量范围、是否用编号列表、是否用加粗
6. **vocabulary** (词汇特征): 标志性口头禅、高频热词、应避免的词
7. **content_themes** (内容主题): 常写的主题领域
8. **viral_factors** (爆款因素): 高分笔记的共性触发点、互动模式

请输出以下 JSON 结构（不要markdown代码块标记，只输出纯JSON）：
{
  "title": {"patterns": [], "avg_length": 0, "common_keywords": []},
  "structure": {"sections": [], "avg_total_length": "", "paragraph_style": ""},
  "tone": {"voice": "", "formality": 0, "pronouns": ""},
  "hooks": {"opening": [], "closing": []},
  "formatting": {"emoji_density": "", "emoji_position": "", "hashtag_count_range": [0,0], "uses_numbered_list": false, "uses_bold": false},
  "vocabulary": {"signature_phrases": [], "buzzwords": [], "avoid_words": []},
  "content_themes": [],
  "viral_factors": {"common_triggers": [], "interaction_patterns": []}
}
"""


def build_analysis_user_prompt(notes: list) -> str:
    """根据笔记列表构建分析用的 user prompt"""
    notes_text_parts = []
    for i, note in enumerate(notes, 1):
        metrics_str = ""
        if note.metrics_json and note.metrics_json != "{}":
            import json
            try:
                metrics = json.loads(note.metrics_json)
                likes = metrics.get("likes", 0)
                metrics_str = f" | 数据: {likes}赞"
            except (json.JSONDecodeError, KeyError):
                pass

        notes_text_parts.append(
            f"--- 笔记 {i}{metrics_str} ---\n"
            f"标题: {note.title}\n"
            f"正文:\n{note.content}\n"
        )

    notes_text = "\n".join(notes_text_parts)

    return f"""请分析以下 {len(notes)} 篇小红书笔记，提取该博主的完整写作模式。

{notes_text}

请严格按照要求的 JSON 格式输出分析结果。"""


def build_multimodal_analysis_message(text_prompt: str, images: list[dict]) -> list[dict]:
    """构建带图片的多模态分析消息。images 为 [{'data': 'base64...', 'media_type': 'image/...'}]"""
    content = [{"type": "text", "text": text_prompt}]
    for img in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["media_type"],
                "data": img["data"],
            },
        })
    return content
