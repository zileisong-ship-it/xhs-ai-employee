# 📕 小红书AI写作分析系统

基于 Claude API 的小红书博主写作风格分析与 AI 内容生成助手。

> **当前为主**：本地运行（Streamlit 网页 + 桌面窗口 + Docker 三种方式），云部署方案已保留在 `deploy_guide.md`。

---

## 功能模块

| 模块 | 说明 |
|------|------|
| 🏠 首页仪表盘 | 博主/笔记/Skill/生成数全局概览 |
| 👤 博主管理 | 添加和管理分析的博主 |
| 📥 笔记导入 | 粘贴/文件上传/图片/视频附件导入 |
| 🔬 AI 分析 | 基于 ≥3 篇笔记提取写作模式，生成结构化 Skill（支持多模态） |
| 🧠 Skill 管理 | 查看、对比、导出写作模式（版本化，不覆盖旧版） |
| ✍️ 生成笔记 | 单/多 Skill 融合，上传素材（文本/Word/Excel/图片/视频），生成小红书笔记 |
| 📊 历史反馈 | 评分 + 文字反馈，累积 ≥3 条触发 Skill 自动优化 |
| 📁 素材历史 | 按博主浏览历史上传素材 |

---

## 快速开始

### 1. 环境要求
- Python 3.10+
- Claude API Key（[获取](https://console.anthropic.com/)）

### 2. 安装

```bash
git clone git@github.com:zileisong-ship-it/xhs-ai-employee.git
cd xhs-ai-employee
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
# 创建 .env 文件
echo ANTHROPIC_API_KEY=sk-你的key > .env
```

### 4. 启动

```bash
# 方式1: 网页版
streamlit run app.py

# 方式2: 桌面原生窗口
python desktop_app.py

# 方式3: Docker
docker compose up -d
```

浏览器访问 `http://localhost:8501`。

---

## 使用流程

```
添加博主 → 导入笔记（≥3篇）→ AI 分析生成 Skill
                                    ↓
           选择 Skill → 输入素材+要求 → 生成笔记
                                    ↓
       不满意？→ 聊天式交互修改（可追加素材）
                                    ↓
               满意 → 评分反馈 → 优化 Skill
```

---

## 项目结构

```
├── app.py              # Streamlit 入口
├── config.yaml         # 应用配置
├── desktop_app.py      # 桌面原生窗口
├── Dockerfile          # Docker 容器化
├── docker-compose.yml  # 本地 Docker 测试
├── CLAUDE.md           # AI Agent 手册（给代码助手看的完整项目文档）
├── deploy_guide.md     # 云端部署指南
├── src/                # 核心代码
│   ├── config.py       # 配置 + Claude 客户端
│   ├── database.py     # 数据库引擎
│   ├── models.py       # 5个数据模型
│   ├── analysis/       # AI 分析引擎
│   ├── generation/     # 内容生成引擎 + 文件解析
│   ├── ingestion/      # 笔记导入 + 媒体存储 + MCP 抽象
│   ├── skills/         # Skill 管理
│   └── feedback/       # 反馈自成长
├── ui/                 # 8 个 Streamlit 页面
└── android-app/        # Android WebView 项目
```

---

## 技术栈

- **UI**: Streamlit
- **AI**: Claude API (Sonnet 4.6)
- **数据库**: SQLite + SQLAlchemy（支持 PostgreSQL 切换）
- **文件解析**: python-docx, openpyxl, OpenCV
- **桌面**: pywebview
- **容器**: Docker

---

## 给 AI Agent 的说明

如果你是 AI 编程助手，请先阅读 `CLAUDE.md`，它包含完整的架构说明、数据库设计、工作流程和关键设计决策。
