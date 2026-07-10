# keep_window_topmost.ps1 - 让当前窗口始终置顶

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WindowHelper {
    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
    public const uint SWP_NOMOVE = 0x0002;
    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_SHOWWINDOW = 0x0040;
}
"@

# 获取当前 PowerShell 窗口句柄
$handle = (Get-Process -Id $PID).MainWindowHandle

# 设置为置顶
[WindowHelper]::SetWindowPos($handle, [WindowHelper]::HWND_TOPMOST, 0, 0, 0, 0,
    [WindowHelper]::SWP_NOMOVE -bor [WindowHelper]::SWP_NOSIZE -bor [WindowHelper]::SWP_SHOWWINDOW)

Write-Host "✅ 当前窗口已设置为始终置顶" -ForegroundColor Green
Write-Host "提示: 关闭窗口后此设置会重置" -ForegroundColor Yellow
