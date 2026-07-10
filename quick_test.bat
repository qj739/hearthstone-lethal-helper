@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo HS Lethal Helper - Quick Test
echo ========================================
echo.

echo [1/3] test_hdt...
python tests\test_hdt.py
if errorlevel 1 goto fail

echo.
echo [2/3] test_taunt...
python tests\test_taunt.py
if errorlevel 1 goto fail

echo.
echo [3/3] test_optimal_taunt...
python tests\test_optimal_taunt.py
if errorlevel 1 goto fail

echo.
echo ========================================
echo All tests passed.
echo ========================================
echo.
echo Run main app: python hdt_tracker.py
echo.
pause
exit /b 0

:fail
echo.
echo TEST FAILED.
pause
exit /b 1
