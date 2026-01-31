#!/bin/bash

echo "================================"
echo "  AI Chat Platform Starting..."
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created!"
    echo ""
fi

# 激活虚拟环境
echo "[2/4] Activating virtual environment..."
source venv/bin/activate
echo ""

# 安装依赖
echo "[3/4] Installing dependencies..."
pip install -r requirements.txt -q
echo "Dependencies installed!"
echo ""

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and configure your API key."
    echo ""
    exit 1
fi

# 运行应用
echo "[4/4] Starting Flask application..."
echo ""
echo "================================"
echo "  Server running at:"
echo "  http://localhost:5000"
echo "================================"
echo ""
python app.py
