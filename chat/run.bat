@echo off
echo ================================
echo   AI Chat Platform Starting...
echo ================================
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
    echo.
)

REM 激活虚拟环境
echo [2/4] Activating virtual environment...
call venv\Scripts\activate
echo.

REM 安装依赖
echo [3/4] Installing dependencies...
pip install -r requirements.txt -q
echo Dependencies installed!
echo.

REM 检查环境变量文件
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and configure your API key.
    echo.
    pause
    exit /b 1
)

REM 运行应用
echo [4/4] Starting Flask application...
echo.
echo ================================
echo   Server running at:
echo   http://localhost:5000
echo ================================
echo.
python app.py

pause
