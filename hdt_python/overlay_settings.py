# overlay_settings.py — Overlay 用户设置（持久化 JSON）

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from hdt_python.app_paths import user_data_dir

DEFAULT_SETTINGS_PATH = user_data_dir() / "overlay_settings.json"

SETTINGS_VERSION = 1


@dataclass
class OverlaySettings:
    """Overlay 显示与行为配置。"""

    version: int = SETTINGS_VERSION

    # 外观
    theme: str = "dark"  # dark | light | transparent
    opacity: int = 230
    scale_percent: int = 100
    show_border: bool = True
    show_header: bool = True
    app_title: str = "HS 斩杀助手"

    # 显示内容
    show_combo_overlay: bool = True
    show_spell_detail: bool = True
    show_breakdown: bool = True
    show_calc_time: bool = True
    show_taunt_line: bool = True
    show_hp_line: bool = True
    show_threat_line: bool = True
    show_lethal_diff: bool = True
    compact_mode: bool = False

    # 窗口
    attach_to_game: bool = True
    use_layered: bool = False
    offset_x: int = 100
    offset_y: int = 20
    refresh_ms: int = 500

    # 控制台
    console_refresh_sec: float = 2.0

    def normalized(self) -> "OverlaySettings":
        """钳制非法值，返回新实例。"""
        d = asdict(self)
        d["version"] = SETTINGS_VERSION
        d["theme"] = d["theme"] if d["theme"] in ("dark", "light", "transparent") else "dark"
        d["opacity"] = max(80, min(255, int(d["opacity"])))
        d["scale_percent"] = max(75, min(150, int(d["scale_percent"])))
        d["offset_x"] = max(0, min(800, int(d["offset_x"])))
        d["offset_y"] = max(0, min(600, int(d["offset_y"])))
        d["refresh_ms"] = max(200, min(2000, int(d["refresh_ms"])))
        d["console_refresh_sec"] = max(0.5, min(10.0, float(d["console_refresh_sec"])))
        d["app_title"] = (d["app_title"] or "HS 斩杀助手").strip()[:40]
        return OverlaySettings(**{k: d[k] for k in {f.name for f in fields(OverlaySettings)}})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self.normalized())

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OverlaySettings":
        if not data:
            return cls()
        known = {f.name for f in fields(cls)}
        kwargs = {k: data[k] for k in known if k in data}
        return cls(**kwargs).normalized()

    def merge_cli(self, *, layered: Optional[bool] = None, float_overlay: Optional[bool] = None) -> "OverlaySettings":
        """命令行参数覆盖配置文件（显式传入时才覆盖）。"""
        s = deepcopy(self.normalized())
        if layered is not None:
            s.use_layered = bool(layered)
        if float_overlay is not None:
            s.attach_to_game = not bool(float_overlay)
        return s


class OverlaySettingsStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_SETTINGS_PATH
        self._settings = OverlaySettings()
        self._listeners: List[Callable[[OverlaySettings], None]] = []

    @property
    def settings(self) -> OverlaySettings:
        return self._settings

    def load(self) -> OverlaySettings:
        if not self.path.is_file():
            self._settings = OverlaySettings()
            return self._settings
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._settings = OverlaySettings.from_dict(raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._settings = OverlaySettings()
        return self._settings

    def save(self, settings: Optional[OverlaySettings] = None) -> OverlaySettings:
        if settings is not None:
            self._settings = settings.normalized()
        else:
            self._settings = self._settings.normalized()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._notify()
        return self._settings

    def update(self, **kwargs) -> OverlaySettings:
        d = asdict(self._settings)
        d.update(kwargs)
        return self.save(OverlaySettings.from_dict(d))

    def on_change(self, callback: Callable[[OverlaySettings], None]) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb(self._settings)
            except Exception:
                pass
