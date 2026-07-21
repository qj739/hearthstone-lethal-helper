# overlay_settings_ui.py — Overlay 设置窗口（tkinter）

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from hdt_python.overlay_settings import OverlaySettings, OverlaySettingsStore


class OverlaySettingsWindow:
    """商业软件风格的设置面板。"""

    def __init__(
        self,
        store: OverlaySettingsStore,
        *,
        on_apply: Optional[Callable[[OverlaySettings], None]] = None,
        settings_path=None,
    ):
        self.store = store
        self.on_apply = on_apply
        self.settings_path = settings_path or store.path
        self._vars: dict = {}
        self.root: Optional[tk.Tk] = None

    def run(self) -> None:
        self.root = tk.Tk()
        self.root.title("Overlay 设置")
        self.root.geometry("520x560")
        self.root.minsize(480, 520)
        self.root.configure(bg="#f0f2f5")

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        header = tk.Frame(self.root, bg="#1e2329", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="HS 斩杀助手 · 显示设置",
            fg="#e8eaed",
            bg="#1e2329",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(side="left", padx=16, pady=12)
        tk.Label(
            header,
            text=str(self.settings_path.name),
            fg="#8a9199",
            bg="#1e2329",
            font=("Consolas", 9),
        ).pack(side="right", padx=(0, 4))
        close_btn = tk.Label(
            header,
            text="×",
            fg="#c5c9ce",
            bg="#1e2329",
            font=("Segoe UI", 16),
            cursor="hand2",
            width=2,
        )
        close_btn.pack(side="right", padx=(0, 8), pady=8)
        close_btn.bind("<Button-1>", lambda _e: self.root.destroy() if self.root else None)
        close_btn.bind("<Enter>", lambda _e: close_btn.configure(fg="#ffffff", bg="#3a4048"))
        close_btn.bind("<Leave>", lambda _e: close_btn.configure(fg="#c5c9ce", bg="#1e2329"))

        body = ttk.Frame(self.root, padding=12)
        body.pack(fill="both", expand=True)

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)

        self._build_appearance_tab(notebook)
        self._build_content_tab(notebook)
        self._build_window_tab(notebook)

        footer = ttk.Frame(body)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="恢复默认", command=self._reset_defaults).pack(side="left")
        ttk.Button(footer, text="取消", command=self.root.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="保存并应用", command=self._save).pack(side="right")

        self.root.mainloop()

    def _current(self) -> OverlaySettings:
        return self.store.settings

    def _bool(self, parent, key: str, label: str, row: int) -> None:
        var = tk.BooleanVar(value=getattr(self._current(), key))
        self._vars[key] = var
        ttk.Checkbutton(parent, text=label, variable=var).grid(
            row=row, column=0, sticky="w", pady=4,
        )

    def _choice(self, parent, key: str, label: str, choices, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(8, 2))
        var = tk.StringVar(value=getattr(self._current(), key))
        self._vars[key] = var
        cb = ttk.Combobox(parent, textvariable=var, values=choices, state="readonly", width=28)
        cb.grid(row=row + 1, column=0, sticky="we", pady=(0, 4))

    def _scale(self, parent, key: str, label: str, from_, to_, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(8, 0))
        var = tk.IntVar(value=int(getattr(self._current(), key)))
        self._vars[key] = var
        scale = ttk.Scale(
            parent, from_=from_, to=to_, orient="horizontal",
            command=lambda v: var.set(int(float(v))),
        )
        scale.set(var.get())
        scale.grid(row=row + 1, column=0, sticky="we")
        val_lbl = ttk.Label(parent, text=str(var.get()))
        val_lbl.grid(row=row + 2, column=0, sticky="w")

        def _sync(_=None):
            val_lbl.configure(text=str(var.get()))

        var.trace_add("write", lambda *_: _sync())
        self._vars[f"{key}__scale"] = scale

    def _build_appearance_tab(self, notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="外观")
        tab.columnconfigure(0, weight=1)

        self._choice(tab, "theme", "配色主题", ("dark", "light", "transparent"), 0)
        ttk.Label(
            tab,
            text="dark=深色专业风  light=浅色  transparent=半透明（需独立浮层）",
            foreground="#666",
        ).grid(row=3, column=0, sticky="w")

        self._scale(tab, "opacity", "不透明度（半透明模式）", 80, 255, 4)
        self._scale(tab, "scale_percent", "字体缩放 (%)", 75, 150, 8)

        ttk.Label(tab, text="标题栏文字").grid(row=12, column=0, sticky="w", pady=(8, 2))
        title_var = tk.StringVar(value=self._current().app_title)
        self._vars["app_title"] = title_var
        ttk.Entry(tab, textvariable=title_var, width=32).grid(row=13, column=0, sticky="we")

        self._bool(tab, "show_header", "显示顶部标题栏", 14)
        self._bool(tab, "show_border", "显示顶部 accent 色条", 15)

    def _build_content_tab(self, notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="显示内容")
        tab.columnconfigure(0, weight=1)

        ttk.Label(tab, text="主 Overlay", font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0, column=0, sticky="w",
        )
        self._bool(tab, "show_breakdown", "场攻行显示分项（随/法/技…）", 1)
        self._bool(tab, "show_spell_detail", "显示法术/纯随说明行", 2)
        self._bool(tab, "show_calc_time", "显示计算耗时", 3)
        self._bool(tab, "show_taunt_line", "显示嘲讽数量", 4)
        self._bool(tab, "show_hp_line", "显示双方血量行", 5)
        self._bool(tab, "show_threat_line", "显示敌方威胁/敌斩提示", 6)
        self._bool(tab, "show_lethal_diff", "显示斩杀差值行", 7)
        self._bool(tab, "compact_mode", "紧凑模式（合并部分行）", 8)

        ttk.Separator(tab, orient="horizontal").grid(row=9, column=0, sticky="we", pady=10)
        ttk.Label(tab, text="斩杀步骤窗", font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=10, column=0, sticky="w",
        )
        self._bool(tab, "show_combo_overlay", "有斩杀时显示步骤浮层", 11)

    def _build_window_tab(self, notebook) -> None:
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="窗口")
        tab.columnconfigure(0, weight=1)

        self._bool(tab, "attach_to_game", "嵌入炉石窗口（全屏常看不见，录屏才建议开）", 0)
        self._bool(tab, "use_layered", "半透明 Layered 窗口", 1)
        ttk.Label(
            tab,
            text="嵌入模式下会自动使用不透明绘制以保证录屏可见。",
            foreground="#666",
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))

        self._scale(tab, "offset_x", "相对游戏窗口 X 偏移", 0, 400, 3)
        self._scale(tab, "offset_y", "相对游戏窗口 Y 偏移", 0, 300, 7)
        self._scale(tab, "refresh_ms", "刷新间隔 (ms)", 200, 1500, 11)
        ttk.Label(tab, text="控制台刷新 (秒)").grid(row=15, column=0, sticky="w", pady=(8, 0))
        console_var = tk.IntVar(value=int(round(self._current().console_refresh_sec * 10)))
        self._vars["console_refresh_sec"] = console_var
        console_scale = ttk.Scale(
            tab, from_=5, to=100, orient="horizontal",
            command=lambda v: console_var.set(int(float(v))),
        )
        console_scale.set(console_var.get())
        console_scale.grid(row=16, column=0, sticky="we")
        console_lbl = ttk.Label(tab, text=f"{console_var.get() / 10:.1f}s")
        console_lbl.grid(row=17, column=0, sticky="w")

        def _sync_console(*_):
            console_lbl.configure(text=f"{console_var.get() / 10:.1f}s")

        console_var.trace_add("write", lambda *_: _sync_console())

    def _collect(self) -> OverlaySettings:
        data = {}
        for key, var in self._vars.items():
            if key.endswith("__scale"):
                continue
            val = var.get()
            if key == "console_refresh_sec":
                data[key] = float(val) / 10.0
            elif key in ("opacity", "scale_percent", "offset_x", "offset_y", "refresh_ms"):
                data[key] = int(val)
            else:
                data[key] = val
        base = self.store.settings.to_dict()
        base.update(data)
        return OverlaySettings.from_dict(base)

    def _reset_defaults(self) -> None:
        if not messagebox.askyesno("恢复默认", "确定恢复全部 Overlay 设置为默认值？"):
            return
        self.store.save(OverlaySettings())
        if self.root:
            self.root.destroy()
        self.run()

    def _save(self) -> None:
        settings = self._collect()
        self.store.save(settings)
        if self.on_apply:
            self.on_apply(settings)
        messagebox.showinfo("已保存", f"设置已写入\n{self.settings_path}")
        if self.root:
            self.root.destroy()


def open_settings_dialog(
    store: Optional[OverlaySettingsStore] = None,
    *,
    on_apply: Optional[Callable[[OverlaySettings], None]] = None,
) -> None:
    store = store or OverlaySettingsStore()
    store.load()
    OverlaySettingsWindow(store, on_apply=on_apply).run()


_settings_dialog_lock = threading.Lock()
_settings_dialog_open = False


def open_settings_dialog_async(
    store: Optional[OverlaySettingsStore] = None,
    *,
    on_apply: Optional[Callable[[OverlaySettings], None]] = None,
) -> bool:
    """在后台线程打开设置窗，避免阻塞 overlay / 追踪主循环。"""
    global _settings_dialog_open
    with _settings_dialog_lock:
        if _settings_dialog_open:
            return False
        _settings_dialog_open = True

    def _run() -> None:
        global _settings_dialog_open
        try:
            open_settings_dialog(store, on_apply=on_apply)
        finally:
            with _settings_dialog_lock:
                _settings_dialog_open = False

    threading.Thread(target=_run, name="OverlaySettingsUI", daemon=True).start()
    return True
