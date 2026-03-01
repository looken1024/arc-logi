#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8000
LOG_FILE="$SCRIPT_DIR/chat.log"
APP_FILE="app.py"

is_running() {
    if netstat -tuln 2>/dev/null | grep -q ":${PORT} " || ss -tuln 2>/dev/null | grep -q ":${PORT} "; then
        return 0
    else
        return 1
    fi
}

get_pid_by_port() {
    local pid
    pid=$(lsof -ti:${PORT} 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        echo "$pid"
        return 0
    fi
    pid=$(fuser ${PORT}/tcp 2>/dev/null | awk '{print $1}')
    if [ -n "$pid" ]; then
        echo "$pid"
        return 0
    fi
    return 1
}

start() {
    if is_running; then
        local pid
        pid=$(get_pid_by_port)
        echo "❌ 服务已在运行 (PID: $pid, 端口: $PORT)"
        return 1
    fi

    if [ ! -d "venv" ]; then
        echo "❌ 错误: 虚拟环境不存在，请先运行 setup.sh 或手动创建"
        return 1
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
    echo "🌐 访问地址: http://localhost:${PORT}"
    echo "📝 日志文件: $LOG_FILE"
    echo "🛑 使用 $0 stop 停止服务"
    echo "=========================================="
    echo ""

    nohup python $APP_FILE >> "$LOG_FILE" 2>&1 &
    local pid=$!
    sleep 1
    
    if is_running; then
        echo "📌 服务 PID: $pid"
    else
        echo "⚠️  服务启动后端口未监听，请检查日志: $LOG_FILE"
    fi
}

stop() {
    if ! is_running; then
        echo "❌ 服务未运行 (端口 $PORT 未监听)"
        return 1
    fi

    local pid
    pid=$(get_pid_by_port)
    if [ -z "$pid" ]; then
        echo "❌ 无法找到端口 $PORT 对应的进程"
        return 1
    fi

    echo "🛑 停止服务 (PID: $pid, 端口: $PORT)..."
    kill "$pid" 2>/dev/null

    local timeout=10
    while [ $timeout -gt 0 ]; do
        if ! is_running; then
            echo "✅ 服务已停止"
            return 0
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    echo "⚠️  强制终止服务..."
    kill -9 "$pid" 2>/dev/null
    sleep 1
    
    if ! is_running; then
        echo "✅ 服务已强制停止"
        return 0
    else
        echo "❌ 服务停止失败"
        return 1
    fi
}

restart() {
    echo "🔄 重启服务..."
    stop
    sleep 2
    start
}

status() {
    if is_running; then
        local pid
        pid=$(get_pid_by_port)
        echo "✅ 服务运行中 (PID: $pid, 端口: $PORT)"
        exit 0
    else
        echo "❌ 服务未运行 (端口: $PORT)"
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
