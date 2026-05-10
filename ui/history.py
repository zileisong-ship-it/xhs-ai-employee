"""历史记录 & 反馈页面"""

import streamlit as st
from src.database import get_session
from src.models import GeneratedNote, Skill
from src.feedback.loop import submit_feedback, get_feedback_for_skill, optimize_skill


def show():
    st.title("📊 历史记录 & 反馈")

    session = get_session()
    gen_notes = (
        session.query(GeneratedNote)
        .order_by(GeneratedNote.created_at.desc())
        .all()
    )
    session.close()

    if not gen_notes:
        st.info("还没有生成过笔记")
        return

    tab1, tab2 = st.tabs(["历史记录", "反馈优化"])

    with tab1:
        st.subheader("生成历史")
        for gn in gen_notes:
            # 获取 skill 名称
            session = get_session()
            skill = session.query(Skill).filter(Skill.id == gn.skill_id).first()
            skill_name = skill.name if skill else "未知模型"
            session.close()

            with st.expander(
                f"[{gn.created_at.strftime('%m/%d %H:%M')}] "
                f"模型: {skill_name} | "
                f"素材: {gn.user_material[:50]}..."
            ):
                st.text_area(
                    "生成内容",
                    gn.generated_content,
                    height=200,
                    disabled=True,
                    key=f"content_{gn.id}",
                )

                # 反馈区
                if gn.rating is None:
                    st.write("**给这篇笔记打分:**")
                    rating = st.slider("评分", 1, 5, 3, key=f"rate_{gn.id}")
                    feedback = st.text_area(
                        "反馈意见（哪里好/哪里需要改进）",
                        key=f"fb_{gn.id}",
                        placeholder="例如：标题不够抓人、语气太正式了...",
                    )
                    if st.button("提交反馈", key=f"sub_{gn.id}", type="primary"):
                        submit_feedback(gn.id, rating, feedback)
                        st.success("反馈已提交！")
                        st.rerun()
                else:
                    st.write(f"⭐ 评分: {gn.rating}/5")
                    if gn.feedback_text:
                        st.write(f"💬 反馈: {gn.feedback_text}")

    with tab2:
        st.subheader("Skill 增量优化")
        st.caption("当成生的笔记积累足够评分反馈后，可以基于反馈优化 Skill")

        session = get_session()
        skills = session.query(Skill).filter(Skill.status == "ready").all()
        session.close()

        if not skills:
            st.info("没有可优化的 Skill")
            return

        skill_options = {s.name: s.id for s in skills}
        selected_name = st.selectbox(
            "选择要优化的 Skill",
            list(skill_options.keys()),
            key="optimize_skill_select",
        )
        skill_id = skill_options[selected_name]

        feedbacks = get_feedback_for_skill(skill_id)
        rated_count = len([f for f in feedbacks if f["rating"] is not None])

        st.metric("可用的评分反馈数", rated_count)

        if rated_count > 0:
            st.write("**反馈摘要:**")
            for f in feedbacks[:10]:
                stars = "⭐" * f["rating"] if f["rating"] else "??"
                fb = f["feedback"][:150] if f["feedback"] else "（无文字）"
                st.write(f"{stars} | {fb}")

        if st.button("🔄 基于反馈优化 Skill",
                     type="primary",
                     disabled=(rated_count < 3)):
            with st.spinner("正在优化 Skill..."):
                try:
                    new_skill = optimize_skill(skill_id)
                    st.success(
                        f"优化完成！新版本: {new_skill.name}，"
                        f"旧版本已标记为 outdated"
                    )
                except Exception as e:
                    st.error(f"优化失败: {e}")

        if rated_count < 3:
            st.caption("至少需要 3 条评分反馈才能触发优化")
