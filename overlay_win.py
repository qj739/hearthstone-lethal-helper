# overlay_win.py — 可拖动 Overlay（支持强显直绘 / 半透明 Layered）
# 用法：
#   from overlay_win import Overlay
#   overlay = Overlay(title_hint="炉石传说", use_layered=False, opacity=220)
#   overlay.start()
#   overlay.set_text("等待数据…")
#   # 鼠标按住窗口任意位置拖动；拖动后不再跟随炉石窗口
#   overlay.reset_follow_game_window()  # 可选：恢复跟随炉石窗口
#   overlay.stop()
# 说明：
#   - 默认中文标题（炉石传说）。如用英文客户端，请改成 title_hint="Hearthstone"。
#   - 初次调试建议 use_layered=False（白底黑字，必可见）。确认可见后可改为 True 走半透明 Layered。
#   - 默认 attach_to_game=True：Overlay 作为炉石子窗口，便于 Win+G / Xbox 录游戏时一并录入。
#   - 若需 HDT 同款独立置顶窗，传 attach_to_game=False 或启动时加 --float-overlay。

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import math
import re
import threading
import time
from typing import Optional, Tuple

user32 = ctypes.windll.user32
gdi32  = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# ---- 指针宽度 & 类型兜底 ----
PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)
HWND      = getattr(wt, 'HWND', ctypes.c_void_p)
UINT      = getattr(wt, 'UINT', ctypes.c_uint)
BYTE      = getattr(wt, 'BYTE', ctypes.c_ubyte)
WORD      = getattr(wt, 'WORD', ctypes.c_ushort)
DWORD     = getattr(wt, 'DWORD', ctypes.c_uint32)
LONG_PTR  = ctypes.c_long if PTR_SIZE == 4 else ctypes.c_longlong
UINT_PTR  = ctypes.c_ulong if PTR_SIZE == 4 else ctypes.c_ulonglong
WPARAM    = getattr(wt, 'WPARAM', UINT_PTR)
LPARAM    = getattr(wt, 'LPARAM', LONG_PTR)
HCURSOR   = getattr(wt, 'HCURSOR', getattr(wt, 'HANDLE', ctypes.c_void_p))
ATOM      = getattr(wt, 'ATOM', WORD)
BOOL      = getattr(wt, 'BOOL', ctypes.c_int)
HMODULE   = getattr(wt, 'HMODULE', getattr(wt, 'HANDLE', ctypes.c_void_p))
HBRUSH    = getattr(wt, 'HBRUSH', getattr(wt, 'HANDLE', ctypes.c_void_p))
HICON     = getattr(wt, 'HICON', getattr(wt, 'HANDLE', ctypes.c_void_p))
LPCWSTR   = getattr(wt, 'LPCWSTR', ctypes.c_wchar_p)
HDC       = getattr(wt, 'HDC', getattr(wt, 'HANDLE', ctypes.c_void_p))
HGDIOBJ   = getattr(wt, 'HGDIOBJ', ctypes.c_void_p)
HFONT     = getattr(wt, 'HFONT', HGDIOBJ)
HBITMAP   = getattr(wt, 'HBITMAP', HGDIOBJ)
LRESULT   = getattr(wt, 'LRESULT', ctypes.c_long if PTR_SIZE == 4 else ctypes.c_longlong)

# ---- 结构体 ----
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", BYTE),
        ("BlendFlags", BYTE),
        ("SourceConstantAlpha", BYTE),
        ("AlphaFormat", BYTE),
    ]

class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("style", UINT),
        ("lpfnWndProc", ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HMODULE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
        ("hIconSm", HICON),
    ]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT),
    ]

# ---- WinAPI 签名 ----
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
user32.DefWindowProcW.restype  = LRESULT
user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
user32.RegisterClassExW.restype  = ATOM
user32.RegisterClassExW.argtypes = [ctypes.c_void_p]
user32.CreateWindowExW.restype  = HWND
user32.CreateWindowExW.argtypes = [DWORD, LPCWSTR, LPCWSTR, DWORD,
                                  ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  HWND, HWND, HMODULE, ctypes.c_void_p]
user32.FindWindowW.restype  = HWND
user32.FindWindowW.argtypes = [LPCWSTR, LPCWSTR]
user32.GetWindowRect.restype  = BOOL
user32.GetWindowRect.argtypes = [HWND, ctypes.c_void_p]
user32.GetClientRect.restype = BOOL
user32.GetClientRect.argtypes = [HWND, ctypes.c_void_p]
user32.ScreenToClient.restype = BOOL
user32.ScreenToClient.argtypes = [HWND, ctypes.POINTER(POINT)]
user32.ClientToScreen.restype = BOOL
user32.ClientToScreen.argtypes = [HWND, ctypes.POINTER(POINT)]
user32.IsWindowVisible.restype = BOOL
user32.IsWindowVisible.argtypes = [HWND]
user32.IsIconic.restype = BOOL
user32.IsIconic.argtypes = [HWND]
user32.ShowWindow.restype = BOOL
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.UpdateLayeredWindow.restype  = BOOL
user32.UpdateLayeredWindow.argtypes = [HWND, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, DWORD, ctypes.c_void_p, DWORD]
user32.SetWindowPos.restype  = BOOL
user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, UINT]
user32.SetParent.restype = HWND
user32.SetParent.argtypes = [HWND, HWND]
user32.LoadCursorW.restype  = HCURSOR
user32.LoadCursorW.argtypes = [HWND, ctypes.c_int]
# FillRect 在 user32.dll（第一个参数为 HDC）
user32.FillRect.restype  = BOOL
user32.FillRect.argtypes = [HDC, ctypes.POINTER(RECT), HBRUSH]
# DrawTextW 在 user32.dll
user32.DrawTextW.restype  = ctypes.c_int
user32.DrawTextW.argtypes = [HDC, LPCWSTR, ctypes.c_int, ctypes.POINTER(RECT), UINT]
gdi32.CreateFontW.restype = HFONT
gdi32.CreateFontW.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCWSTR,
]
gdi32.SelectObject.restype = HGDIOBJ
gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
gdi32.GetStockObject.restype = HGDIOBJ
gdi32.GetStockObject.argtypes = [ctypes.c_int]
gdi32.CreateSolidBrush.restype = HBRUSH
gdi32.CreateSolidBrush.argtypes = [DWORD]
gdi32.SetBkMode.restype = ctypes.c_int
gdi32.SetBkMode.argtypes = [HDC, ctypes.c_int]
gdi32.SetTextColor.restype = DWORD
gdi32.SetTextColor.argtypes = [HDC, DWORD]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateCompatibleBitmap.restype = HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [HDC, ctypes.c_int, ctypes.c_int]
gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.CreatePen.restype = ctypes.c_void_p
gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, DWORD]
gdi32.Ellipse.restype = BOOL
gdi32.Ellipse.argtypes = [HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.MoveToEx.restype = BOOL
gdi32.MoveToEx.argtypes = [HDC, ctypes.c_int, ctypes.c_int, ctypes.POINTER(POINT)]
gdi32.LineTo.restype = BOOL
gdi32.LineTo.argtypes = [HDC, ctypes.c_int, ctypes.c_int]
gdi32.Polygon.restype = BOOL
gdi32.Polygon.argtypes = [HDC, ctypes.POINTER(POINT), ctypes.c_int]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.StretchBlt.restype = BOOL
gdi32.StretchBlt.argtypes = [
    HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, DWORD,
]
gdi32.SetStretchBltMode.restype = ctypes.c_int
gdi32.SetStretchBltMode.argtypes = [HDC, ctypes.c_int]
gdi32.SetBrushOrgEx.restype = BOOL
gdi32.SetBrushOrgEx.argtypes = [HDC, ctypes.c_int, ctypes.c_int, ctypes.POINTER(POINT)]
gdi32.CreateDIBSection.restype = HBITMAP
gdi32.CreateDIBSection.argtypes = [
    HDC, ctypes.c_void_p, UINT, ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_void_p, DWORD,
]
gdi32.BitBlt.restype = BOOL
gdi32.BitBlt.argtypes = [
    HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    HDC, ctypes.c_int, ctypes.c_int, DWORD,
]
gdi32.GetTextExtentPoint32W.restype = BOOL
gdi32.GetTextExtentPoint32W.argtypes = [HDC, LPCWSTR, ctypes.c_int, ctypes.POINTER(SIZE)]
user32.GetDC.restype = HDC
user32.GetDC.argtypes = [HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [HWND, HDC]
user32.GetCursorPos.restype = BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]

kernel32.GetLastError.restype = DWORD

# SetWindowLongPtrW / GetWindowLongPtrW（兼容旧版）
try:
    GetWindowLongPtrW = user32.GetWindowLongPtrW
    SetWindowLongPtrW = user32.SetWindowLongPtrW
except AttributeError:
    GetWindowLongPtrW = user32.GetWindowLongW
    SetWindowLongPtrW = user32.SetWindowLongW
GetWindowLongPtrW.restype  = LONG_PTR
GetWindowLongPtrW.argtypes = [HWND, ctypes.c_int]
SetWindowLongPtrW.restype  = LONG_PTR
SetWindowLongPtrW.argtypes = [HWND, ctypes.c_int, LONG_PTR]

# SetLayeredWindowAttributes（可选）
try:
    SetLayeredWindowAttributes = user32.SetLayeredWindowAttributes
    SetLayeredWindowAttributes.restype  = BOOL
    SetLayeredWindowAttributes.argtypes = [HWND, DWORD, BYTE, DWORD]
except Exception:
    SetLayeredWindowAttributes = None

# ---- 常量 ----
WS_EX_LAYERED      = 0x00080000
WS_EX_TRANSPARENT  = 0x00000020
WS_EX_TOOLWINDOW   = 0x00000080
WS_EX_NOACTIVATE   = 0x08000000
WS_EX_TOPMOST      = 0x00000008
WS_POPUP           = 0x80000000
WS_CHILD           = 0x40000000
WS_VISIBLE         = 0x10000000
GWL_STYLE          = -16
HWND_TOP           = 0
HWND_TOPMOST       = -1  # 独立顶层窗口叠在炉石 HWND 之上（float 模式）
SM_XVIRTUALSCREEN  = 76
SM_YVIRTUALSCREEN  = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
SWP_NOSIZE         = 0x0001
SWP_NOMOVE         = 0x0002
SWP_NOACTIVATE     = 0x0010
SWP_SHOWWINDOW     = 0x0040
ULW_ALPHA          = 0x00000002
DT_LEFT            = 0x00000000
DT_TOP             = 0x00000000
DT_SINGLELINE      = 0x00000020
DT_NOCLIP          = 0x00000100
FW_BOLD            = 700
FW_NORMAL          = 400
DEFAULT_CHARSET    = 1
CLEARTYPE_QUALITY  = 5
WM_CLOSE           = 0x0010
WM_DESTROY         = 0x0002
WM_NCHITTEST       = 0x0084
WM_SETCURSOR       = 0x0020
WM_LBUTTONUP       = 0x0202
WM_ENTERSIZEMOVE   = 0x0231
WM_EXITSIZEMOVE    = 0x0232
CS_VREDRAW         = 0x0001
CS_HREDRAW         = 0x0002
GWL_EXSTYLE        = -20
LWA_ALPHA          = 0x00000002
IDC_ARROW          = 32512
IDC_HAND           = 32649
IDC_SIZEALL        = 32646
HTCLIENT           = 1
HTCAPTION          = 2
SW_SHOWNA          = 8
SW_HIDE            = 0
SW_RESTORE         = 9
HALFTONE           = 4
SRCCOPY            = 0x00CC0020
_SETTINGS_ICON_SS  = 5  # 超采样倍数，接近 Cursor 矢量清晰度

# 炉石未启动/最小化时，overlay 固定显示在屏幕可见区域（避免贴到 -32000 等不可见坐标）
_FALLBACK_X = 50
_FALLBACK_Y = 50
# 相对炉石窗口左上角的默认偏移（未手动拖动时跟随游戏窗口）
_DEFAULT_OFFSET_X = 100
_DEFAULT_OFFSET_Y = 20

# DPI 适配（失败忽略）
try:
    user32.SetProcessDPIAware()
except Exception:
    pass

# COLORREF（RGB -> COLORREF）
def RGB(r: int, g: int, b: int) -> int:
    return (b << 16) | (g << 8) | r

class Overlay:
    THEME_NORMAL = "normal"
    THEME_MY_LETHAL = "my_lethal"
    THEME_OPP_LETHAL = "opp_lethal"
    THEME_DARK = "dark"
    THEME_LIGHT = "light"
    THEME_TRANSPARENT = "transparent"

    _THEMES = {
        THEME_NORMAL: {"bg": (255, 255, 255), "fg": (0, 0, 0)},
        THEME_MY_LETHAL: {"bg": (210, 45, 45), "fg": (255, 255, 255)},
        THEME_OPP_LETHAL: {"bg": (160, 30, 30), "fg": (255, 255, 255)},
        THEME_DARK: {"bg": (28, 32, 38), "fg": (230, 235, 240)},
        THEME_LIGHT: {"bg": (248, 249, 251), "fg": (24, 28, 32)},
        THEME_TRANSPARENT: {"bg": (18, 20, 24), "fg": (220, 225, 230)},
    }
    _ACCENT_DEFAULT = (0, 168, 255)

    _LETHAL_BG_FULL = (210, 45, 45)
    _LETHAL_FG_FULL = (255, 255, 255)
    _LETHAL_BG_NONE = (255, 255, 255)
    _LETHAL_FG_NONE = (0, 0, 0)

    @classmethod
    def lethal_colors_for_prob(cls, prob: float, *, base_bg=None, base_fg=None) -> dict:
        """
        概率斩杀配色：prob=0 用 base 底色，prob=1 满饱和度红底白字，中间线性插值。
        """
        if base_bg is None:
            base_bg = cls._LETHAL_BG_NONE
        if base_fg is None:
            base_fg = cls._LETHAL_FG_NONE
        t = max(0.0, min(1.0, float(prob)))
        bg = tuple(
            int(base_bg[i] + (cls._LETHAL_BG_FULL[i] - base_bg[i]) * t)
            for i in range(3)
        )
        fg = tuple(
            int(base_fg[i] + (cls._LETHAL_FG_FULL[i] - base_fg[i]) * t)
            for i in range(3)
        )
        return {"bg": bg, "fg": fg}

    def lethal_colors_for_prob_on_base(self, prob: float) -> dict:
        """按当前 base 主题做概率斩杀渐变（深色主题下低概率也会偏红）。"""
        base = self._THEMES.get(self._base_theme, self._THEMES[self.THEME_DARK])
        return self.lethal_colors_for_prob(
            prob, base_bg=base["bg"], base_fg=base["fg"],
        )

    def _resolve_display_colors(self, theme: str, custom_colors, hs_detected: bool):
        if custom_colors:
            return custom_colors["bg"], custom_colors["fg"]
        active = theme if hs_detected else self._base_theme
        if active in (self.THEME_MY_LETHAL, self.THEME_OPP_LETHAL):
            colors = self._THEMES[active]
            return colors["bg"], colors["fg"]
        if active == self.THEME_NORMAL:
            active = self._base_theme
        colors = self._THEMES.get(active, self._THEMES[self.THEME_DARK])
        return colors["bg"], colors["fg"]

    def __init__(
        self,
        title_hint: str = "炉石传说",
        use_layered: bool = False,
        opacity: int = 220,
        *,
        attach_to_game: bool = True,
    ):
        self.title_hint = title_hint
        self.attach_to_game = bool(attach_to_game)
        if self.attach_to_game and use_layered:
            # 子窗口 + 分层透明不利于 Win+G 录屏，自动退回白底直绘
            use_layered = False
        self.use_layered = bool(use_layered)
        self.opacity = max(0, min(255, int(opacity)))
        self._game_parent_hwnd = None
        self.hwnd = None
        self.hInstance = kernel32.GetModuleHandleW(None)
        # 每个进程独立类名，避免多次启动/调试残留导致 RegisterClass 冲突
        self.className = f"HSOverlayClassPy_{kernel32.GetCurrentProcessId()}"
        self.stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._create_failed = False
        self._last_error = ""
        self.thread = None
        self._text_lock = threading.Lock()
        self._pos_lock = threading.Lock()
        self._text = ""
        self._theme = self.THEME_NORMAL
        self._custom_colors = None
        self._user_positioned = False  # 用户拖动后不再跟随炉石窗口
        # 强显直绘模式尺寸（宽度过短会裁切「场攻+法术+嘲讽」长行）
        self._fixed_w = 420
        self._fixed_h = 210
        self._min_w = 420
        self._max_w = 720
        self._pad_x = 16
        self._pad_y = 12
        self._line_gap = 6
        # 持久化 WNDPROC，防止 GC
        self._wndproc_c = WNDPROC(self._wndproc)
        self._custom_fonts = []
        self._scale_percent = 100
        self._offset_x = _DEFAULT_OFFSET_X
        self._offset_y = _DEFAULT_OFFSET_Y
        self._refresh_sec = 0.5
        self._show_border = True
        self._show_header = True
        self._header_text = "HS 斩杀助手"
        self._show_menu_bar = True
        self._on_settings = None
        self._on_close = None
        self._user_closed = False
        self._settings_btn_rect = (0, 0, 0, 0)
        self._close_btn_rect = (0, 0, 0, 0)
        self._menu_bar_rect = (0, 0, 0, 0)
        self._base_theme = self.THEME_DARK
        self._accent_rgb = self._ACCENT_DEFAULT
        self._fonts = self._create_fonts()

    def apply_settings(self, settings) -> None:
        """从 OverlaySettings 应用外观与窗口参数（可运行时热更新）。"""
        theme_map = {
            "dark": self.THEME_DARK,
            "light": self.THEME_LIGHT,
            "transparent": self.THEME_TRANSPARENT,
        }
        with self._text_lock:
            self._scale_percent = max(75, min(150, int(getattr(settings, "scale_percent", 100))))
            self._offset_x = max(0, int(getattr(settings, "offset_x", _DEFAULT_OFFSET_X)))
            self._offset_y = max(0, int(getattr(settings, "offset_y", _DEFAULT_OFFSET_Y)))
            self._refresh_sec = max(0.2, int(getattr(settings, "refresh_ms", 500)) / 1000.0)
            self._show_border = bool(getattr(settings, "show_border", True))
            self._show_header = bool(getattr(settings, "show_header", True))
            self._header_text = (getattr(settings, "app_title", "") or "HS 斩杀助手").strip()
            self.opacity = max(80, min(255, int(getattr(settings, "opacity", self.opacity))))
            self.use_layered = bool(getattr(settings, "use_layered", self.use_layered))
            self.attach_to_game = bool(getattr(settings, "attach_to_game", self.attach_to_game))
            self._base_theme = theme_map.get(getattr(settings, "theme", "dark"), self.THEME_DARK)
        self._destroy_fonts()
        self._fonts = self._create_fonts()
        if self.use_layered and self.hwnd:
            self._enable_layered()

    def set_action_callbacks(
        self,
        *,
        on_settings=None,
        on_close=None,
    ) -> None:
        """菜单栏「设置」与右上角关闭按钮回调（在 overlay 消息线程触发）。"""
        self._on_settings = on_settings
        self._on_close = on_close

    @property
    def is_user_closed(self) -> bool:
        return self._user_closed

    def hide(self) -> None:
        """隐藏浮层（不退出追踪主程序）。"""
        self._user_closed = True
        if self.hwnd:
            user32.ShowWindow(self.hwnd, SW_HIDE)

    def show(self) -> None:
        """重新显示被用户关闭的浮层。"""
        self._user_closed = False

    def _menu_bar_h(self) -> int:
        return self._scaled(28) if self._show_menu_bar else 0

    def _chrome_top(self) -> int:
        return 3 if self._show_border else 0

    def _update_chrome_layout(self, w: int) -> None:
        if not self._show_menu_bar:
            self._menu_bar_rect = (0, 0, 0, 0)
            self._settings_btn_rect = (0, 0, 0, 0)
            self._close_btn_rect = (0, 0, 0, 0)
            return
        top = self._chrome_top()
        bar_h = self._menu_bar_h()
        close_size = self._scaled(26)
        settings_size = self._scaled(26)
        gap = self._scaled(4)
        right_pad = self._scaled(6)
        close_right = w - right_pad
        close_left = close_right - close_size
        settings_right = close_left - gap
        settings_left = settings_right - settings_size
        self._menu_bar_rect = (0, top, w, top + bar_h)
        self._close_btn_rect = (close_left, top + 2, close_right, top + bar_h - 2)
        self._settings_btn_rect = (settings_left, top + 2, settings_right, top + bar_h - 2)

    @staticmethod
    def _point_in_rect(x: int, y: int, rect: Tuple[int, int, int, int]) -> bool:
        left, top, right, bottom = rect
        return left <= x < right and top <= y < bottom

    def _screen_point_to_client(self, hwnd, lparam) -> Tuple[int, int]:
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        pt = POINT(x, y)
        user32.ScreenToClient(hwnd, ctypes.byref(pt))
        return pt.x, pt.y

    def _client_point(self, lparam) -> Tuple[int, int]:
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        return x, y

    def _chrome_button_at(self, x: int, y: int) -> Optional[str]:
        if self._point_in_rect(x, y, self._close_btn_rect):
            return "close"
        if self._point_in_rect(x, y, self._settings_btn_rect):
            return "settings"
        return None

    def _invoke_settings(self) -> None:
        cb = self._on_settings
        if cb:
            cb()

    def _invoke_close(self) -> None:
        self.hide()
        cb = self._on_close
        if cb:
            cb()

    def _scaled(self, px: int) -> int:
        return max(8, int(px * self._scale_percent / 100))

    def _create_font(self, height: int, bold: bool = False):
        weight = FW_BOLD if bold else FW_NORMAL
        face = "Microsoft YaHei UI" if bold else "Microsoft YaHei"
        font = gdi32.CreateFontW(
            self._scaled(height), 0, 0, 0, weight,
            0, 0, 0, DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, face,
        )
        if not font:
            return gdi32.GetStockObject(17)
        self._custom_fonts.append(font)
        return font

    def _create_fonts(self):
        return {
            "board": self._create_font(48, bold=True),
            "info": self._create_font(22),
            "damage": self._create_font(24),
            "damage_num": self._create_font(34, bold=True),
            "lethal": self._create_font(30, bold=True),
            "lethal_num": self._create_font(58, bold=True),
        }

    def _destroy_fonts(self):
        for font in self._custom_fonts:
            gdi32.DeleteObject(font)
        self._custom_fonts = []
        self._fonts = {}

    def _text_extent(self, hdc, font, text: str):
        gdi32.SelectObject(hdc, font)
        size = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(size))
        return size.cx, size.cy

    def _draw_text_at(self, hdc, font, text: str, x: int, y: int, color: int):
        if not text:
            return 0, 0
        gdi32.SelectObject(hdc, font)
        gdi32.SetBkMode(hdc, 1)
        gdi32.SetTextColor(hdc, color)
        _, h = self._text_extent(hdc, font, text)
        rc = RECT(x, y, x + 4000, y + h + 8)
        user32.DrawTextW(hdc, text, -1, ctypes.byref(rc), DT_LEFT | DT_TOP | DT_SINGLELINE | DT_NOCLIP)
        w, _ = self._text_extent(hdc, font, text)
        return w, h

    def _draw_segments(self, hdc, segments, x: int, y: int, color: int, default_color: int):
        cx = x
        max_h = 0
        for text, font_key in segments:
            if not text:
                continue
            font = self._fonts[font_key]
            w, h = self._draw_text_at(hdc, font, text, cx, y, color if font_key.startswith("lethal") else default_color)
            cx += w
            max_h = max(max_h, h)
        return cx - x, max_h

    def _draw_damage_line(self, hdc, line: str, x: int, y: int, color: int):
        m = re.match(r"总伤害:\s*(\d+)\s*/\s*(\d+)\s*\(还差(\d+)\)", line)
        if m:
            total, opp, diff = m.groups()
            _, h = self._draw_segments(
                hdc,
                [
                    ("总伤害: ", "damage"),
                    (total, "damage_num"),
                    (" / ", "damage"),
                    (opp, "damage_num"),
                    (f"  (还差{diff})", "damage"),
                ],
                x,
                y,
                color,
                color,
            )
            return h
        m = re.match(r"(?:下回合 )?(\d+)/(\d+) 差(\d+)", line)
        if m:
            total, opp, diff = m.groups()
            prefix = "下回合 " if line.startswith("下回合") else ""
            _, h = self._draw_segments(
                hdc,
                [
                    (prefix, "damage"),
                    (total, "damage_num"),
                    ("/", "damage"),
                    (opp, "damage_num"),
                    (f" 差{diff}", "damage"),
                ],
                x,
                y,
                color,
                color,
            )
            return h
        return self._draw_text_at(hdc, self._fonts["damage"], line, x, y, color)[1]

    def _lethal_line_segments(self, line: str):
        m = re.match(r"⚔️\s*斩杀！总伤\s*(\d+)\s*>=\s*(\d+)\s*⚔️", line)
        if m:
            total, opp = m.groups()
            return [
                ("⚔️ 斩杀！总伤 ", "lethal"),
                (total, "lethal_num"),
                (" >= ", "lethal"),
                (opp, "lethal_num"),
                (" ⚔️", "lethal"),
            ]
        m = re.match(r"⚔️\s*(?:下回合)?斩(?:杀)?\s*(\d+)≥(\d+)", line)
        if m:
            total, opp = m.groups()
            label = "⚔️ 下回合斩 " if "下回合" in line else "⚔️ 斩杀 "
            return [
                (label, "lethal"),
                (total, "lethal_num"),
                ("≥", "lethal"),
                (opp, "lethal_num"),
            ]
        return None

    def _measure_damage_line(self, hdc, line: str) -> Tuple[int, int]:
        m = re.match(r"总伤害:\s*(\d+)\s*/\s*(\d+)\s*\(还差(\d+)\)", line)
        if m:
            total, opp, diff = m.groups()
            return self._measure_segments(
                hdc,
                [
                    ("总伤害: ", "damage"),
                    (total, "damage_num"),
                    (" / ", "damage"),
                    (opp, "damage_num"),
                    (f"  (还差{diff})", "damage"),
                ],
            )
        m = re.match(r"(?:下回合 )?(\d+)/(\d+) 差(\d+)", line)
        if m:
            total, opp, diff = m.groups()
            prefix = "下回合 " if line.startswith("下回合") else ""
            return self._measure_segments(
                hdc,
                [
                    (prefix, "damage"),
                    (total, "damage_num"),
                    ("/", "damage"),
                    (opp, "damage_num"),
                    (f" 差{diff}", "damage"),
                ],
            )
        return self._text_extent(hdc, self._fonts["damage"], line)

    def _measure_segments(self, hdc, segments) -> Tuple[int, int]:
        width = 0
        height = 0
        for text, font_key in segments:
            if not text:
                continue
            w, h = self._text_extent(hdc, self._fonts[font_key], text)
            width += w
            height = max(height, h)
        return width, height

    def _measure_line(self, hdc, line: str, line_index: int) -> Tuple[int, int]:
        if not line:
            return 0, 0
        if line_index == 0:
            return self._text_extent(hdc, self._fonts["board"], line)
        if line_index == 1:
            return self._text_extent(hdc, self._fonts["info"], line)
        if "斩杀" in line or line.startswith("⚔️"):
            segments = self._lethal_line_segments(line)
            if segments:
                return self._measure_segments(hdc, segments)
            return self._text_extent(hdc, self._fonts["lethal"], line)
        return self._measure_damage_line(hdc, line)

    def _draw_lethal_line(self, hdc, line: str, x: int, y: int, color: int):
        segments = self._lethal_line_segments(line)
        if segments:
            _, h = self._draw_segments(hdc, segments, x, y, color, color)
            return h
        return self._draw_text_at(hdc, self._fonts["lethal"], line, x, y, color)[1]

    def _cursor_gear_points(
        self,
        cx: float,
        cy: float,
        half: float,
        *,
        teeth: int = 6,
    ) -> Tuple[Tuple[float, float], ...]:
        """Cursor codicon 风格齿轮：圆角齿、细线框、中心留空。"""
        points: list[Tuple[float, float]] = []
        for i in range(teeth):
            base = (2.0 * math.pi * i / teeth) - (math.pi / 2.0)
            span = math.pi / teeth
            r_outer = half * 0.90
            r_inner = half * 0.64
            for angle, radius in (
                (base - span * 0.95, r_inner),
                (base - span * 0.45, r_outer),
                (base - span * 0.12, r_outer),
                (base + span * 0.12, r_outer),
                (base + span * 0.45, r_outer),
                (base + span * 0.95, r_inner),
            ):
                points.append((
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius,
                ))
        return tuple(points)

    def _pil_rgb_to_bgr_buffer(self, img) -> Tuple[bytes, int, int]:
        """PIL RGB -> 4 字节对齐的 BGR 行缓冲（供 DIB）。"""
        w, h = img.size
        row_bytes = ((w * 3 + 3) // 4) * 4
        buf = bytearray(row_bytes * h)
        raw = img.tobytes("raw", "BGR")
        src_stride = w * 3
        for y in range(h):
            off = y * row_bytes
            src_off = y * src_stride
            buf[off:off + src_stride] = raw[src_off:src_off + src_stride]
        return bytes(buf), w, h

    def _blit_pil_rgb(self, hdc, x: int, y: int, pil_image) -> bool:
        """将 PIL RGB 图 BitBlt 到目标 DC。"""
        try:
            from PIL import Image
        except ImportError:
            return False
        if not isinstance(pil_image, Image.Image):
            return False
        img = pil_image.convert("RGB")
        w, h = img.size
        if w <= 0 or h <= 0:
            return False

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", DWORD),
                ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long),
                ("biPlanes", WORD),
                ("biBitCount", WORD),
                ("biCompression", DWORD),
                ("biSizeImage", DWORD),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", DWORD),
                ("biClrImportant", DWORD),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER)]

        buf, bw, bh = self._pil_rgb_to_bgr_buffer(img)
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = bw
        bmi.bmiHeader.biHeight = -bh
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 24
        bmi.bmiHeader.biCompression = 0

        hdc_screen = user32.GetDC(None)
        try:
            bits = ctypes.c_void_p()
            hbmp = gdi32.CreateDIBSection(
                hdc_screen, ctypes.byref(bmi), 0,
                ctypes.byref(bits), None, 0,
            )
            if not hbmp or not bits.value:
                return False
            ctypes.memmove(bits.value, buf, len(buf))
            hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            if not hdc_mem:
                gdi32.DeleteObject(hbmp)
                return False
            old = gdi32.SelectObject(hdc_mem, hbmp)
            ok = bool(gdi32.BitBlt(hdc, x, y, w, h, hdc_mem, 0, 0, SRCCOPY))
            gdi32.SelectObject(hdc_mem, old)
            gdi32.DeleteDC(hdc_mem)
            gdi32.DeleteObject(hbmp)
            return ok
        finally:
            user32.ReleaseDC(None, hdc_screen)

    def _draw_settings_icon_pil(
        self,
        hdc,
        rect: Tuple[int, int, int, int],
        fg_rgb,
        bg_rgb,
    ) -> bool:
        """Pillow 抗锯齿渲染（优先，最接近 Cursor 清晰度）。"""
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return False

        l, t, r, b = rect
        dw, dh = max(1, r - l), max(1, b - t)
        ss = _SETTINGS_ICON_SS
        sw, sh = dw * ss, dh * ss
        img = Image.new("RGB", (sw, sh), bg_rgb)
        draw = ImageDraw.Draw(img)
        cx, cy = sw / 2.0, sh / 2.0
        half = min(sw, sh) / 2.0 - ss * 2.5
        pts = self._cursor_gear_points(cx, cy, half)
        stroke = max(2, int(round(ss * 1.25)))
        draw.line(
            list(pts) + [pts[0]],
            fill=fg_rgb,
            width=stroke,
            joint="curve",
        )
        hub_r = half * 0.34
        draw.ellipse(
            (cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r),
            fill=bg_rgb,
            outline=fg_rgb,
            width=max(1, stroke - 1),
        )
        img = img.resize((dw, dh), Image.Resampling.LANCZOS)
        return self._blit_pil_rgb(hdc, l, t, img)

    def _draw_settings_icon_gdi(
        self,
        hdc,
        rect: Tuple[int, int, int, int],
        fg_rgb,
        bg_rgb,
    ) -> None:
        """GDI 超采样 + HALFTONE 缩放（无 Pillow 时回退）。"""
        l, t, r, b = rect
        dw, dh = max(1, r - l), max(1, b - t)
        ss = _SETTINGS_ICON_SS
        sw, sh = dw * ss, dh * ss

        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, sw, sh)
        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)
        try:
            bg_brush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
            fill_rect = RECT(0, 0, sw, sh)
            user32.FillRect(hdc_mem, ctypes.byref(fill_rect), bg_brush)
            gdi32.DeleteObject(bg_brush)

            cx, cy = sw / 2.0, sh / 2.0
            half = min(sw, sh) / 2.0 - ss * 2.5
            pts_float = self._cursor_gear_points(cx, cy, half)
            pts = [POINT(int(round(x)), int(round(y))) for x, y in pts_float]
            pt_arr = (POINT * len(pts))(*pts)

            null_brush = gdi32.GetStockObject(5)
            pen_w = max(1, int(round(ss * 1.25)))
            pen = gdi32.CreatePen(0, pen_w, RGB(*fg_rgb))
            gdi32.SelectObject(hdc_mem, null_brush)
            gdi32.SelectObject(hdc_mem, pen)
            gdi32.Polygon(hdc_mem, pt_arr, len(pts))

            hub_r = int(half * 0.34)
            hub_pen = gdi32.CreatePen(0, max(1, pen_w - 1), RGB(*fg_rgb))
            hub_brush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
            gdi32.SelectObject(hdc_mem, hub_brush)
            gdi32.SelectObject(hdc_mem, hub_pen)
            gdi32.Ellipse(
                hdc_mem,
                int(cx - hub_r), int(cy - hub_r),
                int(cx + hub_r), int(cy + hub_r),
            )
            gdi32.DeleteObject(pen)
            gdi32.DeleteObject(hub_pen)
            gdi32.DeleteObject(hub_brush)

            old_mode = gdi32.SetStretchBltMode(hdc, HALFTONE)
            gdi32.SetBrushOrgEx(hdc, 0, 0, None)
            gdi32.StretchBlt(hdc, l, t, dw, dh, hdc_mem, 0, 0, sw, sh, SRCCOPY)
            gdi32.SetStretchBltMode(hdc, old_mode)
        finally:
            gdi32.SelectObject(hdc_mem, old_bmp)
            gdi32.DeleteObject(hbmp)
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(None, hdc_screen)

    def _draw_settings_icon(
        self,
        hdc,
        rect: Tuple[int, int, int, int],
        fg_rgb,
        bg_rgb,
    ) -> None:
        """菜单栏设置齿轮（Cursor 同款：高分辨率抗锯齿）。"""
        if not self._draw_settings_icon_pil(hdc, rect, fg_rgb, bg_rgb):
            self._draw_settings_icon_gdi(hdc, rect, fg_rgb, bg_rgb)

    def _draw_chrome(self, hdc, w: int, h: int, bg_rgb, fg_rgb):
        self._update_chrome_layout(w)
        if self._show_border:
            border = gdi32.CreateSolidBrush(RGB(*self._accent_rgb))
            edge = RECT(0, 0, w, 3)
            user32.FillRect(hdc, ctypes.byref(edge), border)
            gdi32.DeleteObject(border)
        if not self._show_menu_bar:
            return
        left, top, right, bottom = self._menu_bar_rect
        bar_h = bottom - top
        bar_bg = tuple(max(0, int(bg_rgb[i] * 0.82)) for i in range(3))
        bar_brush = gdi32.CreateSolidBrush(RGB(*bar_bg))
        bar_rect = RECT(left, top, right, bottom)
        user32.FillRect(hdc, ctypes.byref(bar_rect), bar_brush)
        gdi32.DeleteObject(bar_brush)

        btn_bg = tuple(
            int(bar_bg[i] * 0.75 + fg_rgb[i] * 0.25) for i in range(3)
        )
        for rect in (self._settings_btn_rect, self._close_btn_rect):
            l, t, r, b = rect
            btn_rect = RECT(l, t, r, b)
            btn_brush = gdi32.CreateSolidBrush(RGB(*btn_bg))
            user32.FillRect(hdc, ctypes.byref(btn_rect), btn_brush)
            gdi32.DeleteObject(btn_brush)

        menu_fg = RGB(*fg_rgb)
        self._draw_settings_icon(hdc, self._settings_btn_rect, fg_rgb, btn_bg)
        if self._show_header and self._header_text:
            title_w, title_h = self._text_extent(hdc, self._fonts["info"], self._header_text)
            title_right = self._settings_btn_rect[0] - self._scaled(8)
            title_x = max(self._pad_x, (title_right - title_w) // 2)
            title_y = top + max(2, (bar_h - title_h) // 2)
            muted = tuple(
                int(fg_rgb[i] * 0.65 + bg_rgb[i] * 0.35) for i in range(3)
            )
            self._draw_text_at(
                hdc, self._fonts["info"], self._header_text,
                title_x, title_y, RGB(*muted),
            )
        close_cx = (self._close_btn_rect[0] + self._close_btn_rect[2]) // 2
        close_cy = (self._close_btn_rect[1] + self._close_btn_rect[3]) // 2
        close_label = "×"
        close_w, close_h = self._text_extent(hdc, self._fonts["info"], close_label)
        self._draw_text_at(
            hdc, self._fonts["info"], close_label,
            close_cx - close_w // 2,
            close_cy - close_h // 2,
            menu_fg,
        )

    def _content_top(self) -> int:
        top = self._pad_y
        if self._show_border:
            top += 4
        if self._show_menu_bar:
            top += self._menu_bar_h()
        return top

    def _paint_text(self, hdc, text: str, w: int, h: int, color: int):
        lines = [ln for ln in (text or "").split("\n") if ln]
        y = self._content_top()
        for i, line in enumerate(lines):
            if i == 0:
                _, lh = self._draw_text_at(hdc, self._fonts["board"], line, self._pad_x, y, color)
            elif i == 1:
                _, lh = self._draw_text_at(hdc, self._fonts["info"], line, self._pad_x, y, color)
            elif "斩杀" in line or line.startswith("⚔️"):
                lh = self._draw_lethal_line(hdc, line, self._pad_x, y, color)
            else:
                lh = self._draw_damage_line(hdc, line, self._pad_x, y, color)
            y += lh + self._line_gap

    def _scaled_limit(self, base: int) -> int:
        """字体缩放时同步放宽窗口宽/高下限。"""
        return max(base, int(base * self._scale_percent / 100))

    def _measure_content_width(self, text: str) -> int:
        lines = [ln for ln in (text or "").split("\n") if ln]
        if not lines:
            return self._scaled_limit(self._min_w)
        hdc = user32.GetDC(None)
        try:
            max_w = 0
            for i, line in enumerate(lines):
                w, _ = self._measure_line(hdc, line, i)
                max_w = max(max_w, w)
            min_w = self._scaled_limit(self._min_w)
            max_w_limit = self._scaled_limit(self._max_w)
            return min(max_w_limit, max(min_w, max_w + 2 * self._pad_x))
        finally:
            user32.ReleaseDC(None, hdc)

    def _content_size(self, text: str):
        lines = [ln for ln in (text or "").split("\n") if ln]
        w = self._measure_content_width(text)
        extra_h = 0
        if self._show_border:
            extra_h += 4
        if self._show_menu_bar:
            extra_h += self._menu_bar_h()
        if not lines:
            return w, self._fixed_h + extra_h
        hdc = user32.GetDC(None)
        try:
            total_h = self._content_top() + self._pad_y
            for i, line in enumerate(lines):
                _, lh = self._measure_line(hdc, line, i)
                total_h += lh + self._line_gap
            min_h = self._scaled_limit(self._fixed_h)
            return w, max(min_h, total_h)
        finally:
            user32.ReleaseDC(None, hdc)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_NCHITTEST:
            if self._show_menu_bar:
                x, y = self._screen_point_to_client(hwnd, lparam)
                if self._chrome_button_at(x, y):
                    return HTCLIENT
            return HTCAPTION
        if msg == WM_SETCURSOR:
            hit = lparam & 0xFFFF
            if hit == HTCLIENT and self._show_menu_bar:
                pt = POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                user32.ScreenToClient(hwnd, ctypes.byref(pt))
                if self._chrome_button_at(pt.x, pt.y):
                    user32.SetCursor(user32.LoadCursorW(None, IDC_HAND))
                    return 1
            user32.SetCursor(user32.LoadCursorW(None, IDC_SIZEALL))
            return 1
        if msg == WM_LBUTTONUP:
            x, y = self._client_point(lparam)
            btn = self._chrome_button_at(x, y)
            if btn == "settings":
                self._invoke_settings()
                return 0
            if btn == "close":
                self._invoke_close()
                return 0
        if msg in (WM_ENTERSIZEMOVE, WM_EXITSIZEMOVE):
            with self._pos_lock:
                self._user_positioned = True
            return 0
        if msg == WM_CLOSE:
            self._invoke_close()
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _register_class(self):
        wcx = WNDCLASSEX()
        wcx.cbSize = ctypes.sizeof(WNDCLASSEX)
        wcx.style = CS_HREDRAW | CS_VREDRAW
        wcx.lpfnWndProc = self._wndproc_c
        wcx.cbClsExtra = 0
        wcx.cbWndExtra = 0
        wcx.hInstance = self.hInstance
        wcx.hIcon = None
        wcx.hCursor = user32.LoadCursorW(None, IDC_ARROW)
        wcx.hbrBackground = gdi32.GetStockObject(5)  # NULL_BRUSH（直绘自填充）
        wcx.lpszMenuName = None
        wcx.lpszClassName = self.className
        wcx.hIconSm = None
        atom = user32.RegisterClassExW(ctypes.byref(wcx))
        if atom == 0:
            last_err = kernel32.GetLastError()
            if last_err not in (0, 1410):  # 1410: 类已存在
                print(f"[overlay] RegisterClassExW 失败，错误码={last_err}")

    def _create_window(self):
        # 为提高成功率：先不带 layered
        exStyle = WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        hwnd = user32.CreateWindowExW(
            exStyle,
            self.className,
            "HS Overlay",
            WS_POPUP,
            100, 100, self._min_w, self._fixed_h,
            None, None, self.hInstance, None
        )
        if not hwnd:
            last_err = kernel32.GetLastError()
            self._last_error = f"CreateWindowExW 失败，错误码={last_err}"
            print(f"[overlay] {self._last_error}")
        self.hwnd = hwnd
        return hwnd

    def _enable_layered(self):
        if not self.hwnd:
            return
        old_ex = GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE)
        # 不用 WS_EX_TRANSPARENT，否则鼠标穿透无法拖动
        new_ex = old_ex | WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        SetWindowLongPtrW(self.hwnd, GWL_EXSTYLE, new_ex)
        if SetLayeredWindowAttributes:
            SetLayeredWindowAttributes(self.hwnd, 0, BYTE(self.opacity), LWA_ALPHA)

    def reset_follow_game_window(self):
        """恢复跟随炉石窗口位置（例如拖动后想贴回默认位置）。"""
        with self._pos_lock:
            self._user_positioned = False

    def _is_hs_foreground(self, hs_hwnd) -> bool:
        if not hs_hwnd:
            return False
        fg = user32.GetForegroundWindow()
        return fg == hs_hwnd or fg == self.hwnd

    def _client_rect(self, hwnd) -> RECT:
        rect = RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        return rect

    def _client_position_from_screen(self, parent_hwnd, x: int, y: int) -> Tuple[int, int]:
        pt = POINT(x, y)
        user32.ScreenToClient(parent_hwnd, ctypes.byref(pt))
        return pt.x, pt.y

    def _clamp_to_parent_client(
        self, parent_hwnd, x: int, y: int, w: int, h: int,
    ) -> Tuple[int, int]:
        client = self._client_rect(parent_hwnd)
        cw = client.right - client.left
        ch = client.bottom - client.top
        if cw <= 0 or ch <= 0:
            return x, y
        x = max(0, min(x, cw - w))
        y = max(0, min(y, ch - h))
        return x, y

    def _detach_from_game(self) -> None:
        if not self.hwnd or self._game_parent_hwnd is None:
            return
        user32.SetParent(self.hwnd, None)
        style = int(GetWindowLongPtrW(self.hwnd, GWL_STYLE))
        style = (style & ~WS_CHILD) | WS_POPUP
        SetWindowLongPtrW(self.hwnd, GWL_STYLE, style)
        ex = int(GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE))
        ex = (ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~WS_EX_TOPMOST
        SetWindowLongPtrW(self.hwnd, GWL_EXSTYLE, ex)
        self._game_parent_hwnd = None

    def _attach_to_game(self, hs_hwnd) -> bool:
        if not self.hwnd or not hs_hwnd or user32.IsIconic(hs_hwnd):
            return False
        if self._game_parent_hwnd == hs_hwnd:
            return True
        self._detach_from_game()
        style = int(GetWindowLongPtrW(self.hwnd, GWL_STYLE))
        style = (style & ~WS_POPUP) | WS_CHILD | WS_VISIBLE
        SetWindowLongPtrW(self.hwnd, GWL_STYLE, style)
        ex = int(GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE))
        ex = (ex & ~WS_EX_TOPMOST & ~WS_EX_TOOLWINDOW) | WS_EX_NOACTIVATE
        if self.use_layered:
            ex |= WS_EX_LAYERED
        SetWindowLongPtrW(self.hwnd, GWL_EXSTYLE, ex)
        user32.SetParent(self.hwnd, hs_hwnd)
        self._game_parent_hwnd = hs_hwnd
        return True

    def _sync_game_attachment(self, hs_hwnd) -> bool:
        if not self.attach_to_game:
            if self._game_parent_hwnd:
                self._detach_from_game()
            return False
        if not hs_hwnd or user32.IsIconic(hs_hwnd):
            if self._game_parent_hwnd:
                self._detach_from_game()
            return False
        return self._attach_to_game(hs_hwnd)

    def _overlay_client_position(
        self, hs_hwnd, *, content_w: int = 420, content_h: int = 210,
    ) -> Tuple[int, int]:
        """炉石客户区坐标（attach 模式）。"""
        if not hs_hwnd or user32.IsIconic(hs_hwnd):
            return self._offset_x, self._offset_y
        x = self._offset_x
        y = self._offset_y
        return self._clamp_to_parent_client(hs_hwnd, x, y, content_w, content_h)

    def _client_position_from_overlay(self, parent_hwnd) -> Tuple[int, int]:
        if not self.hwnd:
            return self._offset_x, self._offset_y
        rect = self._get_window_rect(self.hwnd)
        return self._client_position_from_screen(parent_hwnd, rect.left, rect.top)

    def _apply_window_placement(
        self, hs_hwnd, ox: int, oy: int, content_w: int, content_h: int,
    ) -> None:
        if not self.hwnd:
            return
        if self.attach_to_game and hs_hwnd and not user32.IsIconic(hs_hwnd):
            self._sync_game_attachment(hs_hwnd)
            user32.SetWindowPos(
                self.hwnd, HWND_TOP, ox, oy,
                content_w, content_h, SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
            if not user32.IsWindowVisible(self.hwnd):
                user32.ShowWindow(self.hwnd, SW_SHOWNA)
            return
        if self._game_parent_hwnd:
            self._detach_from_game()
        user32.SetWindowPos(
            self.hwnd, HWND_TOPMOST, ox, oy,
            content_w, content_h, SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
        self._ensure_shown(hs_hwnd)
        if hs_hwnd and self._is_hs_foreground(hs_hwnd):
            self._ensure_topmost(hs_hwnd)

    def _ensure_topmost(self, hs_hwnd=None):
        """float 模式：周期性用 SetWindowPos 维持 WS_EX_TOPMOST / 置顶 Z 序。"""
        if self.attach_to_game or not self.hwnd:
            return
        user32.SetWindowPos(
            self.hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
        ex = int(GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE))
        if (ex & WS_EX_TOPMOST) == 0:
            SetWindowLongPtrW(self.hwnd, GWL_EXSTYLE, ex | WS_EX_TOPMOST)

    def _clamp_to_virtual_screen(self, x: int, y: int, w: int, h: int):
        """多显示器时把窗口限制在虚拟桌面可见区域内。"""
        vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        vw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        vh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if vw <= 0 or vh <= 0:
            return x, y
        x = max(vx, min(x, vx + vw - w))
        y = max(vy, min(y, vy + vh - h))
        return x, y

    def _render_dc(self, text: str, w: int, h: int, bg_rgb, fg_rgb):
        # 非 Layered 路径：客户区直绘
        hdc = user32.GetDC(self.hwnd)
        try:
            rect = RECT(0, 0, w, h)
            hbrush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
            user32.FillRect(hdc, ctypes.byref(rect), hbrush)
            gdi32.DeleteObject(hbrush)
            self._draw_chrome(hdc, w, h, bg_rgb, fg_rgb)
            self._paint_text(hdc, text, w, h, RGB(*fg_rgb))
        finally:
            user32.ReleaseDC(self.hwnd, hdc)

    def _render_layered(self, text: str, w: int, h: int, bg_rgb, fg_rgb):
        # 半透明 Layered 路径
        hdc_screen = user32.GetDC(None)
        hdc_mem    = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp       = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        gdi32.SelectObject(hdc_mem, hbmp)
        rect = RECT(0, 0, w, h)
        hbrush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
        user32.FillRect(hdc_mem, ctypes.byref(rect), hbrush)
        gdi32.DeleteObject(hbrush)
        self._draw_chrome(hdc_mem, w, h, bg_rgb, fg_rgb)
        self._paint_text(hdc_mem, text, w, h, RGB(*fg_rgb))
        pt_src  = POINT(0, 0)
        pt_dst  = POINT(0, 0)
        size    = SIZE(w, h)
        blend   = BLENDFUNCTION(0, 0, BYTE(self.opacity), 0)
        user32.UpdateLayeredWindow(self.hwnd, hdc_screen,
                                   ctypes.byref(pt_dst), ctypes.byref(size),
                                   hdc_mem, ctypes.byref(pt_src),
                                   0, ctypes.byref(blend), ULW_ALPHA)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

    def set_text(self, text: str, *, theme: str = None, colors: dict = None):
        with self._text_lock:
            self._text = text
            if theme is not None:
                if theme in (self.THEME_NORMAL, self.THEME_MY_LETHAL, self.THEME_OPP_LETHAL):
                    self._theme = theme
                elif theme in self._THEMES:
                    self._theme = theme
                else:
                    self._theme = self._base_theme
            if colors is not None:
                self._custom_colors = colors
            elif theme is not None:
                self._custom_colors = None

    def set_theme(self, theme: str):
        with self._text_lock:
            self._theme = theme if theme in self._THEMES else self.THEME_NORMAL

    @property
    def is_ready(self) -> bool:
        return bool(self.hwnd) and not self._create_failed

    def start(self, *, wait_ready: float = 3.0) -> bool:
        """启动 overlay 线程；wait_ready 秒内等待窗口创建完成。"""
        if self.thread and self.thread.is_alive():
            if self._ready_event.wait(timeout=wait_ready):
                return self.is_ready
            return False

        self._create_failed = False
        self._last_error = ""
        self._ready_event.clear()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name="HSOverlayThread", daemon=True)
        self.thread.start()

        if wait_ready <= 0:
            return True
        if self._ready_event.wait(timeout=wait_ready):
            return self.is_ready
        self._last_error = self._last_error or "overlay 窗口创建超时"
        print(f"[overlay] ⚠️ {self._last_error}")
        return False

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        self._ready_event.clear()
        self.hwnd = None

    def _find_hs_window(self):
        hs_hwnd = user32.FindWindowW("UnityWndClass", None)
        if hs_hwnd:
            return hs_hwnd
        for title in (self.title_hint, "炉石传说", "Hearthstone"):
            if not title:
                continue
            hs_hwnd = user32.FindWindowW(None, title)
            if hs_hwnd:
                return hs_hwnd
        return None

    def _overlay_position(self, hs_hwnd, *, content_w: int = 420, content_h: int = 210):
        """计算 overlay 屏幕坐标；炉石最小化/无效矩形时回退到屏幕左上角。"""
        if not hs_hwnd or user32.IsIconic(hs_hwnd):
            return _FALLBACK_X, _FALLBACK_Y
        rect = self._get_window_rect(hs_hwnd)
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w <= 0 or h <= 0 or rect.left < -2000 or rect.top < -2000:
            return _FALLBACK_X, _FALLBACK_Y
        x = rect.left + self._offset_x
        y = rect.top + self._offset_y
        return self._clamp_to_virtual_screen(x, y, content_w, content_h)

    def _window_position(self, hs_hwnd, *, content_w: int = 420, content_h: int = 210):
        """attach 模式用炉石客户区坐标；float 模式用屏幕坐标。"""
        with self._pos_lock:
            user_moved = self._user_positioned
        if (
            self.attach_to_game
            and hs_hwnd
            and not user32.IsIconic(hs_hwnd)
        ):
            if user_moved and self.hwnd and self._game_parent_hwnd == hs_hwnd:
                x, y = self._client_position_from_overlay(hs_hwnd)
            else:
                x, y = self._overlay_client_position(
                    hs_hwnd, content_w=content_w, content_h=content_h,
                )
            return self._clamp_to_parent_client(hs_hwnd, x, y, content_w, content_h)
        if user_moved and self.hwnd:
            rect = self._get_window_rect(self.hwnd)
            return rect.left, rect.top
        return self._overlay_position(hs_hwnd, content_w=content_w, content_h=content_h)

    def _ensure_shown(self, hs_hwnd=None):
        if not self.hwnd:
            return
        if not user32.IsWindowVisible(self.hwnd):
            user32.ShowWindow(self.hwnd, SW_SHOWNA)
        self._ensure_topmost(hs_hwnd)

    def _get_window_rect(self, hwnd) -> RECT:
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect

    def _loop(self):
        try:
            self._register_class()
            self._create_window()
            if not self.hwnd:
                self._create_failed = True
                self._last_error = self._last_error or "CreateWindowExW 失败"
                print(f"[overlay] 叠加层窗口创建失败: {self._last_error}（主程序仍可继续）")
                self._ready_event.set()
                while not self.stop_event.is_set():
                    time.sleep(0.5)
                return

            # 初始显示（固定尺寸，先出现在可见区域）
            user32.SetWindowPos(
                self.hwnd, HWND_TOPMOST, _FALLBACK_X, _FALLBACK_Y,
                self._min_w, self._fixed_h, SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
            user32.ShowWindow(self.hwnd, SW_SHOWNA)
            user32.UpdateWindow(self.hwnd)
            self._ready_event.set()

            if self.use_layered:
                self._enable_layered()

            while not self.stop_event.is_set():
                if self._user_closed:
                    if self.hwnd and user32.IsWindowVisible(self.hwnd):
                        user32.ShowWindow(self.hwnd, SW_HIDE)
                    msg = MSG()
                    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                    time.sleep(0.3)
                    continue

                hs = self._find_hs_window()

                with self._text_lock:
                    text = self._text or "等待数据…"
                    theme = self._theme
                    custom_colors = self._custom_colors

                display_text = text if hs else "未检测到 Hearthstone / 炉石传说 窗口…"
                content_w, content_h = self._content_size(display_text)

                ox, oy = self._window_position(hs, content_w=content_w, content_h=content_h)

                if custom_colors:
                    bg_rgb, fg_rgb = custom_colors["bg"], custom_colors["fg"]
                else:
                    bg_rgb, fg_rgb = self._resolve_display_colors(theme, None, bool(hs))
                if self.use_layered:
                    self._render_layered(display_text, content_w, content_h, bg_rgb, fg_rgb)
                else:
                    self._render_dc(display_text, content_w, content_h, bg_rgb, fg_rgb)

                self._apply_window_placement(hs, ox, oy, content_w, content_h)

                msg = MSG()
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                time.sleep(self._refresh_sec)
        except Exception as exc:
            self._create_failed = True
            self._last_error = str(exc)
            print(f"[overlay] 线程异常退出: {exc}")
            import traceback
            traceback.print_exc()
            self._ready_event.set()
        finally:
            self._destroy_fonts()
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None

    def window_rect(self):
        """调试用：返回 overlay 屏幕坐标与是否可见。"""
        if not self.hwnd:
            return None
        rect = self._get_window_rect(self.hwnd)
        return {
            "left": rect.left,
            "top": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
            "visible": bool(user32.IsWindowVisible(self.hwnd)),
            "topmost": bool(int(GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE)) & WS_EX_TOPMOST),
            "attached_to_game": self._game_parent_hwnd is not None,
        }


class ComboOverlay(Overlay):
    """斩杀步骤专用醒目窗口（紧贴主 HUD 下方，随主窗口跟随炉石）。"""

    THEME_COMBO_LETHAL = "combo_lethal"

    _COMBO_THEMES = {
        **Overlay._THEMES,
        THEME_COMBO_LETHAL: {"bg": (20, 0, 0), "fg": (255, 230, 80)},
    }

    _COMBO_GAP = 4

    def __init__(
        self,
        title_hint: str = "炉石传说",
        use_layered: bool = False,
        opacity: int = 245,
        *,
        anchor_overlay: Optional["Overlay"] = None,
        attach_to_game: Optional[bool] = None,
    ):
        if attach_to_game is None and anchor_overlay is not None:
            attach_to_game = anchor_overlay.attach_to_game
        if attach_to_game is None:
            attach_to_game = True
        super().__init__(
            title_hint=title_hint,
            use_layered=use_layered,
            opacity=opacity,
            attach_to_game=attach_to_game,
        )
        self._anchor_overlay = anchor_overlay
        self.className = f"HSComboOverlayClassPy_{kernel32.GetCurrentProcessId()}"
        self._fixed_w = 560
        self._fixed_h = 360
        self._min_w = 480
        self._max_w = 920
        self._pad_y = 14
        self._line_gap = 8
        self._THEMES = self._COMBO_THEMES
        self._destroy_fonts()
        self._fonts = self._create_fonts()

    def _create_fonts(self):
        return {
            "title": self._create_font(36, bold=True),
            "step": self._create_font(26, bold=True),
            "hint": self._create_font(20),
        }

    def _content_size(self, text: str):
        lines = [ln for ln in (text or "").split("\n") if ln.strip()]
        if not lines:
            return self._min_w, 0
        hdc = user32.GetDC(None)
        try:
            max_w = 0
            total_h = self._pad_y
            for i, line in enumerate(lines):
                if i == 0:
                    font = self._fonts["title"]
                elif line.startswith("（"):
                    font = self._fonts["hint"]
                else:
                    font = self._fonts["step"]
                w, h = self._text_extent(hdc, font, line)
                max_w = max(max_w, w)
                total_h += h + self._line_gap
            total_h += self._pad_y
            min_w = self._scaled_limit(self._min_w)
            max_w_limit = self._scaled_limit(self._max_w)
            width = min(max_w_limit, max(min_w, max_w + 2 * self._pad_x))
            return width, max(120, total_h)
        finally:
            user32.ReleaseDC(None, hdc)

    def _paint_combo_text(self, hdc, text: str, fg: int):
        lines = [ln for ln in (text or "").split("\n") if ln.strip()]
        y = self._pad_y
        for i, line in enumerate(lines):
            if i == 0:
                font = self._fonts["title"]
            elif line.startswith("（"):
                font = self._fonts["hint"]
            else:
                font = self._fonts["step"]
            _, lh = self._draw_text_at(hdc, font, line, self._pad_x, y, fg)
            y += lh + self._line_gap

    def _render_dc(self, text: str, w: int, h: int, bg_rgb, fg_rgb):
        hdc = user32.GetDC(self.hwnd)
        try:
            rect = RECT(0, 0, w, h)
            hbrush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
            user32.FillRect(hdc, ctypes.byref(rect), hbrush)
            gdi32.DeleteObject(hbrush)
            border = gdi32.CreateSolidBrush(RGB(255, 200, 40))
            edge = RECT(0, 0, w, 4)
            user32.FillRect(hdc, ctypes.byref(edge), border)
            gdi32.DeleteObject(border)
            self._paint_combo_text(hdc, text, RGB(*fg_rgb))
        finally:
            user32.ReleaseDC(self.hwnd, hdc)

    def _render_layered(self, text: str, w: int, h: int, bg_rgb, fg_rgb):
        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        gdi32.SelectObject(hdc_mem, hbmp)
        rect = RECT(0, 0, w, h)
        hbrush = gdi32.CreateSolidBrush(RGB(*bg_rgb))
        user32.FillRect(hdc_mem, ctypes.byref(rect), hbrush)
        gdi32.DeleteObject(hbrush)
        border = gdi32.CreateSolidBrush(RGB(255, 200, 40))
        edge = RECT(0, 0, w, 4)
        user32.FillRect(hdc_mem, ctypes.byref(edge), border)
        gdi32.DeleteObject(border)
        self._paint_combo_text(hdc_mem, text, RGB(*fg_rgb))
        pt_src = POINT(0, 0)
        pt_dst = POINT(0, 0)
        size = SIZE(w, h)
        blend = BLENDFUNCTION(0, 0, BYTE(self.opacity), 0)
        user32.UpdateLayeredWindow(
            self.hwnd, hdc_screen,
            ctypes.byref(pt_dst), ctypes.byref(size),
            hdc_mem, ctypes.byref(pt_src),
            0, ctypes.byref(blend), ULW_ALPHA,
        )
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

    def _anchor_position(
        self, hs_hwnd, *, content_w: int, content_h: int,
    ) -> Tuple[int, int]:
        """紧贴主 Overlay 底边；attach 模式用客户区坐标。"""
        anchor = self._anchor_overlay
        if anchor is None:
            if self.attach_to_game and hs_hwnd and not user32.IsIconic(hs_hwnd):
                return self._overlay_client_position(
                    hs_hwnd, content_w=content_w, content_h=content_h,
                )
            return super()._overlay_position(hs_hwnd, content_w=content_w, content_h=content_h)
        with anchor._text_lock:
            main_text = anchor._text or "等待数据…"
        main_w, main_h = anchor._content_size(main_text)
        ax, ay = anchor._window_position(hs_hwnd, content_w=main_w, content_h=main_h)
        x = ax
        y = ay + main_h + self._COMBO_GAP
        if self.attach_to_game and hs_hwnd and not user32.IsIconic(hs_hwnd):
            return self._clamp_to_parent_client(hs_hwnd, x, y, content_w, content_h)
        if anchor.hwnd and user32.IsWindowVisible(anchor.hwnd):
            arect = self._get_window_rect(anchor.hwnd)
            x = arect.left
            y = arect.bottom + self._COMBO_GAP
        return self._clamp_to_virtual_screen(x, y, content_w, content_h)

    def _window_position(self, hs_hwnd, *, content_w: int = 560, content_h: int = 360):
        """始终跟随主 Overlay，不受本窗拖动影响。"""
        return self._anchor_position(
            hs_hwnd, content_w=content_w, content_h=content_h,
        )

    def _wndproc(self, hwnd, msg, wparam, lparam):
        # 斩杀步骤窗不可单独拖动，避免与主 HUD 错位
        if msg == WM_NCHITTEST:
            return 1
        if msg == WM_SETCURSOR:
            user32.SetCursor(user32.LoadCursorW(None, IDC_ARROW))
            return 1
        return super()._wndproc(hwnd, msg, wparam, lparam)

    def _loop(self):
        try:
            self._register_class()
            self._create_window()
            if not self.hwnd:
                self._create_failed = True
                self._last_error = self._last_error or "CreateWindowExW 失败"
                print(f"[combo-overlay] 窗口创建失败: {self._last_error}")
                self._ready_event.set()
                while not self.stop_event.is_set():
                    time.sleep(0.5)
                return

            user32.SetWindowPos(
                self.hwnd, HWND_TOPMOST, _FALLBACK_X, _FALLBACK_Y + 120,
                self._min_w, self._fixed_h, SWP_NOACTIVATE,
            )
            user32.ShowWindow(self.hwnd, SW_HIDE)
            user32.UpdateWindow(self.hwnd)
            self._ready_event.set()

            if self.use_layered:
                self._enable_layered()

            while not self.stop_event.is_set():
                if self._user_closed:
                    if self.hwnd and user32.IsWindowVisible(self.hwnd):
                        user32.ShowWindow(self.hwnd, SW_HIDE)
                    msg = MSG()
                    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                    time.sleep(0.3)
                    continue

                hs = self._find_hs_window()
                with self._text_lock:
                    text = (self._text or "").strip()
                    theme = self._theme

                if not text:
                    if self.hwnd and user32.IsWindowVisible(self.hwnd):
                        user32.ShowWindow(self.hwnd, SW_HIDE)
                    time.sleep(0.5)
                    msg = MSG()
                    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                    continue

                content_w, content_h = self._content_size(text)
                ox, oy = self._window_position(hs, content_w=content_w, content_h=content_h)
                colors = self._COMBO_THEMES.get(
                    theme if hs else self.THEME_NORMAL,
                    self._COMBO_THEMES[self.THEME_COMBO_LETHAL],
                )
                bg_rgb, fg_rgb = colors["bg"], colors["fg"]
                if self.use_layered:
                    self._render_layered(text, content_w, content_h, bg_rgb, fg_rgb)
                else:
                    self._render_dc(text, content_w, content_h, bg_rgb, fg_rgb)

                self._apply_window_placement(hs, ox, oy, content_w, content_h)

                msg = MSG()
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                time.sleep(self._refresh_sec)
        except Exception as exc:
            self._create_failed = True
            self._last_error = str(exc)
            print(f"[combo-overlay] 线程异常: {exc}")
            import traceback
            traceback.print_exc()
            self._ready_event.set()
        finally:
            self._destroy_fonts()
            if self.hwnd:
                user32.DestroyWindow(self.hwnd)
                self.hwnd = None
