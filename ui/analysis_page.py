"""AI 分析页面"""

import streamlit as st
import json
from src.database import get_session
from src.models import Blogger, Skill
from src.analysis.analyzer import analyze_blogger_notes
from src.ingestion.importer import get_note_count


def show():
    st.title("🔬 AI 分析 - 提取写作模式")

    session = get_session()
    bloggers = session.query(Blogger).order_by(Blogger.name).all()
    session.close()

    if not bloggers:
        st.warning("还没有博主，请先去「博主管理」页创建")
        return

    blogger_options = {b.name: b.id for b in bloggers}
    selected_name = st.selectbox("选择要分析的博主", list(blogger_options.keys()))
    blogger_id = blogger_options[selected_name]

    note_count = get_note_count(blogger_id)
    st.metric("该博主笔记数", note_count)

    if note_count < 3:
        st.warning("至少需要 3 篇笔记才能进行分析，请先导入更多笔记")
        return

    # 检查是否已有 Skill
    session = get_session()
    latest_skill = (
        session.query(Skill)
        .filter(Skill.blogger_id == blogger_id)
        .order_by(Skill.version.desc())
        .first()
    )
    session.close()

    if latest_skill:
        st.info(f"该博主已有 Skill: {latest_skill.name}（状态: {latest_skill.status}）")
        st.caption("重新分析将创建新版本，旧版本会保留")

    st.markdown("---")

    if st.button("🚀 开始分析", type="primary", use_container_width=True):
        with st.spinner(f"AI 正在分析 {selected_name} 的所有笔记..."):
            try:
                skill = analyze_blogger_notes(blogger_id)
                st.success(f"分析完成！Skill「{skill.name}」已生成")
                st.balloons()

                # 展示结果摘要
                patterns = json.loads(skill.patterns_json)
                st.subheader("分析结果总览")

                tone = patterns.get("tone", {})
                title = patterns.get("title", {})
                structure = patterns.get("structure", {})

                col1, col2, col3 = st.columns(3)
                col1.metric("口吻", tone.get("voice", "?"))
                col2.metric("正式度", f"{tone.get('formality', '?')}/5")
                col3.metric("篇幅", structure.get("avg_total_length", "?"))

                st.write(f"**标题套路:** {', '.join(title.get('patterns', []))}")
                st.write(f"**内容主题:** {', '.join(patterns.get('content_themes', []))}")
                st.write(f"**爆款触发:** {', '.join(patterns.get('viral_factors', {}).get('common_triggers', []))}")

                with st.expander("查看完整 JSON"):
                    st.code(skill.patterns_json, language="json")

            except Exception as e:
                st.error(f"分析失败: {e}")
