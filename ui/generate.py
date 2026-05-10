"""内容生成页面"""

import streamlit as st
from src.skills.manager import get_all_skills
from src.generation.generator import generate_note
from src.generation.file_parser import parse_uploaded_file


def show():
    st.title("✍️ 生成笔记")

    skills = get_all_skills()
    ready_skills = [s for s in skills if s.status == "ready"]

    if not ready_skills:
        st.warning("还没有可用的 Skill。请先分析博主笔记生成 Skill")
        if not skills:
            st.info("整个系统还没有任何 Skill，请从「笔记导入」和「AI 分析」开始")
        else:
            st.info(f"当前有 {len(skills)} 个 Skill，但状态都不是 ready")
        return

    skill_options = {s.name: s.id for s in ready_skills}
    selected_name = st.selectbox("选择写作模型", list(skill_options.keys()))
    skill_id = skill_options[selected_name]

    st.subheader("写作素材与要求")

    tab1, tab2 = st.tabs(["✏️ 文本录入", "📎 文件上传"])

    with tab1:
        user_material_text = st.text_area(
            "写作素材（产品信息、话题、核心要点等）",
            height=200,
            placeholder="输入你想写的内容素材，例如：\n- 产品：某品牌面霜\n- 核心卖点：保湿、不油腻、适合敏感肌\n- 使用感受：...",
            key="material_text",
        )

    with tab2:
        uploaded_files = st.file_uploader(
            "上传文件（支持 Word / Excel / 图片 / TXT）",
            type=["docx", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "gif", "webp"],
            accept_multiple_files=True,
            key="material_files",
        )

        file_text_parts = []
        file_images = []

        if uploaded_files:
            for uf in uploaded_files:
                parsed = parse_uploaded_file(uf.read(), uf.name)
                if parsed["text"]:
                    file_text_parts.append(f"--- 文件: {uf.name} ---\n{parsed['text']}")
                if parsed["images"]:
                    file_images.extend(parsed["images"])
                    st.caption(f"📷 {uf.name}: 提取到 {len(parsed['images'])} 张图片")

            if file_text_parts:
                st.text_area(
                    "提取的文件内容（可编辑）",
                    "\n\n".join(file_text_parts),
                    height=200,
                    key="file_text_preview",
                )

            if file_images:
                st.caption(f"共 {len(file_images)} 张图片将传给 AI 作为参考")
        else:
            st.caption("上传 Word、Excel、TXT 文件提取文字，或直接上传图片")

    user_requirements = st.text_area(
        "额外要求（可选）",
        height=100,
        placeholder="例如：\n- 控制字数在500字以内\n- 强调性价比\n- 加入使用前后对比\n- 语气更活泼一些",
    )

    # 聚合素材
    all_material_parts = []
    if user_material_text.strip():
        all_material_parts.append(user_material_text.strip())
    if uploaded_files:
        for uf in uploaded_files:
            parsed = parse_uploaded_file(uf.read(), uf.name)
            if parsed["text"]:
                all_material_parts.append(f"[{uf.name}]\n{parsed['text']}")

    # 收集所有图片
    all_images = []
    if uploaded_files:
        for uf in uploaded_files:
            parsed = parse_uploaded_file(uf.read(), uf.name)
            if parsed["images"]:
                all_images.extend(parsed["images"])

    combined_material = "\n\n".join(all_material_parts)

    if st.button("🚀 生成笔记", type="primary", use_container_width=True):
        if not combined_material.strip() and not all_images:
            st.error("请至少输入一些写作素材或上传文件/图片")
        else:
            with st.spinner("AI 正在按照博主风格创作中..."):
                try:
                    gen_note = generate_note(
                        skill_id=skill_id,
                        user_material=combined_material,
                        user_requirements=user_requirements,
                        images=all_images if all_images else None,
                    )
                    st.session_state["last_generated_id"] = gen_note.id
                    st.session_state["last_generated_content"] = gen_note.generated_content
                    st.success("生成完成！")
                except Exception as e:
                    st.error(f"生成失败: {e}")

    if "last_generated_content" in st.session_state:
        st.divider()
        st.subheader("📄 生成结果")
        st.text_area(
            "笔记内容（可复制）",
            st.session_state.last_generated_content,
            height=400,
            key="result_display",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 复制到剪贴板"):
                st.info("请选中上方文本框内容后 Ctrl+C 复制")
        with col2:
            st.caption("在侧边栏选择「📊 历史反馈」进行评分")
