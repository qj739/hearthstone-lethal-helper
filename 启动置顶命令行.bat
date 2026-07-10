@echo off
chcp 65001 >nul
echo 正在启动置顶命令行窗口...

:: 启动 PowerShell 并设置置顶
powershell -NoExit -Command "Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public class WindowHelper{[DllImport(\"user32.dll\")]public static extern bool SetWindowPos(IntPtr hWnd,IntPtr hWndInsertAfter,int X,int Y,int cx,int cy,uint uFlags);}';$handle=(Get-Process -Id $PID).MainWindowHandle;[WindowHelper]::SetWindowPos($handle,[IntPtr](-1),0,0,0,0,0x0043);Write-Host '✅ 窗口已置顶，可以开始工作' -ForegroundColor Green;Write-Host '';cd C:\Users\zqinjie\Desktop\HS"
