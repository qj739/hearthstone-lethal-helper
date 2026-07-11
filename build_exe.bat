@echo off
setlocal
cd /d "%~dp0"

echo [1/3] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo 未找到 python，请先安装 Python 3.10+ 并加入 PATH
    exit /b 1
)

echo [2/4] 安装打包依赖 PyInstaller / Pillow...
python -m pip install -q -U pyinstaller pillow

echo [3/4] 生成图标 assets\hs_lethal_helper.ico ...
python scripts\make_icon.py
if errorlevel 1 (
    echo 图标生成失败
    exit /b 1
)

echo [4/4] 打包 HS-Lethal-Helper.exe ...
python -m PyInstaller --noconfirm --clean HS-Lethal-Helper.spec

if errorlevel 1 (
    echo 打包失败
    exit /b 1
)

echo.
echo 完成: dist\HS-Lethal-Helper.exe
echo 我方 PlayerID 自动识别，无需配置战网名
echo 设置: 运行后在浮层菜单栏点击「设置」
endlocal
