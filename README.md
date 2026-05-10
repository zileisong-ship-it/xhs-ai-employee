# 📕 小红书AI写作分析系统

基于 Claude API 的小红书博主写作风格分析与内容生成工具。导入博主笔记 → AI 拆解写作模式 → 生成同风格内容 → 反馈自优化，形成完整的 AI 辅助写作闭环。

## 功能概览

| 模块 | 说明 |
|------|------|
| 🏠 首页仪表盘 | 博主数、笔记数、Skill 数、生成笔记数等全局概览 |
| 👤 博主管理 | 添加和管理要分析的博主 |
| 📥 笔记导入 | 支持单篇粘贴导入或批量文本文件导入 |
| 🔬 AI 分析 | 基于博主的笔记（≥3篇）提取写作模式，生成 Skill（标题偏好、开头套路、正文结构、结尾风格等） |
| 🧠 Skill 管理 | 查看、对比、导出写作模式模型 |
| ✍️ 生成笔记 | 输入素材和要求，根据 Skill 生成符合博主风格的小红书笔记 |
| 📊 历史反馈 | 对生成笔记评分反馈，累积 ≥3 条后可触发 Skill 增量优化 |

## 技术栈

- **前端界面**: [Streamlit](https://streamlit.io/)
- **AI 引擎**: [Claude API](https://docs.anthropic.com/) (Sonnet 4.6)
- **数据库**: SQLite + SQLAlchemy ORM
- **配置**: YAML + 环境变量

## 快速开始

### 1. 环境要求

- Python 3.10+
- Anthropic API Key（[获取地址](https://console.anthropic.com/)）

### 2. 安装

```bash
git clone git@github.com:zileisong-ship-it/xhs-ai-employee.git
cd xhs-ai-employee
pip install -r requirements.txt
```

### 3. 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

`.env` 内容：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 4. 启动

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`。

## 使用流程

```
添加博主 → 导入笔记 → AI 分析生成 Skill → 输入素材生成笔记 → 评分反馈 → 优化 Skill
```

一次典型的使用路径：

1. **新建博主** — 在「博主管理」中添加
2. **导入笔记** — 将博主的历史笔记粘贴导入（支持标题+正文自动解析）
3. **AI 分析** — 选择博主，Claude 自动拆解写作风格，生成结构化 Skill
4. **生成笔记** — 输入你的素材和需求，AI 模拟博主风格生成小红书文案
5. **反馈优化** — 对生成结果打分（1-5），累积反馈后可触发模型增量优化

## 项目结构

```
xhs-ai-employee/
├── app.py                  # Streamlit 主入口
├── config.yaml             # 应用配置（模型、参数等）
├── requirements.txt        # Python 依赖
├── src/
│   ├── models.py           # 数据模型（Blogger, Note, Skill, GeneratedNote）
│   ├── database.py         # SQLite 初始化和连接
│   ├── config.py           # 配置加载 & Claude 客户端工具
│   ├── analysis/           # AI 分析引擎
│   │   ├── analyzer.py     # 笔记 → 写作模式提取
│   │   └── prompts.py      # 分析 Prompt
│   ├── generation/         # 内容生成引擎
│   │   ├── generator.py    # 基于 Skill 生成笔记
│   │   └── prompts.py      # 生成 Prompt
│   ├── ingestion/          # 笔记导入
│   │   ├── importer.py     # 导入逻辑
│   │   └── parser.py       # 文本解析
│   ├── feedback/           # 反馈自成长
│   │   └── loop.py         # 评分收集 & Skill 优化
│   └── skills/             # Skill 管理
│       ├── manager.py      # Skill CRUD & 导出
│       └── schema.py       # Skill 数据结构
└── ui/                     # Streamlit 页面
    ├── home.py             # 首页仪表盘
    ├── bloggers.py         # 博主管理
    ├── import_notes.py     # 笔记导入
    ├── analysis_page.py    # AI 分析
    ├── skills.py           # Skill 管理
    ├── generate.py         # 生成笔记
    └── history.py          # 历史反馈
```

## License

MIT
