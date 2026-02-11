#!/bin/bash

# Chat 服务启停管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.chat_server.pid"
LOG_FILE="$SCRIPT_DIR/chat.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "❌ 服务已在运行 (PID: $PID)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    if [ ! -d "venv" ]; then
        echo "❌ 错误: 虚拟环境不存在，请先运行 setup.sh 或手动创建"
        exit 1
    fi

    echo "=========================================="
    echo "🚀 启动 Chat 服务..."
    echo "=========================================="

    source venv/bin/activate

    echo "📦 激活虚拟环境..."
    pip install -q -r requirements.txt 2>/dev/null || true

    echo "🗄️  初始化数据库..."
    python -c "
from app import init_database
try:
    init_database()
    print('✅ 数据库初始化完成')
except Exception as e:
    print(f'⚠️  数据库初始化失败: {e}')
    print('   请确保 MySQL 已启动并配置正确的连接信息')
" 2>&1 | tee -a "$LOG_FILE"

    echo ""
    echo "=========================================="
    echo "✅ Chat 服务启动完成!"
    echo "🌐 访问地址: http://localhost:8000"
    echo "📝 日志文件: $LOG_FILE"
    echo "🛑 使用 stop.sh 停止服务"
    echo "=========================================="
    echo ""

    nohup python app.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "📌 服务 PID: $(cat "$PID_FILE")"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ 服务未运行 (未找到 PID 文件)"
        exit 1
    fi

    PID=$(cat "$PID_FILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "❌ 服务未运行 (PID: $PID 可能已失效)"
        rm -f "$PID_FILE"
        exit 1
    fi

    echo "🛑 停止服务 (PID: $PID)..."
    kill "$PID" 2>/dev/null

    TIMEOUT=10
    while [ $TIMEOUT -gt 0 ]; do
        if ! kill -0 "$PID" 2>/dev/null; then
            rm -f "$PID_FILE"
            echo "✅ 服务已停止"
            exit 0
        fi
        sleep 1
        TIMEOUT=$((TIMEOUT - 1))
    done

    echo "⚠️  强制终止服务..."
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "✅ 服务已强制停止"
}

restart() {
    echo "🔄 重启服务..."
    stop
    sleep 2
    start
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✅ 服务运行中 (PID: $PID)"
            exit 0
        else
            echo "❌ 服务未运行 (PID 文件过期)"
            rm -f "$PID_FILE"
            exit 1
        fi
    else
        echo "❌ 服务未运行"
        exit 1
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
