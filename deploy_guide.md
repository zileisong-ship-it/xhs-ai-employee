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

三端共用同一台服务器 (Streamlit Cloud)，数据集中在云端。

---

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

---

## 技术架构说明

```
项目文件结构:
├── app.py                    # Streamlit 应用入口
├── config.yaml               # 本地配置
├── .streamlit/
│   └── config.toml           # Streamlit Cloud 主题/服务器配置
├── packages.txt              # 系统依赖 (OpenCV)
├── requirements.txt          # Python 依赖
├── src/
│   ├── config.py             # 配置 + Anthropic 客户端
│   ├── database.py           # SQLAlchemy 数据库
│   ├── models.py             # 数据模型定义
│   ├── analysis/             # AI 分析引擎
│   ├── generation/           # 笔记生成引擎
│   ├── ingestion/            # 笔记导入 + MCP 抽象
│   ├── skills/               # Skill 管理
│   └── feedback/             # 反馈循环
├── ui/                       # Streamlit 页面组件
├── desktop_app.py            # Windows/Mac 桌面版
├── android-app/              # Android WebView 项目
├── deploy.py                 # 一键部署脚本
└── deploy_guide.md           # 本文件
```
