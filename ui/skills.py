"""Skill 管理页面"""

import streamlit as st
import json
from src.skills.manager import (
    get_all_skills,
    get_skill,
    get_skill_versions,
    delete_skill,
    export_skill_to_file,
)
from src.database import get_session
from src.models import Blogger


def show():
    st.title("🧠 Skill 管理（写作模型）")

    # 从数据库取数据
    skills = get_all_skills()

    if not skills:
        st.info("还没有任何 Skill。请先导入博主笔记，然后在「AI 分析」页分析生成 Skill")
        return

    # 按博主分组
    session = get_session()
    skill_blogger_map = {}
    for s in skills:
        blogger = session.query(Blogger).filter(Blogger.id == s.blogger_id).first()
        blogger_name = blogger.name if blogger else "未知博主"
        if blogger_name not in skill_blogger_map:
            skill_blogger_map[blogger_name] = []
        skill_blogger_map[blogger_name].append(s)
    session.close()

    selected_blogger = st.selectbox("按博主筛选", ["全部"] + list(skill_blogger_map.keys()))

    if selected_blogger != "全部":
        display_skills = skill_blogger_map.get(selected_blogger, [])
    else:
        display_skills = skills

    for skill in display_skills:
        blogger_name = ""
        for bn, sl in skill_blogger_map.items():
            if skill in sl:
                blogger_name = bn
                break

        patterns = json.loads(skill.patterns_json) if skill.patterns_json else {}

        with st.expander(
            f"{skill.name} — {skill.status} — "
            f"{skill.updated_at.strftime('%Y-%m-%d %H:%M') if skill.updated_at else ''}"
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("版本", f"v{skill.version}")
            col2.metric("分析笔记数", skill.total_notes_used)
            col3.metric("状态", skill.status)

            if patterns:
                tab1, tab2 = st.tabs(["写作模式概览", "原始 JSON"])
                with tab1:
                    _render_patterns_summary(patterns)
                with tab2:
                    st.code(skill.patterns_json, language="json")

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("导出 JSON", key=f"exp_{skill.id}"):
                    try:
                        path = export_skill_to_file(skill.id)
                        st.success(f"已导出到 {path}")
                    except Exception as e:
                        st.error(str(e))
            with c2:
                if st.button("查看历史版本", key=f"ver_{skill.id}"):
                    versions = get_skill_versions(skill.blogger_id)
                    st.write(f"共 {len(versions)} 个版本")
                    for v in versions:
                        st.write(f"  v{v.version} — {v.status} — {v.updated_at.strftime('%Y-%m-%d')}")
            with c3:
                if st.button("删除", key=f"del_{skill.id}", type="secondary"):
                    delete_skill(skill.id)
                    st.rerun()


def _render_patterns_summary(patterns: dict):
    """渲染写作模式摘要"""
    title = patterns.get("title", {})
    structure = patterns.get("structure", {})
    tone = patterns.get("tone", {})
    hooks = patterns.get("hooks", {})
    formatting = patterns.get("formatting", {})
    vocab = patterns.get("vocabulary", {})
    themes = patterns.get("content_themes", [])
    viral = patterns.get("viral_factors", {})

    st.write("**📝 标题模式**")
    st.write(f"套路: {', '.join(title.get('patterns', []))}")
    st.write(f"平均{title.get('avg_length', '?')}字, 高频词: {', '.join(title.get('common_keywords', []))}")

    st.write("**📐 内容结构**")
    st.write(f"段落: {' → '.join(structure.get('sections', []))}")
    st.write(f"篇幅: {structure.get('avg_total_length', '?')}, 风格: {structure.get('paragraph_style', '?')}")

    st.write("**🎭 语气人设**")
    st.write(f"{tone.get('voice', '?')}, 正式度: {tone.get('formality', '?')}/5, 人称: {tone.get('pronouns', '?')}")

    st.write("**🎣 开头/结尾**")
    st.write(f"开头: {', '.join(hooks.get('opening', []))}")
    st.write(f"结尾: {', '.join(hooks.get('closing', []))}")

    st.write("**🎨 排版**")
    st.write(f"Emoji: {formatting.get('emoji_density', '?')}({formatting.get('emoji_position', '?')})")
    st.write(f"Hashtag: {formatting.get('hashtag_count_range', [0,0])}个")
    st.write(f"编号列表: {formatting.get('uses_numbered_list', False)}, 加粗: {formatting.get('uses_bold', False)}")

    st.write("**💬 词汇**")
    st.write(f"口头禅: {', '.join(vocab.get('signature_phrases', []))}")
    st.write(f"热词: {', '.join(vocab.get('buzzwords', []))}")

    st.write("**📂 主题**: " + ", ".join(themes))
    st.write(f"**🔥 爆款触发**: {', '.join(viral.get('common_triggers', []))}")
