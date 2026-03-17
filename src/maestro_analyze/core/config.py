"""配置管理。

~/.maestro-analyst/
├── config.toml      # 用户配置
├── data/            # DuckDB 数据文件
├── templates/       # 用户自定义模板
└── outputs/         # 分析结果输出
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:
        raise ImportError("Install 'tomli' for Python < 3.11") from exc

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------

BASE_DIR = Path.home() / ".maestro" / "analyst"
CONFIG_PATH = BASE_DIR / "config.toml"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUTS_DIR = BASE_DIR / "outputs"
PLUGINS_DIR = BASE_DIR / "plugins"

# ---------------------------------------------------------------------------
# 默认配置
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict = {
    "data": {
        "dir": str(DATA_DIR),
        "default_db": "workspace.duckdb",
    },
    "output": {
        "dir": str(OUTPUTS_DIR),
        "chart_format": "html",  # html | png | svg
        "chart_theme": "plotly_white",
    },
    "analysis": {
        "max_rows_preview": 20,
        "auto_detect_types": True,
        "locale": "zh-CN",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(path: Path | None = None) -> dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as f:
            config = _deep_merge(config, tomllib.load(f))
    if path is not None and path.exists():
        with path.open("rb") as f:
            config = _deep_merge(config, tomllib.load(f))
    return config


def ensure_dirs() -> None:
    """确保所有必要目录存在。"""
    for d in (BASE_DIR, DATA_DIR, TEMPLATES_DIR, OUTPUTS_DIR, PLUGINS_DIR):
        d.mkdir(parents=True, exist_ok=True)
