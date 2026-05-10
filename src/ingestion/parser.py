"""笔记内容解析和清洗"""

import re


def parse_note_text(raw_text: str) -> dict:
    """解析粘贴的笔记文本，尝试分离标题和正文"""
    text = raw_text.strip()
    if not text:
        return {"title": "", "content": ""}

    lines = text.split("\n")
    first_line = lines[0].strip()

    # 如果第一行看起来像标题（较短且没有标点密集），作为标题
    if len(first_line) <= 50 and first_line:
        title = first_line
        content = "\n".join(lines[1:]).strip()
    else:
        title = first_line[:50]
        content = text

    return {"title": title, "content": content}


def parse_batch_file(file_content: str) -> list[dict]:
    """解析批量导入文件，用 --- 或 === 分隔多篇笔记"""
    notes = re.split(r"\n---+\n|\n===+\n", file_content)
    result = []
    for note_text in notes:
        note_text = note_text.strip()
        if note_text:
            result.append(parse_note_text(note_text))
    return result


def clean_content(text: str) -> str:
    """清洗笔记内容，去除多余空白"""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text
