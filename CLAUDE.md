# 小红书AI写作分析系统 — AI Agent 项目手册

> 本文档面向未来的 AI 编程助手（以及人类协作者）。阅读本文档后，你应该完全理解项目的架构、技术栈、数据模型、工作流程和关键设计决策。

---

## 1. 项目概览

**一句话**：基于 Claude API 的小红书博主写作风格分析与内容生成工具，支持电脑桌面版 + 手机 APP + 网页版三端使用。

**核心能力**：
- 导入小红书博主的历史笔记（文本粘贴 / 文件上传 / 图片 / 视频 / 未来 MCP 自动抓取）
- AI 分析博主的写作模式（标题、结构、语气、排版、词汇等），生成结构化 "Skill"
- 基于单个或多个 Skill 融合生成新笔记
- 交互式聊天反馈优化生成内容（可追加素材）
- 收集用户评分反馈，累积 ≥3 条后自动优化 Skill（版本化不覆盖旧版）

**运行模式**：
| 模式 | 描述 | 入口 |
|------|------|------|
| 本地开发 | `streamlit run app.py` | http://localhost:8501 |
| 桌面版 | pywebview 原生窗口包裹本地 Streamlit | `python desktop_app.py` |
| Docker | 容器化运行 | `docker build -t xhs-ai . && docker run -p 8501:8501` |
| 云端 | Streamlit Cloud 或阿里云 SAE | 自动从 GitHub 部署 |

---

## 2. 技术栈

| 层 | 技术 | 版本要求 |
|----|------|----------|
| **UI** | Streamlit | >=1.28.0 |
| **AI** | Anthropic Claude API (`claude-sonnet-4-6`) | >=0.30.0 |
| **ORM** | SQLAlchemy | >=2.0.0 |
| **数据库** | SQLite（本地）/ PostgreSQL（云端可选） | — |
| **配置** | YAML + 环境变量 + Streamlit Secrets | pyyaml>=6.0 |
| **文件解析** | python-docx, openpyxl, OpenCV | 见 requirements.txt |
| **桌面** | pywebview (仅 desktop_app.py) | >=6.0 |
| **容器** | Docker (python:3.12-slim) | — |
| **移动** | Android WebView 包装 APK | — |

---

## 3. 项目文件结构（全量）

```
小红书AI员工/
├── app.py                          # Streamlit 主入口，8 个页面路由
├── config.yaml                     # 本地应用配置（模型、超时、重试）
├── .env                            # 环境变量（ANTHROPIC_API_KEY），不入 git
├── .env.example                    # .env 模板
├── requirements.txt                # Python 依赖（含 pywebview + opencv）
├── packages.txt                    # Streamlit Cloud 系统依赖（OpenCV）
├── Dockerfile                      # Docker 镜像构建
├── .dockerignore                   # Docker 构建排除
├── docker-compose.yml              # 本地 Docker 测试
├── CLAUDE.md                       # 本文档
├── deploy_guide.md                 # 完整部署指南（方案A: Streamlit Cloud / 方案B: 阿里云SAE）
├── deploy.py                       # 一键部署检查脚本
├── desktop_app.py                  # 桌面原生窗口入口（本地模式+云端模式）
├── pwa_inline.py                   # PWA 内联资源（manifest + service worker data URI）
├── README.md                       # 人类可读的项目说明
│
├── .streamlit/
│   └── config.toml                 # Streamlit 主题和服务器配置
│
├── static/                         # PWA 图标和 manifest 源文件
│   ├── manifest.json
│   ├── sw.js
│   ├── icon-192.png
│   └── icon-512.png
│
├── data/                           # 运行时数据（不在 git 中）
│   ├── xhs_ai.db                   # SQLite 数据库
│   ├── media/                      # 上传的媒体文件
│   └── skills/                     # Skill 导出 JSON
│
├── src/                            # 核心代码
│   ├── config.py                   # 配置加载 + Anthropic 客户端工厂 + 重试 + 环境变量
│   ├── database.py                 # SQLAlchemy 引擎初始化
│   ├── models.py                   # 5 个数据模型
│   │
│   ├── analysis/                   # AI 分析引擎
│   │   ├── analyzer.py             # 笔记 → Skill 分析（支持多模态）
│   │   └── prompts.py              # 分析 Prompt 模板
│   │
│   ├── generation/                 # 内容生成引擎
│   │   ├── generator.py            # 生成 + 迭代优化（多 Skill 融合）
│   │   ├── prompts.py              # 生成 Prompt 模板 + 多模态消息构建
│   │   └── file_parser.py          # 文件解析（docx/xlsx/image/video/txt）
│   │
│   ├── ingestion/                  # 笔记导入
│   │   ├── importer.py             # 导入逻辑（单篇/批量/删除）
│   │   ├── parser.py               # 文本格式解析
│   │   └── media.py                # 媒体文件存储 + MCP 抽象
│   │
│   ├── skills/                     # Skill 管理
│   │   ├── manager.py              # Skill CRUD + 导入导出
│   │   └── schema.py               # Skill JSON Schema + patterns_to_text()
│   │
│   └── feedback/                   # 反馈自成长
│       └── loop.py                 # 评分收集 + Skill 增量优化
│
├── ui/                             # Streamlit 页面组件
│   ├── home.py                     # 首页仪表盘（5 步工作流展示）
│   ├── bloggers.py                 # 博主管理（增删改查）
│   ├── import_notes.py             # 笔记导入（粘贴 + 文件上传 + 图片/视频附件）
│   ├── analysis_page.py            # AI 分析触发页
│   ├── skills.py                   # Skill 管理与对比
│   ├── generate.py                 # 生成笔记（多 Skill + 聊天式交互 + 文件上传）
│   ├── history.py                  # 历史反馈浏览
│   └── materials.py                # 素材历史浏览
│
└── android-app/                    # Android WebView 包装项目
    ├── build.gradle                # 项目级 Gradle
    ├── settings.gradle
    ├── gradle.properties
    ├── gradle/wrapper/
    └── app/
        ├── build.gradle            # 应用级 Gradle
        ├── proguard-rules.pro
        └── src/main/
            ├── AndroidManifest.xml
            └── java/com/xhs/aiassistant/
                └── MainActivity.java   # 全屏 WebView + 文件上传支持
```

---

## 4. 数据库设计（5 张表，UUID 主键）

```
bloggers ──1:N──→ notes
bloggers ──1:N──→ skills ──1:N──→ generated_notes
bloggers ──1:N──→ materials (素材历史)
```

### 4.1 Blogger（博主）
| 列 | 类型 | 说明 |
|----|------|------|
| id | String(36) PK | UUID |
| name | String(100) | 唯一，博主名称 |
| description | Text | 博主描述 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 4.2 Note（笔记）
| 列 | 类型 | 说明 |
|----|------|------|
| id | String(36) PK | UUID |
| blogger_id | FK→bloggers.id | 所属博主 |
| title | String(500) | 笔记标题 |
| content | Text | 笔记正文 |
| source_url | String(500) | 来源 URL（可选） |
| metrics_json | Text | 互动数据 JSON `{likes, collects, comments, shares}` |
| **attachments_json** | Text | 附件元数据 JSON 数组 `[{id, original_name, saved_path, type}]` |
| published_at | DateTime | 发布时间 |
| imported_at | DateTime | 导入时间 |

### 4.3 Skill（写作风格模型）
| 列 | 类型 | 说明 |
|----|------|------|
| id | String(36) PK | UUID |
| blogger_id | FK→bloggers.id | 所属博主 |
| name | String(200) | Skill 名称 |
| **version** | Integer | 版本号（从 1 递增，旧版标记 outdated 不删除） |
| **patterns_json** | Text | 写作模式 JSON（核心数据，结构见 schema.py） |
| example_note_ids | Text | 分析时使用的笔记 ID 列表（JSON 数组） |
| total_notes_used | Integer | 分析的笔记总数 |
| **status** | String(20) | `training` / `ready` / `outdated` |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 4.4 GeneratedNote（AI 生成的笔记）
| 列 | 类型 | 说明 |
|----|------|------|
| id | String(36) PK | UUID |
| skill_id | FK→skills.id | 使用的 Skill |
| user_material | Text | 用户提供的素材 |
| user_requirements | Text | 用户的要求 |
| generated_content | Text | AI 生成的内容 |
| rating | Integer | 用户评分（1-5） |
| feedback_text | Text | 用户文字反馈 |
| created_at | DateTime | 生成时间 |

### 4.5 Material（素材历史）
| 列 | 类型 | 说明 |
|----|------|------|
| id | String(36) PK | UUID |
| blogger_id | FK→bloggers.id | 所属博主 |
| skill_id | FK→skills.id (nullable) | 使用的 Skill |
| material_text | Text | 素材文本 |
| requirements_text | Text | 要求文本 |
| file_names_json | Text | 上传文件名列表（JSON 数组） |
| image_count | Integer | 图片/视频帧数量 |
| generated_note_id | String(36) | 关联的生成笔记 ID |
| created_at | DateTime | 创建时间 |

---

## 5. 核心工作流

### 5.1 完整闭环
```
添加博主 → 导入笔记 → AI 分析生成 Skill → 输入素材+要求生成笔记
                                           ↓
                                    聊天式交互修改 ← 上传新素材
                                           ↓
                                    评分反馈 → 累积≥3条 → 优化Skill（版本化）
```

### 5.2 分析流程 (analyzer.py)
1. 查询博主的所有笔记（≥3 篇）
2. 从 `attachments_json` 加载图片（`load_attachments_as_images()`，最多 20 张）
3. 有图片 → 构建多模态 Claude 消息（文本 + base64 图片）
4. 无图片 → 纯文本 Prompt
5. 调用 `call_and_parse_json()` → 提取 Patterns JSON
6. 查找已有 Skill，版本号 +1（不覆盖旧版）
7. 新 Skill status="ready"，旧版 status="outdated"

### 5.3 生成流程 (generator.py)
1. 用户选择 1-多个 Skill（`st.multiselect`）
2. `_get_multi_skill_context()` 合并多个 Skill 的 patterns
3. 用户可上传文件（docx/xlsx/image/video/txt）→ `parse_uploaded_file()` 解析
4. 有图片 → 多模态 Claude API 调用
5. 无图片 → 纯文本 Prompt
6. 返回生成文本，同时保存 Material 记录

### 5.4 交互式修改流程 (generate.py UI + generator.py refine)
1. 生成后显示聊天面板（`st.session_state.chat_history`）
2. 用户输入修改意见，可选附加新素材（文件上传）
3. `refine_note()` 基于现有内容 + 修改意见 + 新素材重新生成
4. 支持多轮迭代

### 5.5 反馈优化流程 (loop.py)
1. 用户对生成笔记打分（1-5）
2. `submit_feedback()` 写入 GeneratedNote.rating
3. 当某 Skill 的评分反馈 ≥3 条 → `optimize_skill()` 可调用
4. Claude 分析反馈 ← → 当前 patterns → 输出优化后的 patterns
5. 旧 Skill status="outdated"，新建优化后的 Skill

---

## 6. 配置系统

### 6.1 API Key 解析优先级
```
st.secrets (Streamlit Cloud) → ${ENV_VAR} 替换 (config.yaml) → ValueError
```

### 6.2 环境变量
| 变量 | 必填 | 说明 |
|------|------|------|
| `ANTHROPIC_API_KEY` | 是 | Claude API Key（本地放 .env，云端放 Secrets） |
| `DATABASE_URL` | 否 | PostgreSQL 连接串（设置后优先于 SQLite） |
| `MEDIA_DIR` | 否 | 媒体文件目录（默认 `data/media`） |
| `CLOUD_URL` | 否 | desktop_app.py 的云端模式 URL |

### 6.3 config.yaml 关键配置
- `anthropic.model`: `claude-sonnet-4-6`
- `database.path`: `data/xhs_ai.db`
- `analysis.max_retries`: 3, `retry_delay`: 2
- `generation.temperature`: 0.8

### 6.4 Streamlit Cloud 部署
- `.streamlit/config.toml` — 主题（小红书红 #FE2C55）+ 服务器配置
- `packages.txt` — 系统依赖（libopencv-dev, libgl1）
- Secrets 通过 `st.secrets` 读取

---

## 7. 本地运行指南

```bash
# 1. 安装依赖
cd E:\小红书AI员工
pip install -r requirements.txt

# 2. 配置 API Key（二选一）
# 方式A: 环境变量
set ANTHROPIC_API_KEY=sk-...
# 方式B: .env 文件
echo ANTHROPIC_API_KEY=sk-... > .env

# 3. 启动（三选一）
streamlit run app.py                          # 网页版
python desktop_app.py                         # 桌面原生窗口
docker compose up -d                          # Docker 版

# 4. 浏览器访问 http://localhost:8501
```

---

## 8. 关键设计决策与约定

### 8.1 Skill 版本化（永不覆盖）
- 每次分析或优化产生新 Skill，version +1
- 旧 Skill 标记为 `status="outdated"`，保留所有历史版本
- 生成笔记时可选择任意 ready 状态的 Skill

### 8.2 多 Skill 融合
- `generate_note()` 和 `refine_note()` 接受 `skill_ids: list[str]`
- `_get_multi_skill_context()` 合并所有 Skill 的 patterns 文本
- 融合模式的 System Prompt 不同（`MULTI_SKILL_SYSTEM_PROMPT`），强调"取长补短"

### 8.3 图片/视频处理
- 图片始终 base64 编码在内存中流转，不落盘（除非用户上传到媒体库）
- 视频需写入临时文件（OpenCV 限制），处理后立即删除
- Claude API 图片限制：最长边 ≤1568px, JPEG quality 80
- 每次分析/生成最多携带 20 张图片

### 8.4 数据库
- **本地默认**：SQLite，`connect_args={"check_same_thread": False}` 适配 Streamlit 多线程
- **云端可选**：PostgreSQL，设置 `DATABASE_URL` 环境变量即可切换
- **迁移**：SQLAlchemy `create_all` 自动建表（开发阶段），生产环境建议用 Alembic

### 8.5 会话安全
- 数据库 session 使用 try/finally 确保关闭
- Claude API 调用有重试机制（`call_with_retry`），超时和 429 自动退避重试
- `load_config()` 使用 `@lru_cache()` 缓存，避免重复读文件

### 8.6 桌面版设计
- `desktop_app.py` 使用 subprocess 启动 Streamlit（避免 signal 线程问题）
- 支持两种模式：本地模式（默认，自启 Streamlit）/ 云端模式（设置 `CLOUD_URL` 环境变量）
- pywebview 创建原生窗口包裹 WebView

### 8.7 PWA
- `pwa_inline.py` 包含完整的 PWA manifest + service worker 作为 data URI 内联
- 原因：Streamlit 不提供 `/static/` 路径下的用户文件服务
- Service worker 缓存策略：`/` 仅缓存根路径

### 8.8 MCP 抽象（预留）
- `media.py` 中的 `ContentFetcher` Protocol 定义了未来 MCP 接入接口
- `set_fetcher()` / `get_fetcher()` 注册和使用
- `auto_fetch_note()` 和 `auto_fetch_blogger()` 自动调用已注册的 fetcher
- 当前无实现，等待 MCP 工具就绪

---

## 9. 云部署方案（已实现，暂不使用）

项目包含两种云部署方案，代码和配置已就绪：

### 方案 A：Streamlit Cloud（免费）
- 部署方式：GitHub 仓库 → share.streamlit.io
- 数据持久化：有限（容器重启会丢数据）
- 详见 `deploy_guide.md` 方案 A 章节

### 方案 B：阿里云 SAE（国内推荐，¥38-60/月）
- Docker 容器 + NAS 持久化 + ACR 镜像仓库
- 数据库和媒体文件存储在 NAS 上，不丢数据
- 详见 `deploy_guide.md` 方案 B 章节

---

## 10. 常见问题与陷阱

### 10.1 数据库
- **"No such table"**：删除了 `data/xhs_ai.db` 后自动重建，`create_all` 会自动建表
- **SQLite 多线程报错**：已通过 `check_same_thread=False` 修复
- **attachments_json 中的 saved_path 失效**：这是本地绝对路径，迁移到其他机器后需要文件也在相同路径。新代码同时支持 `storage_key`（相对路径）

### 10.2 Claude API
- **401 错误**：检查 API Key 是否有效
- **429 错误**：速率限制，`call_with_retry` 会自动退避重试
- **超时**：config.yaml 中 `timeout: 120`，可调大
- **JSON 解析失败**：`call_and_parse_json` 有两层容错 — 先去掉 markdown 代码块，再尝试从 `{` 到 `}` 提取

### 10.3 文件上传
- **视频无法解析**：需要 OpenCV（opencv-python-headless），确保已安装
- **大视频卡住**：最多提取 8 帧，每帧压缩到 1568px
- **DOCX 图片提取**：从 rels 中提取内嵌图片，可能遗漏外部链接图片

### 10.4 Streamlit
- **页面刷新状态丢失**：Streamlit 的 session_state 在脚本重跑时保持，但浏览器刷新会丢失
- **文件上传限制**：Streamlit 默认 200MB，可在 config.toml 中调整

---

## 11. 修改项目时的注意事项

1. **不要修改 `src/models.py` 的已有列名**：会影响现有数据库
2. **新增列用 nullable=True**：避免现有数据迁移问题
3. **多模态消息格式**：Claude API 要求 content 为 `[{"type": "text", ...}, {"type": "image", "source": {...}}]` 数组
4. **base64 图片不要拼接 data URI 前缀**：Claude API 需要分离的 `data` 和 `media_type`
5. **数据库 session 用完必须关闭**：使用 try/finally 模式
6. **添加新页面**：在 `app.py` 的 `pages` 字典中注册
7. **pywebview 只在 desktop_app.py 导入**：不要在其他模块导入，否则 Docker/云端会崩溃

---

## 12. 未来扩展方向

- [ ] MCP 工具接入（自动抓取小红书博主笔记）
- [ ] Alembic 数据库迁移
- [ ] OSS 对象存储（云端媒体文件）
- [ ] 用户认证系统
- [ ] 笔记发布 API 集成
- [ ] 分析报告导出（PDF）
- [ ] iOS PWA 优化
