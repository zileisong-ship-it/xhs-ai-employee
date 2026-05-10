"""小红书AI写作分析系统 - 主入口"""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from src.database import init_db
from pwa_inline import PWA_META
from ui.home import show as show_home
from ui.bloggers import show as show_bloggers
from ui.import_notes import show as show_import
from ui.analysis_page import show as show_analysis
from ui.skills import show as show_skills
from ui.generate import show as show_generate
from ui.history import show as show_history
from ui.materials import show as show_materials


def main():
    st.set_page_config(
        page_title="小红书AI写作分析系统",
        page_icon="📕",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # PWA 支持
    st.markdown(PWA_META, unsafe_allow_html=True)

    # 初始化数据库
    init_db()

    # 侧边栏导航
    st.sidebar.title("📕 导航")
    st.sidebar.markdown("---")

    pages = {
        "🏠 首页仪表盘": show_home,
        "👤 博主管理": show_bloggers,
        "📥 笔记导入": show_import,
        "🔬 AI 分析": show_analysis,
        "🧠 Skill 管理": show_skills,
        "✍️ 生成笔记": show_generate,
        "📊 历史反馈": show_history,
        "📁 素材历史": show_materials,
    }

    page = st.sidebar.radio("选择页面", list(pages.keys()))

    st.sidebar.markdown("---")
    st.sidebar.caption("小红书AI写作分析系统 v1.0")
    st.sidebar.caption("Powered by Claude API")

    # 渲染选中页面
    pages[page]()


if __name__ == "__main__":
    main()
