# 小红书AI写作分析系统 - 完整部署指南

## 架构概览

```
┌─────────────────────────────────────────────┐
│              Streamlit Cloud                 │
│  ┌───────────────────────────────────────┐  │
│  │       app.py (Streamlit)              │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │  │
│  │  │首页 │ │博主 │ │分析 │ │生成 │...│   │  │
│  │  └─────┘ └─────┘ └─────┘ └─────┘   │  │
│  │  SQLite DB + uploaded media files    │  │
│  └───────────────────────────────────────┘  │
│  API Key → st.secrets (secure)              │
└──────────────┬──────────────────────────────┘
               │ HTTPS
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Desktop App  │ │ Android APK  │
│ (pywebview)  │ │ (WebView)    │
│ Windows/Mac  │ │ 手机端       │
└─────────────┘ └─────────────┘
```

三端共用同一台服务器，数据集中在云端。

---

## 部署方案选择

| 方案 | 适合人群 | 费用 | 国内速度 | 数据持久化 |
|------|----------|------|----------|------------|
| **A: Streamlit Cloud** | 个人、测试、海外用户 | 免费 | 一般 | 容器重启会丢数据 |
| **B: 阿里云 SAE + NAS** | 国内用户、生产环境 | ~¥30-60/月 | 快 | NAS 持久化，不丢数据 |

下面分别介绍两种方案。

---

# 方案 A：Streamlit Cloud 部署（免费）

## 第一步：准备 GitHub 仓库

### 1.1 安装 Git

```bash
# Windows: 下载安装 https://git-scm.com
# Mac: brew install git
```

### 1.2 创建 GitHub 仓库

1. 访问 https://github.com 并登录
2. 点击右上角 "+" → "New repository"
3. Repository name: `xhs-ai-assistant` (或其他名称)
4. 选择 **Private** (推荐，保护 API key 配置)
5. 不要勾选 "Add a README file"
6. 点击 "Create repository"

### 1.3 推送代码

```bash
cd E:\小红书AI员工

# 初始化 Git (如果尚未初始化)
git init
git add -A
git commit -m "Initial commit: 小红书AI写作分析系统"

# 关联远程仓库并推送
git remote add origin https://github.com/YOUR_USERNAME/xhs-ai-assistant.git
git branch -M main
git push -u origin main
```

---

## 第二步：Streamlit Cloud 部署

### 2.1 部署应用

1. 访问 https://share.streamlit.io
2. 用 GitHub 账号登录
3. 点击 **"New app"** 按钮
4. 配置：
   - **Repository**: `YOUR_USERNAME/xhs-ai-assistant`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 自定义一个子域名 (如 `xhs-ai`)
5. 点击 **"Deploy!"**

### 2.2 配置 API Key (Secrets)

在应用页面 → **Settings** → **Secrets** 中添加：

```toml
ANTHROPIC_API_KEY = "sk-your-api-key-here"
```

> **重要**: 必须使用 Secrets 存储 API Key，不要提交到代码仓库！

### 2.3 验证部署

访问 `https://YOUR_APP_NAME.streamlit.app`，确认应用正常运行。

首次部署后：
- 应用 URL 固定不变
- 每次 `git push` 到 main 分支后自动重新部署
- 数据文件 (SQLite DB) 在重新部署后保留（只要不重启容器）

---

## 第三步：桌面版更新 URL

修改 `desktop_app.py` 中的 URL，指向你的 Streamlit Cloud 地址：

```python
# 找到这一行:
webview.create_window(title="小红书AI写作助手", url="http://localhost:8501", ...)

# 改为你的云端 URL:
webview.create_window(title="小红书AI写作助手", url="https://YOUR_APP_NAME.streamlit.app", ...)
```

这样桌面版就变成了云端客户端，即使电脑上的 Python 环境没运行也能使用。

---

## 第四步：构建 Android APK

### 4.1 修改应用 URL

编辑 `android-app/app/src/main/java/com/xhs/aiassistant/MainActivity.java`：

```java
// 第 46 行, 改为你的 Streamlit Cloud URL:
private static final String APP_URL = "https://YOUR_APP_NAME.streamlit.app";
```

### 4.2 方法 A：使用 Android Studio 构建 (推荐)

1. 安装 [Android Studio](https://developer.android.com/studio)
2. 打开 `android-app/` 目录
3. 等待 Gradle 同步完成
4. 菜单栏: **Build → Build Bundle(s) / APK(s) → Build APK(s)**
5. 生成的 APK 位于: `android-app/app/build/outputs/apk/debug/app-debug.apk`

### 4.3 方法 B：命令行构建

**前置要求：**
- JDK 17+
- Android SDK (通过 Android Studio 或命令行安装)
- 设置 `ANDROID_HOME` 环境变量

```bash
# Windows
cd android-app
gradlew.bat assembleDebug

# Mac/Linux
cd android-app
chmod +x gradlew
./gradlew assembleDebug
```

### 4.4 生成签名 APK (正式版)

```
1. Android Studio → Build → Generate Signed Bundle / APK
2. 选择 APK
3. 创建新的 keystore (保存好密码和文件)
4. 选择 release 构建
5. 生成的 APK 可以正式分发
```

### 4.5 分发到手机

**微信分发：**
1. 将 APK 文件发送到微信"文件传输助手"
2. 在手机微信中下载 APK
3. 点击 APK 文件安装
4. 允许"未知来源"安装

**二维码分发：**
1. 上传 APK 到网盘 (百度网盘/阿里云盘/蓝奏云)
2. 生成分享链接的二维码
3. 手机扫码下载安装

---

## 第五步：更新桌面快捷方式

修改桌面快捷方式指向云端：

**方案 1**：更新 `desktop_app.py` 中的 URL 后重新创建快捷方式：
```bash
pythonw.exe E:\小红书AI员工\desktop_app.py
```

**方案 2**：直接创建浏览器快捷方式：
- 用 Chrome 打开 `https://YOUR_APP_NAME.streamlit.app`
- Chrome 菜单 → 更多工具 → 创建快捷方式 → 勾选"在窗口中打开"

---

## 日常使用流程

| 场景 | 操作 |
|------|------|
| **电脑使用** | 双击桌面快捷方式打开桌面版，或直接访问网页版 |
| **手机使用** | 打开"小红书AI助手"APP |
| **更新功能** | `git push` 到 main 分支，Streamlit Cloud 自动部署 |
| **所有设备** | 共享同一套数据和配置 |

---

# 方案 B：阿里云 SAE 部署（国内推荐）

## 架构概览

```
┌──────────────────────────────────────────────┐
│           阿里云 SAE (Serverless)             │
│  ┌────────────────────────────────────────┐  │
│  │  Docker Container (python:3.12-slim)   │  │
│  │  ┌──────────────────────────────────┐  │  │
│  │  │  app.py (Streamlit :8501)        │  │  │
│  │  │  + UI + AI analysis/generation   │  │  │
│  │  └──────────────────────────────────┘  │  │
│  │  data/xhs_ai.db  ← NAS 挂载           │  │
│  │  data/media/     ← NAS 挂载           │  │
│  └──────────────┬───────────────────────┘  │
│                 │                            │
│  ┌──────────────┴───────────────────────┐  │
│  │  阿里云 NAS (持久存储)                 │  │
│  │  - 数据库文件永不丢失                  │  │
│  │  - 媒体文件永不丢失                    │  │
│  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## B.1 前置准备

### 需要的阿里云服务

| 服务 | 用途 | 费用 |
|------|------|------|
| **SAE** (Serverless App Engine) | 运行 Docker 容器 | 按量: ~¥0.003/核·秒 |
| **ACR** (容器镜像服务) | 存储 Docker 镜像 | 个人版免费 |
| **NAS** (文件存储) | 持久化数据库和媒体文件 | ~¥0.35/GB·月 (最低 ¥10/月) |

> 个人使用预估：¥30-60/月（1核2G，10GB NAS）

### 安装阿里云 CLI（可选，也可用网页控制台）

```bash
# Windows (PowerShell 管理员)
winget install Alibaba.AlibabaCloudCLI

# 配置凭证
aliyun configure
# 输入 AccessKey ID 和 AccessKey Secret
```

---

## B.2 本地构建 Docker 镜像

```bash
cd E:\小红书AI员工

# 构建镜像
docker build -t xhs-ai-staff:latest .

# 本地测试运行
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-... xhs-ai-staff:latest

# 浏览器打开 http://localhost:8501 验证
```

---

## B.3 推送镜像到阿里云 ACR

### 1. 创建容器镜像仓库

访问 https://cr.console.aliyun.com：
- 创建 **个人版** 实例
- 命名空间: `xhs`
- 仓库名称: `xhs-ai-staff`
- 仓库类型: 私有

### 2. 登录并推送

```bash
# 登录 ACR（替换为你的地域和命名空间）
docker login --username=你的阿里云账号 registry.cn-hangzhou.aliyuncs.com

# 打标签
docker tag xhs-ai-staff:latest registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest

# 推送
docker push registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest
```

---

## B.4 创建 NAS 文件系统

访问 https://nas.console.aliyun.com：

1. 创建文件系统：
   - 类型: **通用型**
   - 协议: **NFS**
   - 地域: 与 SAE 相同（如杭州）
   - 容量型即可

2. 记录以下信息备用：
   - 文件系统 ID (如 `123456-abc.cn-hangzhou.nas.aliyuncs.com`)
   - 挂载点域名

3. 创建挂载点目录（在 SAE 部署时自动创建）：
   - `/app/data` — 数据库和媒体文件目录

---

## B.5 在 SAE 创建应用

访问 https://sae.console.aliyun.com：

### 1. 创建应用

- **应用名称**: `xhs-ai-staff`
- **运行时**: 容器镜像
- **镜像地址**: `registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest`
- **命名空间**: 默认或新建
- **VPC/交换机**: 选择或新建（SAE 会自动配置）

### 2. 资源配置

```
CPU: 1 核
内存: 2 GB
实例数: 1（个人使用即可）
```

### 3. 配置环境变量

在应用设置中添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `ANTHROPIC_API_KEY` | `sk-你的key` | Claude API 密钥 |

### 4. 配置 NAS 挂载

在 **存储** 或 **持久化存储** 设置中：

- 挂载点: `/app/data`
- NAS 文件系统: 选择 B.4 创建的
- 容量: 10 GB

### 5. 配置 SLB（公网访问）

- 在 **网络设置** 中启用公网访问
- SAE 自动分配一个公网域名（如 `xhs-ai-staff.cn-hangzhou.sae.aliyuncs.com`）

### 6. 部署

点击 **确认创建**，SAE 自动拉取镜像启动容器。

---

## B.6 配置自定义域名（可选）

1. 在阿里云 **DNS** 或你的域名服务商添加 CNAME 记录
2. 指向 SAE 分配的公网域名
3. 在 SAE → 应用 → 域名管理 中添加自定义域名
4. 上传 SSL 证书启用 HTTPS

---

## B.7 更新应用

每次代码更新后：

```bash
# 1. 重新构建
docker build -t xhs-ai-staff:latest .

# 2. 推送到 ACR
docker tag xhs-ai-staff:latest registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest
docker push registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest

# 3. 在 SAE 控制台 → 应用 → 变更镜像 → 部署
# 或使用 CLI:
aliyun sae DeployApplication \
  --AppId <app-id> \
  --ImageUrl registry.cn-hangzhou.aliyuncs.com/xhs/xhs-ai-staff:latest
```

---

## B.8 方案 B 环境变量参考

Docker 容器支持的环境变量汇总：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `ANTHROPIC_API_KEY` | 是 | — | Claude API 密钥 |
| `DATABASE_URL` | 否 | — | PostgreSQL 连接串（可选，用于替代 SQLite） |
| `MEDIA_DIR` | 否 | `data/media` | 媒体文件目录 |

## B.9 方案 B 成本估算

| 资源 | 规格 | 月费（约） |
|------|------|------------|
| SAE 计算 | 1核2G × 1实例 | ¥25-40 |
| NAS 存储 | 10 GB | ¥3-5 |
| ACR 镜像 | 个人版 | 免费 |
| SLB 公网 | 共享 | ¥10-15 |
| **合计** | | **¥38-60/月** |

> 如用 SAE 按量计费（无访问时缩容到 0），费用可降低 50% 以上。

---

## 常见问题

### Q: Streamlit Cloud 免费版有什么限制？
- 1 GB RAM，共享 CPU
- 无外部网络访问 (不能调用其他 API，但 Claude API 走的是 HTTPS，可以)
- 无固定 IP
- 长时间无访问会自动休眠（下次访问自动唤醒，约需 30 秒）

### Q: 数据会丢失吗？
- SQLite 数据库存储在容器本地磁盘
- `git push` 重新部署不会清除数据
- 但如果 Streamlit 重启容器（偶发），数据会丢失
- 建议定期导出数据备份

### Q: 如何升级到持久化数据库？
- 使用 [Turso](https://turso.tech) (SQLite 兼容，免费 9GB)
- 使用 [Supabase](https://supabase.com) (PostgreSQL，免费 500MB)
- 后续可以集成，只需修改 `src/database.py` 的连接字符串

### Q: Android APP 提示"网页无法加载"？
1. 检查手机网络连接
2. 确认 APP_URL 已改为正确的 Streamlit Cloud URL
3. 确认 Streamlit Cloud 应用没有休眠（等待 30 秒唤醒）
4. 检查 AndroidManifest.xml 中 `usesCleartextTraffic="true"` 已设置

### Q: 如何更新 Android APP？
- 重新构建 APK 并安装即可覆盖旧版本
- 或者 APP 内部通过 WebView 自动加载最新的云端代码，无需更新 APP

### Q: SAE 和 Streamlit Cloud 怎么选？
- **只在国内用、想要可靠服务** → 阿里云 SAE
- **只是自己玩玩、能接受偶尔无法访问** → Streamlit Cloud 免费版
- 两套可以同时部署，共用同一套代码

### Q: SAE 的 NAS 数据会丢吗？
- NAS 是独立的持久化存储服务，不是容器本地磁盘
- 容器重启、重新部署都不会影响 NAS 数据
- NAS 本身有 99.9999999% 的数据可靠性保障

### Q: 如何从 Streamlit Cloud 迁移到 SAE？
1. 下载 Streamlit Cloud 上的 `data/xhs_ai.db` 和 `data/media/`
2. 上传到 SAE 的 NAS 挂载目录
3. 更新 Android 和桌面版的 URL 指向 SAE 地址
4. 完成迁移

---

## 技术架构说明

```
项目文件结构:
├── app.py                    # Streamlit 应用入口
├── config.yaml               # 本地配置
├── Dockerfile                # Docker 容器化
├── .dockerignore             # Docker 构建排除
├── docker-compose.yml        # 本地 Docker 测试
├── .streamlit/
│   └── config.toml           # Streamlit Cloud 主题/服务器配置
├── packages.txt              # 系统依赖 (OpenCV, Streamlit Cloud用)
├── requirements.txt          # Python 依赖
├── src/
│   ├── config.py             # 配置 + Anthropic 客户端 + 环境变量
│   ├── database.py           # SQLAlchemy 数据库 (SQLite/PostgreSQL)
│   ├── models.py             # 数据模型定义 (5 tables)
│   ├── storage.py            # (预留) 云存储抽象
│   ├── analysis/             # AI 分析引擎
│   ├── generation/           # 笔记生成引擎
│   ├── ingestion/            # 笔记导入 + 媒体存储 + MCP 抽象
│   ├── skills/               # Skill 管理
│   └── feedback/             # 反馈循环
├── ui/                       # Streamlit 页面组件
├── desktop_app.py            # Windows/Mac 桌面版
├── android-app/              # Android WebView 项目
├── deploy.py                 # 一键部署脚本
└── deploy_guide.md           # 本文件
```
