"""首页仪表盘"""

import streamlit as st
from src.database import get_session
from src.models import Blogger, Note, Skill, GeneratedNote


def show():
    st.title("🏠 小红书AI写作分析系统")

    session = get_session()
    blogger_count = session.query(Blogger).count()
    note_count = session.query(Note).count()
    skill_count = session.query(Skill).count()
    gen_count = session.query(GeneratedNote).count()
    session.close()

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 博主", blogger_count)
    col2.metric("📝 笔记", note_count)
    col3.metric("🧠 Skill", skill_count)
    col4.metric("✍️ 生成", gen_count)

    st.markdown("---")

    st.subheader("快速开始")
    st.markdown("""
    1. **添加博主** → 在「博主管理」中创建你要学习的博主
    2. **导入笔记** → 粘贴该博主的笔记内容（至少3篇）
    3. **分析生成 Skill** → 在「AI 分析」中提取写作模式
    4. **生成笔记** → 选择 Skill，输入素材，AI 为你创作
    5. **反馈优化** → 对生成结果打分，让模型越用越好
    """)

    st.subheader("核心工作流")
    cols = st.columns(5)
    steps = [
        ("📥", "导入笔记"),
        ("🔬", "分析模式"),
        ("🧠", "生成Skill"),
        ("✍️", "创作笔记"),
        ("🔄", "反馈优化"),
    ]
    for i, (emoji, label) in enumerate(steps):
        with cols[i]:
            st.markdown(f"#### {emoji}")
            st.caption(label)
    st.caption("导入笔记 → 分析模式 → 生成Skill → 创作笔记 → 反馈优化")
