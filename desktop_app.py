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
    # 确保使用 Edge Chromium 内核，避免 IE 内核中文乱码
    try:
        from webview import config as wv_config
        wv_config.gui = 'edgechromium'
    except Exception:
        pass

    webview.create_window(
        title="小红书AI写作助手",
        url=url,
        width=1280,
        height=860,
        min_size=(900, 600),
        text_select=True,
    )
    webview.start()

    # 窗口关闭后清理
    if streamlit_proc:
        streamlit_proc.terminate()
        streamlit_proc.wait(timeout=5)
    os._exit(0)


if __name__ == "__main__":
    main()
