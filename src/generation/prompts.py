"""内容生成 Prompt 模板"""

GENERATION_SYSTEM_PROMPT = """你是一个小红书内容创作专家。你的任务是基于指定博主的写作模式，根据用户提供的素材（文字和图片）和要求，创作一篇高质量的小红书笔记。

你需要严格遵循以下写作模式来创作：
- 标题风格要和博主一致
- 内容结构要模仿博主的典型段落划分
- 语气、人设、口吻要贴合博主
- 开头和结尾要用博主的常见技巧
- 排版习惯（emoji、hashtag、段落长度等）要一致
- 适当使用博主的标志性词汇和口头禅

创作时请注意：
1. 内容要有真实感和代入感
2. 不要生搬硬套，要自然融入用户提供的素材
3. 如果用户提供了图片，请参考图片内容来创作
4. 保持小红书平台的社区氛围
5. 输出时直接给出笔记全文，不要加额外说明"""


def build_generation_prompt(
    patterns_text: str,
    user_material: str,
    user_requirements: str,
    reference_notes: list | None = None,
) -> str:
    """构建生成笔记的文本 prompt（无图片时使用）。"""
    parts = [
        "请按照以下博主的写作模式，根据我的素材创作一篇小红书笔记。",
        "",
        "=== 博主的写作模式 ===",
        patterns_text,
        "",
        "=== 我的写作素材 ===",
        user_material or "（用户未提供素材，请根据写作模式自由发挥）",
        "",
        "=== 额外要求 ===",
        user_requirements or "无额外要求",
    ]

    if reference_notes:
        parts.append("")
        parts.append("=== 参考笔记（风格参照用）===")
        for i, ref in enumerate(reference_notes, 1):
            parts.append(f"\n--- 参考笔记 {i} ---")
            parts.append(f"标题: {ref.get('title', '')}")
            parts.append(f"正文:\n{ref.get('content', '')[:500]}")
            if len(ref.get('content', '')) > 500:
                parts.append("...(截断)")

    return "\n".join(parts)


def build_multimodal_message(
    patterns_text: str,
    user_material: str,
    user_requirements: str,
    images: list[dict],
    reference_notes: list | None = None,
) -> list[dict]:
    """构建带图片的多模态消息内容。"""
    text_prompt = build_generation_prompt(
        patterns_text, user_material, user_requirements, reference_notes
    )

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
