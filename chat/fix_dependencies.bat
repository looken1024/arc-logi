@echo off
echo ================================
echo   Fixing Dependencies...
echo ================================
echo.

REM 激活虚拟环境
if exist "venv\Scripts\activate" (
    call venv\Scripts\activate
) else (
    echo Virtual environment not found! Please run run.bat first.
    pause
    exit /b 1
)

echo [1/3] Uninstalling old openai package...
pip uninstall openai -y

echo.
echo [2/3] Clearing pip cache...
pip cache purge

echo.
echo [3/3] Installing fresh dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ================================
echo   Dependencies fixed!
echo   Please restart the server.
echo ================================
pause
