# app_paths.py — 开发目录 / PyInstaller 打包后的资源与用户数据路径

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """只读资源（json、log.config 模板等）。"""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """可写用户配置（overlay_settings.json 等）。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return bundle_dir()


def resource_path(*parts: str) -> Path:
    return bundle_dir().joinpath(*parts)
