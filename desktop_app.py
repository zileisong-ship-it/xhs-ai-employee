"""小红书AI写作分析系统 - 桌面版入口

支持两种模式:
1. 本地模式: 启动本地 Streamlit 服务器
2. 云端模式: 连接已部署的 Streamlit Cloud 服务器

通过 CLOUD_URL 环境变量或直接修改 DEFAULT_CLOUD_URL 来切换。
"""
import os
import sys
import time
import subprocess
import urllib.request

# 强制 UTF-8 编码，解决 Windows 下 pywebview 中文乱码
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.getdefaultencoding() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 设置为你的 Streamlit Cloud URL（部署后填入）
DEFAULT_CLOUD_URL = os.environ.get("CLOUD_URL", "")


def wait_for_server(url, max_wait=40):
    """等待服务器就绪。"""
    for _ in range(max_wait):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    # 确定 URL
    cloud_url = DEFAULT_CLOUD_URL

    if cloud_url:
        # 云端模式：直接连接远程服务器
        url = cloud_url
        streamlit_proc = None
    else:
        # 本地模式：启动本地 Streamlit（传递 UTF-8 编码环境）
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["XHS_DESKTOP_MODE"] = "1"  # 告诉 app.py 跳过 PWA 注入
        streamlit_proc = subprocess.Popen(
            [
                sys.executable, "-X", "utf8", "-m", "streamlit", "run", "app.py",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--server.port", "8501",
            ],
            cwd=os.path.dirname(__file__),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        url = "http://localhost:8501"
        if not wait_for_server(url):
            streamlit_proc.terminate()
            print("本地服务器启动失败")
            sys.exit(1)

    # 打开原生桌面窗口（Edge Chromium 内核）
    import webview

    # 检查 WebView2 是否可用
    webview_ok = False
    try:
        from webview import config as wv_config
        wv_config.gui = 'edgechromium'
        wv_config.gui  # 确认设置生效
        webview_ok = True
    except Exception:
        pass

    if webview_ok:
        try:
            webview.create_window(
                title="小红书AI写作助手",
                url=url,
                width=1280,
                height=860,
                min_size=(900, 600),
                text_select=True,
            )
            webview.start()
        except Exception as e:
            print(f"pywebview 启动失败: {e}")
            webview_ok = False

    # 如果 pywebview 不可用，回退到系统浏览器 app 模式
    if not webview_ok:
        import webbrowser
        print("使用系统浏览器打开...")
        # 尝试用 Chrome/Edge app 模式（无浏览器边框的窗口）
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        ]
        browser_launched = False
        for browser in chrome_paths:
            if os.path.exists(browser):
                subprocess.Popen([browser, f"--app={url}", "--window-size=1280,860"])
                browser_launched = True
                break

        if not browser_launched:
            webbrowser.open(url)

        # 等待 Streamlit 进程（用户关闭浏览器窗口后手动 Ctrl+C 退出）
        try:
            while streamlit_proc and streamlit_proc.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # 窗口关闭后清理
    if streamlit_proc:
        streamlit_proc.terminate()
        streamlit_proc.wait(timeout=5)
    os._exit(0)


if __name__ == "__main__":
    main()
