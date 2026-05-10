"""笔记导入页面"""

import json
import streamlit as st
from src.database import get_session
from src.models import Blogger
from src.ingestion.importer import (
    import_single_note,
    import_batch_notes,
    get_notes_by_blogger,
    delete_note,
)


def show():
    st.title("📥 笔记导入")

    session = get_session()
    bloggers = session.query(Blogger).order_by(Blogger.name).all()
    session.close()

    if not bloggers:
        st.warning("还没有博主，请先去「博主管理」页创建")
        return

    blogger_options = {b.name: b.id for b in bloggers}
    selected_name = st.selectbox("选择博主", list(blogger_options.keys()))
    blogger_id = blogger_options[selected_name]

    tab1, tab2, tab3 = st.tabs(["粘贴导入", "批量文件导入", "已导入笔记"])

    with tab1:
        st.subheader("手动粘贴笔记")
        raw_text = st.text_area(
            "粘贴笔记全文（第一行自动作为标题）",
            height=300,
            placeholder="在这里粘贴小红书笔记的完整内容...",
        )
        source_url = st.text_input("原文链接（可选）")
        st.caption("附带图片/视频（可选，AI 分析时会参考视觉内容）")
        media_uploads = st.file_uploader(
            "上传图片或视频",
            type=["png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "avi", "mkv", "webm"],
            accept_multiple_files=True,
            key="note_media",
        )
        if st.button("导入笔记", type="primary"):
            if raw_text.strip():
                media_tuples = [(uf.read(), uf.name) for uf in media_uploads] if media_uploads else None
                note = import_single_note(blogger_id, raw_text, source_url, media_files=media_tuples)
                if media_uploads:
                    st.success(f"导入成功！笔记「{note.title}」+ {len(media_uploads)} 个附件已保存")
                else:
                    st.success(f"导入成功！笔记「{note.title}」已保存")
            else:
                st.error("请粘贴笔记内容")

    with tab2:
        st.subheader("批量导入")
        st.caption("上传 .txt 文件，用 `---` 或 `===` 分隔多篇笔记")
        uploaded_file = st.file_uploader("选择文件", type=["txt"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            st.text_area("文件预览", content, height=200, disabled=True)
            if st.button("批量导入", type="primary"):
                notes = import_batch_notes(blogger_id, content)
                st.success(f"成功导入 {len(notes)} 篇笔记")

    with tab3:
        st.subheader("已导入笔记")
        notes = get_notes_by_blogger(blogger_id)
        if not notes:
            st.info("该博主还没有导入笔记")
        else:
            for note in notes:
                attach_info = ""
                try:
                    atts = json.loads(note.attachments_json) if note.attachments_json else []
                    if atts:
                        types = set(a.get("type", "file") for a in atts)
                        parts = []
                        if "image" in types: parts.append("📷图片")
                        if "video" in types: parts.append("🎬视频")
                        attach_info = " + " + " ".join(parts)
                except (json.JSONDecodeError, TypeError):
                    pass

                with st.expander(f"{note.title or '(无标题)'}{attach_info} — {note.imported_at.strftime('%Y-%m-%d %H:%M')}"):
                    st.text(note.content[:500])
                    if st.button("删除", key=f"del_{note.id}"):
                        delete_note(note.id)
                        st.rerun()
