@echo off
title DEX Trading Bot v7.0 - Complete Installation
color 0B

echo ============================================================
echo   DEX TRADING BOT V7.0 - COMPLETE INSTALLATION
echo ============================================================
echo.
echo This will:
echo   1. Install Python dependencies
echo   2. Create Desktop\v7bot folder
echo   3. Copy all v7 files
echo   4. Copy all v4 backend modules (unchanged)
echo   5. Setup proper directory structure
echo.
pause

echo.
echo [1/6] Installing Python dependencies...
echo.

python -m pip install --upgrade pip
python -m pip uninstall -y web3
python -m pip install web3==7.6.0
python -m pip install customtkinter requests python-dotenv pyyaml eth-account

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Dependency installation failed!
    pause
    exit /b 1
)

echo ✓ Dependencies installed
echo.

echo [2/6] Creating Desktop\v7bot folder...
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "INSTALL_DIR=%DESKTOP%\v7bot"

if exist "%INSTALL_DIR%" (
    echo Found existing v7bot folder
    choice /C YN /M "Delete and recreate"
    if errorlevel 2 goto :skip_delete
    rmdir /S /Q "%INSTALL_DIR%"
)

:skip_delete
mkdir "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%\src"
mkdir "%INSTALL_DIR%\data"
mkdir "%INSTALL_DIR%\logs"

echo ✓ Folders created
echo.

echo [3/6] Copying v7 core files...
echo.

copy /Y main_v7.py "%INSTALL_DIR%\" >nul
copy /Y gui_v7.py "%INSTALL_DIR%\" >nul
copy /Y main_integrated_v7.py "%INSTALL_DIR%\" >nul
copy /Y backend_modules_v7.py "%INSTALL_DIR%\" >nul
copy /Y opportunity_scanner_v7.py "%INSTALL_DIR%\" >nul
copy /Y networks_v7.json "%INSTALL_DIR%\" >nul
copy /Y START_V7.bat "%INSTALL_DIR%\" >nul

echo ✓ Core files copied
echo.

echo [4/6] Copying v4 backend modules (unchanged)...
echo.

REM These files keep their v4 names
copy /Y wallet_manager_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y dex_router_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y swap_executor_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y token_scanner_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y state_manager_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y abi_manager_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y slippage_calculator_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y transaction_manager_v4.py "%INSTALL_DIR%\" >nul 2>nul
copy /Y route_optimizer_v4.py "%INSTALL_DIR%\" >nul 2>nul

REM Also copy to src folder for imports
copy /Y wallet_manager_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y dex_router_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y swap_executor_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y token_scanner_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y state_manager_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y abi_manager_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y slippage_calculator_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y transaction_manager_v4.py "%INSTALL_DIR%\src\" >nul 2>nul
copy /Y route_optimizer_v4.py "%INSTALL_DIR%\src\" >nul 2>nul

echo ✓ Backend modules copied
echo.

echo [5/6] Creating safety guide...
echo.

(
echo ====================================================================
echo   DEX TRADING BOT V7 - SAFETY GUIDE
echo ====================================================================
echo.
echo BEFORE TRADING:
echo   1. Start in SIMULATION mode
echo   2. Set a small trading balance [$1-$10]
echo   3. Test with paper trading first
echo   4. Use a separate wallet for live trading
echo.
echo RISK MANAGEMENT:
echo   - Max position size: 5%% of balance
echo   - Stop loss: 5%%
echo   - Take profit: 10%%
echo   - Daily loss limit: 10%%
echo.
echo WALLET SECURITY:
echo   - Never share your private key
echo   - Use hardware wallet when possible
echo   - Start with small amounts
echo   - Monitor closely when live
echo.
echo FIXES IN V7:
echo   ✓ Balance management fixed
echo   ✓ Swap executor properly initialized
echo   ✓ Activity feed integrated in dashboard
echo   ✓ Token detection improved
echo   ✓ Better error handling
echo.
echo ====================================================================
) > "%INSTALL_DIR%\SAFETY_GUIDE.txt"

echo ✓ Safety guide created
echo.

echo [6/6] Installation complete!
echo.
echo ============================================================
echo   INSTALLATION SUCCESSFUL!
echo ============================================================
echo.
echo Location: %INSTALL_DIR%
echo.
echo NEXT STEPS:
echo   1. Navigate to Desktop\v7bot
echo   2. Double-click START_V7.bat
echo   3. Start in SIMULATION mode
echo   4. Read SAFETY_GUIDE.txt
echo.
echo ============================================================
echo.
pause

REM Open folder
explorer "%INSTALL_DIR%"
