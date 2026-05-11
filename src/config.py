"""Shared configuration and Anthropic client factory."""

import os
import time
import yaml
from functools import lru_cache
from anthropic import Anthropic, APIStatusError, APITimeoutError


@lru_cache()
def load_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_client() -> Anthropic:
    config = load_config()

    # 1. Streamlit Cloud secrets 优先
    api_key = ""
    try:
        import streamlit as st
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    # 2. 本地：config.yaml 环境变量引用
    if not api_key:
        api_key = config["anthropic"]["api_key"]
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var, "")

    if not api_key:
        raise ValueError("请设置 ANTHROPIC_API_KEY（本地用 .env，云端用 Streamlit Secrets）")
    timeout = config["anthropic"].get("timeout", 120)
    return Anthropic(api_key=api_key, timeout=timeout)


def call_with_retry(client: Anthropic, config_section: str, **kwargs) -> str:
    """Call Claude API with retry logic. Returns response text."""
    config = load_config()
    max_retries = config.get(config_section, {}).get("max_retries", 3)
    retry_delay = config.get(config_section, {}).get("retry_delay", 2)

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(**kwargs)
            return response.content[0].text.strip()
        except APITimeoutError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
        except APIStatusError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1) * 2)
            else:
                raise
    raise last_error


def get_env_config() -> dict:
    """返回环境变量驱动的部署配置，优先使用环境变量，否则使用默认值。

    支持的环境变量:
      DATABASE_URL  — PostgreSQL 连接串（设置后优先于 SQLite）
      MEDIA_DIR     — 媒体文件存储目录（默认: data/media）
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    return {
        "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        "MEDIA_DIR": os.environ.get("MEDIA_DIR", os.path.join(project_root, "data", "media")),
    }


def call_and_parse_json(client: Anthropic, config_section: str, **kwargs) -> dict:
    """Call Claude API with retry and parse response as JSON."""
    import json
    raw_text = call_with_retry(client, config_section, **kwargs)

    # 清理 markdown 代码块
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        if lines[0].startswith("```"):
            raw_text = "\n".join(lines[1:])
        if raw_text.rstrip().endswith("```"):
            raw_text = raw_text.rstrip()[:-3].rstrip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw_text[start:end])
        raise ValueError(f"AI 返回的结果无法解析为 JSON:\n{raw_text[:500]}")
