"""内容生成页面 — 支持实时交互式修改和素材补充"""

import streamlit as st
from src.skills.manager import get_all_skills
from src.generation.generator import generate_note, refine_note, save_material
from src.generation.file_parser import parse_uploaded_file
from src.database import get_session
from src.models import Skill, GeneratedNote


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

    # ===== 初始化 session state =====
    defaults = {
        "chat_history": [],         # [{role, content, type}]
        "current_result": "",
        "current_result_id": "",
        "has_generated": False,
        "base_material": "",
        "base_requirements": "",
        "base_images": [],
        "base_file_names": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ===== 上半部分：Skill 选择 & 初始素材 =====
    skill_options = {s.name: s.id for s in ready_skills}
    selected_names = st.multiselect(
        "选择写作模型（可多选融合）",
        list(skill_options.keys()),
        placeholder="选择一个或多个 Skill...",
    )
    if not selected_names:
        st.info("请至少选择一个写作模型")
        return

    skill_ids = [skill_options[name] for name in selected_names]

    session = get_session()
    first_skill = session.query(Skill).filter(Skill.id == skill_ids[0]).first()
    blogger_id = first_skill.blogger_id if first_skill else ""
    session.close()

    if len(skill_ids) > 1:
        st.caption(f"已选 {len(skill_ids)} 个 Skill，AI 将融合它们的风格")

    # 初始素材（仅在未生成时显示完整表单）
    if not st.session_state.has_generated:
        st.subheader("初始写作素材与要求")

        tab1, tab2 = st.tabs(["✏️ 文本录入", "📎 文件上传"])

        with tab1:
            user_material_text = st.text_area(
                "写作素材（产品信息、话题、核心要点等）",
                height=200,
                placeholder="输入你想写的内容素材...",
                key="init_material_text",
            )

        with tab2:
            uploaded_files = st.file_uploader(
                "上传文件（Word / Excel / 图片 / TXT）",
                type=["docx", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "avi", "mkv", "webm"],
                accept_multiple_files=True,
                key="init_files",
            )
            _show_file_preview(uploaded_files)

        user_requirements = st.text_area(
            "额外要求（可选）",
            height=100,
            placeholder="例如：控制字数在500字以内、强调性价比...",
            key="init_requirements",
        )

        if st.button("🚀 生成笔记", type="primary", use_container_width=True):
            material, file_names, images = _collect_material(
                user_material_text, uploaded_files
            )
            requirements = user_requirements.strip()

            if not material and not images:
                st.error("请至少输入一些写作素材或上传文件/图片")
            else:
                with st.spinner("AI 正在按照博主风格创作中..."):
                    try:
                        gen_note = generate_note(
                            skill_ids=skill_ids,
                            user_material=material,
                            user_requirements=requirements,
                            images=images if images else None,
                        )

                        # 保存状态
                        st.session_state.current_result = gen_note.generated_content
                        st.session_state.current_result_id = gen_note.id
                        st.session_state.has_generated = True
                        st.session_state.base_material = material
                        st.session_state.base_requirements = requirements
                        st.session_state.base_images = images
                        st.session_state.base_file_names = file_names
                        st.session_state.chat_history = [
                            {"role": "user", "content": _truncate(material, 200), "type": "material"},
                            {"role": "assistant", "content": gen_note.generated_content, "type": "result"},
                        ]

                        save_material(
                            blogger_id=blogger_id,
                            skill_id=skill_ids[0],
                            material_text=material,
                            requirements_text=requirements,
                            file_names=file_names,
                            image_count=len(images),
                            generated_note_id=gen_note.id,
                        )

                        st.success("生成完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成失败: {e}")

    # ===== 下半部分：交互式对话面板 =====
    else:
        st.divider()
        st.subheader("📝 协作编辑")

        # 左侧：对话 + 结果，右侧：上下文
        left, right = st.columns([3, 1])

        with right:
            st.caption("**当前 Skill**")
            for name in selected_names:
                st.caption(f"• {name}")
            if st.session_state.base_requirements:
                with st.expander("📋 原始要求"):
                    st.text(st.session_state.base_requirements)
            if st.session_state.base_material:
                with st.expander("📄 原始素材"):
                    st.text(st.session_state.base_material[:500])
            if st.button("🔄 重新开始", use_container_width=True):
                for k in defaults:
                    st.session_state[k] = defaults[k]
                st.rerun()

        with left:
            # 显示对话历史
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        label = "初始素材" if msg["type"] == "material" else "反馈"
                        st.caption(f"📤 {label}")
                        st.text(msg["content"][:300])
                else:
                    with st.chat_message("assistant"):
                        st.caption("🤖 AI 生成")
                        st.text(msg["content"][:500])
                        if len(msg["content"]) > 500:
                            st.caption("...（下方查看完整内容）")

            st.divider()

            # 当前结果 — 始终可编辑
            st.caption("**当前结果（可直接修改）**")
            edited = st.text_area(
                "笔记内容",
                st.session_state.current_result,
                height=350,
                key="live_result",
                label_visibility="collapsed",
            )

            # 手动保存
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 保存手动修改", use_container_width=True):
                    st.session_state.current_result = edited
                    _update_db_result(st.session_state.current_result_id, edited)
                    st.success("已保存！")
                    st.rerun()
            with c2:
                st.caption(f"对话轮次: {len(st.session_state.chat_history) // 2}")
            with c3:
                if st.button("📋 复制", use_container_width=True):
                    st.info("选中文本框 Ctrl+C 复制")

            st.divider()

            # 反馈输入区
            st.caption("**💬 输入反馈让 AI 调整（可选附带新素材）**")

            feedback = st.text_area(
                "修改意见",
                height=70,
                placeholder="例如：标题不够抓人、语气太正式了、结尾加个引导评论的话...",
                key="chat_feedback",
                label_visibility="collapsed",
            )

            # 附加新素材
            with st.expander("📎 附加新素材（可选）"):
                extra_text = st.text_area(
                    "补充文字素材",
                    height=100,
                    placeholder="粘贴新的产品信息、数据、使用感受等...",
                    key="extra_material_text",
                )
                extra_files = st.file_uploader(
                    "补充文件 / 图片",
                    type=["docx", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "avi", "mkv", "webm"],
                    accept_multiple_files=True,
                    key="extra_files",
                )
                _show_file_preview(extra_files)

            if st.button("📨 发送给 AI 修改", type="primary", use_container_width=True):
                if not feedback.strip() and not extra_text.strip() and not extra_files:
                    st.error("请输入修改意见或补充素材")
                else:
                    with st.spinner("AI 正在优化..."):
                        try:
                            # 收集额外素材
                            extra_material_text, _, extra_images = _collect_material(
                                extra_text, extra_files
                            )

                            # 保存当前编辑内容
                            st.session_state.current_result = edited

                            refined = refine_note(
                                skill_ids=skill_ids,
                                current_content=st.session_state.current_result,
                                refinement_instruction=feedback.strip() or "请根据新素材优化内容",
                                user_material=st.session_state.base_material,
                                user_requirements=st.session_state.base_requirements,
                                images=st.session_state.base_images if st.session_state.base_images else None,
                                additional_material=extra_material_text if extra_material_text else "",
                                additional_images=extra_images if extra_images else None,
                            )

                            # 更新状态
                            st.session_state.current_result = refined.generated_content
                            st.session_state.current_result_id = refined.id

                            # 构建反馈消息
                            feedback_msg = feedback.strip()
                            if extra_material_text:
                                feedback_msg += f"\n[附加素材: {_truncate(extra_material_text, 150)}]"

                            st.session_state.chat_history.append({
                                "role": "user", "content": feedback_msg, "type": "feedback",
                            })
                            st.session_state.chat_history.append({
                                "role": "assistant", "content": refined.generated_content, "type": "result",
                            })

                            st.success("AI 已根据反馈调整！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"修改失败: {e}")


def _collect_material(text: str, files: list) -> tuple[str, list[str], list[dict]]:
    """从文本和文件列表收集：素材文字、文件名、图片列表。"""
    parts = []
    file_names = []
    images = []

    if text and text.strip():
        parts.append(text.strip())

    if files:
        for uf in files:
            parsed = parse_uploaded_file(uf.read(), uf.name)
            if parsed["text"]:
                parts.append(f"[{uf.name}]\n{parsed['text']}")
            if parsed["images"]:
                images.extend(parsed["images"])
            file_names.append(uf.name)

    return "\n\n".join(parts), file_names, images


def _show_file_preview(files):
    """显示上传文件的预览。"""
    if not files:
        return
    for uf in files:
        parsed = parse_uploaded_file(uf.read(), uf.name)
        img_count = len(parsed["images"])
        text_len = len(parsed["text"])
        info = f"📎 {uf.name}"
        if text_len:
            info += f" — {text_len} 字"
        if img_count:
            info += f" — 📷 {img_count} 张图"
        st.caption(info)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _update_db_result(gen_id: str, new_content: str):
    session = get_session()
    gn = session.query(GeneratedNote).filter(GeneratedNote.id == gen_id).first()
    if gn:
        gn.generated_content = new_content
        session.commit()
    session.close()
