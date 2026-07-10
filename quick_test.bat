@echo off
echo ========================================
echo 炉石传说辅助工具 - 快速测试
echo ========================================
echo.

echo [1/4] 测试基础功能...
python tests/test_hdt.py
if %errorlevel% neq 0 (
    echo 基础测试失败！
    pause
    exit /b 1
)

echo.
echo [2/4] 测试嘲讽逻辑...
python tests/test_taunt.py
if %errorlevel% neq 0 (
    echo 嘲讽测试失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 测试最优解算法...
python tests/test_optimal_taunt.py
if %errorlevel% neq 0 (
    echo 最优解测试失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 所有测试通过！
echo ========================================
echo.
echo 现在可以运行主程序了：
echo   python hdt_tracker.py
echo.
pause
