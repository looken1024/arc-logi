#!/bin/bash

# Admin 服务启停管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/.admin_server.pid"
LOG_FILE="$SCRIPT_DIR/admin.log"
PORT=5001

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "❌ 服务已在运行 (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "=========================================="
    echo "🚀 启动 Admin 服务..."
    echo "=========================================="

    echo "📦 检查依赖..."
    pip install -q flask flask-cors 2>/dev/null || true

    echo ""
    echo "=========================================="
    echo "✅ Admin 服务启动完成!"
    echo "🌐 访问地址: http://localhost:$PORT"
    echo "📝 日志文件: $LOG_FILE"
    echo "🛑 使用 $0 stop 停止服务"
    echo "=========================================="
    echo ""

    nohup python3 app.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "📌 服务 PID: $(cat "$PID_FILE")"
}

stop() {
    if ! netstat -tuln 2>/dev/null | grep -q ":$PORT " && ! ss -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "❌ 服务未运行 (端口 $PORT 未监听)"
        rm -f "$PID_FILE"
        return 1
    fi

    if [ ! -f "$PID_FILE" ]; then
        echo "❌ 服务未运行 (未找到 PID 文件，但端口 $PORT 被占用)"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        if ! netstat -tuln 2>/dev/null | grep -q ":$PORT " && ! ss -tuln 2>/dev/null | grep -q ":$PORT "; then
            rm -f "$PID_FILE"
            echo "❌ 服务未运行"
            return 1
        fi
        echo "⚠️  PID 文件过期，尝试查找端口 $PORT 对应的进程..."
        PID=$(lsof -ti:$PORT 2>/dev/null | head -1)
        if [ -z "$PID" ]; then
            echo "❌ 无法找到端口 $PORT 对应的进程"
            return 1
        fi
        echo "$PID" > "$PID_FILE"
    fi

    echo "🛑 停止服务 (PID: $PID)..."
    kill "$PID" 2>/dev/null

    TIMEOUT=10
    while [ $TIMEOUT -gt 0 ]; do
        if ! kill -0 "$PID" 2>/dev/null; then
            rm -f "$PID_FILE"
            echo "✅ 服务已停止"
            return 0
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
    stop || echo "ℹ️  服务未运行或停止失败，尝试启动..."
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
        start || exit 1
        ;;
    stop)
        stop || exit 1
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
