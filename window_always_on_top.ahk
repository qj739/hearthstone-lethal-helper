; window_always_on_top.ahk
; 按 Ctrl + Space 切换当前窗口的置顶状态

^Space::  ; Ctrl + Space
Winset, AlwaysOnTop, Toggle, A
WinGetTitle, WindowTitle, A
if (ErrorLevel = 0)
{
    WinGet, ExStyle, ExStyle, A
    if (ExStyle & 0x8)  ; 0x8 是 WS_EX_TOPMOST
        TrayTip, 窗口置顶, %WindowTitle% 已置顶, 1
    else
        TrayTip, 窗口置顶, %WindowTitle% 已取消置顶, 1
}
return
