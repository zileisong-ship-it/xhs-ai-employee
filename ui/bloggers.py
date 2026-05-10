"""博主管理页面"""

import streamlit as st
from datetime import datetime
from src.database import get_session
from src.models import Blogger


def show():
    st.title("👤 博主管理")

    # 创建博主
    with st.expander("➕ 添加新博主", expanded=False):
        name = st.text_input("博主名称")
        description = st.text_area("博主简介（领域/风格描述）")
        if st.button("创建博主", type="primary"):
            if name.strip():
                session = get_session()
                existing = session.query(Blogger).filter(Blogger.name == name.strip()).first()
                if existing:
                    st.error("该博主已存在")
                else:
                    blogger = Blogger(name=name.strip(), description=description.strip())
                    session.add(blogger)
                    session.commit()
                    st.success(f"博主「{name}」创建成功！")
                session.close()
            else:
                st.error("请输入博主名称")

    # 博主列表
    st.subheader("已添加博主")
    session = get_session()
    bloggers = session.query(Blogger).order_by(Blogger.created_at.desc()).all()

    if not bloggers:
        st.info("还没有添加博主")
        session.close()
        return

    for blogger in bloggers:
        note_count = len(blogger.notes)
        skill_count = len(blogger.skills)
        with st.expander(f"{blogger.name} — {note_count}篇笔记, {skill_count}个Skill"):
            st.text(f"简介: {blogger.description or '无'}")
            st.text(f"创建时间: {blogger.created_at.strftime('%Y-%m-%d %H:%M')}")

            # 修改
            new_desc = st.text_area(
                "更新简介", blogger.description or "",
                key=f"desc_{blogger.id}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("更新", key=f"upd_{blogger.id}"):
                    blogger.description = new_desc
                    blogger.updated_at = datetime.utcnow()
                    session.commit()
                    st.success("已更新")
            with col2:
                if st.button("删除博主", key=f"del_{blogger.id}", type="secondary"):
                    if note_count == 0:
                        session.delete(blogger)
                        session.commit()
                        st.success(f"博主「{blogger.name}」已删除")
                        st.rerun()
                    else:
                        st.error(f"该博主有 {note_count} 篇笔记，请先删除笔记")

    session.close()
