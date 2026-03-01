#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_INTERVAL=10
CTL_SCRIPT="$SCRIPT_DIR/ctl.sh"

is_running() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":${port} " || ss -tuln 2>/dev/null | grep -q ":${port} "; then
        return 0
    else
        return 1
    fi
}

if [ -f "$CTL_SCRIPT" ]; then
    PORT=8000
else
    echo "❌ ctl.sh 不存在"
    exit 1
fi

echo "=========================================="
echo "🔍 Chat 服务监控已启动"
echo "📡 监听端口: $PORT"
echo "⏱️  检查间隔: ${CHECK_INTERVAL} 秒"
echo "=========================================="
echo ""

while true; do
    if ! is_running $PORT; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ⚠️  端口 $PORT 未监听，正在启动服务..."
        "$CTL_SCRIPT" start
        if [ $? -eq 0 ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 服务启动成功"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') ❌ 服务启动失败"
        fi
    fi
    sleep $CHECK_INTERVAL
done
