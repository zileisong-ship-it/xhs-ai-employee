"""素材历史记录页面"""

import json
import streamlit as st
from src.database import get_session
from src.models import Material, Blogger, GeneratedNote


def show():
    st.title("📁 素材历史")

    session = get_session()
    materials = (
        session.query(Material)
        .order_by(Material.created_at.desc())
        .all()
    )

    if not materials:
        st.info("还没有上传过素材。去「生成笔记」页面创作后，素材会自动保存到这里。")
        session.close()
        return

    # 按博主分组
    blogger_map = {}
    for m in materials:
        blogger = session.query(Blogger).filter(Blogger.id == m.blogger_id).first()
        blogger_name = blogger.name if blogger else "未知博主"
        if blogger_name not in blogger_map:
            blogger_map[blogger_name] = []
        blogger_map[blogger_name].append(m)

    session.close()

    st.caption(f"共 {len(materials)} 条素材记录，来自 {len(blogger_map)} 位博主")

    # 按博主目录展示
    for blogger_name, items in blogger_map.items():
        with st.expander(f"📂 {blogger_name} — {len(items)} 条素材"):
            for i, m in enumerate(items):
                file_names = json.loads(m.file_names_json) if m.file_names_json else []
                files_label = ", ".join(file_names) if file_names else "纯文本录入"
                imgs_label = f", {m.image_count}张图" if m.image_count > 0 else ""

                with st.expander(
                    f"📄 {m.created_at.strftime('%m/%d %H:%M')} — {files_label}{imgs_label}"
                ):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if m.material_text:
                            st.text_area(
                                "写作素材",
                                m.material_text,
                                height=200,
                                disabled=True,
                                key=f"mat_{m.id}",
                            )
                        if m.requirements_text:
                            st.text_area(
                                "额外要求",
                                m.requirements_text,
                                height=80,
                                disabled=True,
                                key=f"req_{m.id}",
                            )
                    with col2:
                        st.caption(f"时间: {m.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.caption(f"文件: {len(file_names)} 个")
                        st.caption(f"图片: {m.image_count} 张")

                        if m.generated_note_id:
                            session = get_session()
                            gn = session.query(GeneratedNote).filter(
                                GeneratedNote.id == m.generated_note_id
                            ).first()
                            session.close()
                            if gn:
                                with st.expander("👁 查看生成结果"):
                                    st.text_area(
                                        "生成的笔记",
                                        gn.generated_content,
                                        height=300,
                                        disabled=True,
                                        key=f"gn_{m.id}",
                                    )
                                    if gn.rating:
                                        st.write(f"⭐ 评分: {gn.rating}/5")
                                    if gn.feedback_text:
                                        st.write(f"💬 反馈: {gn.feedback_text}")

                    st.divider()
