@echo off
title DEX Trading Bot v7.0
color 0A

echo ============================================================
echo   DEX TRADING BOT V7.0 - PROFESSIONAL EDITION
echo ============================================================
echo.
echo Starting bot...
echo.

if not exist "main_integrated_v7.py" (
    echo ❌ main_integrated_v7.py not found!
    echo Please run INSTALL_V7.bat first
    pause
    exit /b 1
)

python main_integrated_v7.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo   ERROR: Failed to start bot
    echo ============================================================
    echo.
    echo Possible fixes:
    echo   1. Run INSTALL_V7.bat
    echo   2. Check error above
    echo.
    pause
)
