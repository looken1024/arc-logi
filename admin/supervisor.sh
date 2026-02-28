#!/bin/bash

# Admin 服务监控脚本
# 当发现 5001 端口不再有监听时，触发 ctl.sh start

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_INTERVAL=10
PORT=5001

check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$PORT " || ss -tuln 2>/dev/null | grep -q ":$PORT "; then
        return 0
    else
        return 1
    fi
}

echo "=========================================="
echo "🔍 Admin 服务监控已启动"
echo "📡 监听端口: $PORT"
echo "⏱️  检查间隔: ${CHECK_INTERVAL} 秒"
echo "=========================================="
echo ""

while true; do
    if ! check_port; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ⚠️  端口 $PORT 未监听，正在启动服务..."
        "$SCRIPT_DIR/ctl.sh" start
        if [ $? -eq 0 ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 服务启动成功"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') ❌ 服务启动失败"
        fi
    fi
    sleep $CHECK_INTERVAL
done
