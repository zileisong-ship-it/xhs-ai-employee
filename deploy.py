"""One-click deployment helper for 小红书AI写作分析系统.

Handles:
1. Git initialization and GitHub push
2. Streamlit Cloud deployment verification
3. Android APK build guidance
"""
import os
import sys
import subprocess
import json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def run(cmd, cwd=None):
    """Run a command and return stdout."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or PROJECT_DIR,
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def check_git():
    """Check git installation and repo status."""
    section("1. Git 仓库检查")
    _, _, code = run("git --version")
    if code != 0:
        print("[错误] 未安装 Git，请先安装: https://git-scm.com")
        return False

    # Check if already a git repo
    if os.path.exists(os.path.join(PROJECT_DIR, ".git")):
        print("[OK] Git 仓库已存在")
        out, _, _ = run("git remote -v")
        if "origin" in out:
            print(f"[OK] 远程仓库已配置:")
            for line in out.split("\n"):
                if line.strip():
                    print(f"     {line.strip()}")
        else:
            print("[提示] 未配置远程仓库，需要设置 GitHub 仓库")
        return True
    else:
        print("[提示] 尚未初始化 Git 仓库")
        return True

def init_and_push():
    """Initialize git and push to GitHub."""
    section("2. 推送到 GitHub")

    # Check if origin exists
    out, _, _ = run("git remote get-url origin")
    if out:
        print(f"[OK] 远程仓库: {out}")
        choice = input("是否重新推送? (y/n): ").strip().lower()
        if choice != 'y':
            return

    # Create .gitignore if not present
    gitignore = os.path.join(PROJECT_DIR, ".gitignore")
    if not os.path.exists(gitignore):
        print("[提示] 创建 .gitignore...")
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write("""# Python
__pycache__/
*.py[cod]
*.egg-info/
.env
venv/

# Project data
data/*.db
data/media/

# IDE
.vscode/
.idea/

# Android
android-app/build/
android-app/app/build/
android-app/.gradle/
android-app/*.apk
""")

    # Stage and commit
    run('git add -A')
    out, err, code = run('git status --short')
    if not out:
        print("[提示] 没有文件变更")
    else:
        commit_msg = input("输入 commit 信息 (默认: 'Deploy to cloud'): ").strip()
        if not commit_msg:
            commit_msg = "Deploy to cloud"
        run(f'git commit -m "{commit_msg}"')

    # Push
    print("\n推送到 GitHub...")
    out, err, code = run("git push -u origin main")
    if code != 0:
        # Try master branch
        out, err, code = run("git push -u origin master")
        if code != 0:
            print(f"[错误] 推送失败: {err}")
            print("\n请确保:")
            print("  1. 已在 GitHub 创建仓库")
            print("  2. 已配置远程仓库: git remote add origin <URL>")
            return False
    print("[OK] 推送成功!")
    return True

def check_streamlit_config():
    """Verify Streamlit Cloud config files."""
    section("3. Streamlit Cloud 配置检查")

    all_ok = True
    checks = [
        (".streamlit/config.toml", "主题和服务器配置"),
        ("packages.txt", "系统依赖 (OpenCV)"),
        ("requirements.txt", "Python 依赖"),
        ("app.py", "应用入口"),
    ]

    for path, desc in checks:
        full_path = os.path.join(PROJECT_DIR, path)
        if os.path.exists(full_path):
            print(f"[OK] {path} ({desc})")
        else:
            print(f"[缺失] {path} ({desc})")
            all_ok = False

    # Check that config.py uses st.secrets
    config_path = os.path.join(PROJECT_DIR, "src", "config.py")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "st.secrets" in content:
            print("[OK] API Key 使用 Streamlit Secrets")
        else:
            print("[警告] 请确保 config.py 支持 st.secrets 获取 API Key")

    return all_ok

def streamlit_cloud_instructions():
    """Print Streamlit Cloud deployment steps."""
    section("4. Streamlit Cloud 部署步骤")

    print("""
  步骤 1: 访问 https://share.streamlit.io
  步骤 2: 使用 GitHub 账号登录
  步骤 3: 点击 "New app"
  步骤 4: 选择你的仓库、分支 (main/master)
  步骤 5: Main file path 设为 "app.py"
  步骤 6: 点击 "Deploy!"

  配置 Secrets:
    在 App Settings → Secrets 中添加:
    ANTHROPIC_API_KEY = "你的 API Key"

  注意:
    - Streamlit Cloud 免费版有资源限制 (1GB RAM, 共享CPU)
    - 应用在无访问时会自动休眠
    - 数据存储在容器本地，重新部署不会丢失
    - 如需持久化数据，建议后续接入 Supabase/Turso
""")

def android_build_instructions():
    """Print Android build instructions."""
    section("5. Android APK 构建步骤")

    # Check if Android project exists
    android_dir = os.path.join(PROJECT_DIR, "android-app")
    if os.path.exists(android_dir):
        print("[OK] Android 项目已创建: android-app/")
    else:
        print("[提示] 未找到 Android 项目")

    print("""
  方法 A: 使用 Android Studio (推荐)
    1. 安装 Android Studio: https://developer.android.com/studio
    2. 打开 android-app/ 目录
    3. 修改 MainActivity.java 中的 APP_URL 为你的 Streamlit Cloud URL
    4. Build → Build Bundle(s) / APK(s) → Build APK(s)
    5. APK 位于: android-app/app/build/outputs/apk/debug/

  方法 B: 使用命令行
    1. 安装 JDK 17+ 和 Android SDK
    2. cd android-app
    3. ./gradlew assembleDebug (Linux/Mac)
       或 gradlew.bat assembleDebug (Windows)
    4. APK 位于: app/build/outputs/apk/debug/

  分发到手机:
    - 通过微信发送 APK 文件
    - 安装时需允许"未知来源"安装
    - 或使用二维码下载 (上传到网盘后生成)
""")

def check_secrets():
    """Check if API key is configured."""
    section("6. API Key 检查")

    env_path = os.path.join(PROJECT_DIR, ".env")
    config_path = os.path.join(PROJECT_DIR, "config.yaml")

    # Check .env
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "ANTHROPIC_API_KEY" in content and "sk-" in content:
            print("[OK] 本地 .env 中已配置 API Key")
        else:
            print("[提示] .env 文件中未找到有效的 API Key")
    else:
        print("[提示] 未找到 .env 文件")

    # Check config.yaml
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "ANTHROPIC_API_KEY" in content:
            print("[OK] config.yaml 引用了环境变量")
        else:
            print("[提示] config.yaml 中未配置 API Key")

    print("""
  云端部署提醒:
    - 在 Streamlit Cloud → App Settings → Secrets 中添加:
      ANTHROPIC_API_KEY = "sk-..."
    - 不要在代码中硬编码 API Key
""")

def main():
    print("=" * 60)
    print("  小红书AI写作分析系统 - 一键部署助手")
    print("=" * 60)

    if not check_git():
        return

    print("\n部署流程:")
    print("  1. 推送代码到 GitHub")
    print("  2. 在 Streamlit Cloud 部署")
    print("  3. 验证部署")
    print("  4. 构建 Android APK (可选)")
    print("  5. 更新桌面快捷方式 URL (可选)")

    choice = input("\n是否自动执行 Git 推送? (y/n): ").strip().lower()
    if choice == 'y':
        init_and_push()

    check_streamlit_config()
    check_secrets()
    streamlit_cloud_instructions()
    android_build_instructions()

    print(f"\n{'=' * 60}")
    print("  部署检查完成！")
    print(f"{'=' * 60}")
    print("""
  快速命令参考:
    本地运行:     streamlit run app.py
    桌面版:       python desktop_app.py
    Git推送:      git push
    云端URL:      https://YOUR_APP_NAME.streamlit.app
  文档:          deploy_guide.md
""")

if __name__ == "__main__":
    main()
