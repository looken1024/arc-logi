# 知识库部署与运维指南

## 目录

1. [环境要求](#环境要求)
2. [数据库配置](#数据库配置)
3. [部署步骤](#部署步骤)
4. [配置说明](#配置说明)
5. [运维监控](#运维监控)
6. [备份恢复](#备份恢复)
7. [性能优化](#性能优化)
8. [故障排查](#故障排查)

---

## 环境要求

### 基础环境
- Python 3.8+
- MySQL 5.7+ / MariaDB 10.3+
- Redis 5.0+ (可选，用于缓存)

### 系统依赖
```bash
# Ubuntu/Debian
apt-get update && apt-get install -y \
    python3.8 python3-pip \
    mysql-server \
    redis-server

# CentOS/RHEL
yum install -y \
    python38 python38-pip \
    mysql-server \
    redis
```

### Python 依赖
```bash
pip install -r requirements.txt
```

---

## 数据库配置

### 1. 创建数据库
```bash
mysql -u root -p < schema.sql
mysql -u root -p < schema_knowledge_base.sql
```

### 2. 创建专用用户
```sql
CREATE USER 'kb_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON arc_logi_chat.* TO 'kb_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量
```bash
# .env
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=kb_user
export DB_PASSWORD=your_password
export DB_NAME=arc_logi_chat
```

---

## 部署步骤

### 开发环境
```bash
# 1. 克隆代码
git clone <repository_url>
cd arc-logi/chat

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
# 编辑 .env 填入配置

# 5. 初始化数据库
mysql -u root -p < schema.sql
mysql -u root -p < schema_knowledge_base.sql

# 6. 启动服务
python app.py
```

### 生产环境 (使用 Gunicorn)

```bash
# 安装 gunicorn
pip install gunicorn

# 启动命令
gunicorn -w 4 -b 0.0.0.0:8000 app:app \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info
```

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - DB_PASSWORD=secret
    depends_on:
      - db
      - redis
  
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: arc_logi_chat
    volumes:
      - mysql_data:/var/lib/mysql
  
  redis:
    image: redis:6-alpine

volumes:
  mysql_data:
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 3306 | 数据库端口 |
| DB_USER | root | 数据库用户 |
| DB_PASSWORD | - | 数据库密码 |
| DB_NAME | arc_logi_chat | 数据库名 |
| DB_CHARSET | utf8mb4 | 字符集 |
| SECRET_KEY | - | Flask 密钥 |
| REDIS_HOST | localhost | Redis 主机 |
| REDIS_PORT | 6379 | Redis 端口 |

### 知识库配置

```python
# app.py 中可配置的参数
KNOWLEDGE_BASE_CONFIG = {
    'max_items_per_kb': 10000,      # 单知识库最大条目数
    'max_content_length': 50000,     # 最大内容长度
    'version_retention': 30,         # 版本保留天数
    'search_cache_ttl': 300,        # 搜索缓存 TTL (秒)
    'graph_max_nodes': 500          # 图谱最大节点数
}
```

---

## 运维监控

### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler(
    'logs/knowledge_base.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
```

### 监控指标

| 指标 | 描述 | 告警阈值 |
|------|------|----------|
| kb_item_count | 知识条目总数 | > 10000 |
| kb_query_latency | 查询延迟 | > 500ms |
| kb_write_latency | 写入延迟 | > 1000ms |
| db_connection_count | 数据库连接数 | > 80% |
| cache_hit_rate | 缓存命中率 | < 60% |

### 健康检查

```
GET /api/health
```

```json
{
  "status": "healthy",
  "database": "connected",
  "knowledge_base": {
    "total_items": 1234,
    "total_kb": 10
  }
}
```

---

## 备份恢复

### 自动备份脚本

```bash
#!/bin/bash
# backup_knowledge_base.sh

BACKUP_DIR="/backup/kb"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="arc_logi_chat"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
mysqldump -u root -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/kb_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/kb_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: kb_$DATE.sql.gz"
```

### 恢复数据

```bash
# 解压备份
gunzip kb_20240115_100000.sql.gz

# 恢复数据
mysql -u root -p$DB_PASSWORD $DB_NAME < kb_20240115_100000.sql
```

### 定时备份 (crontab)

```bash
# 每天凌晨 2 点执行备份
0 2 * * * /path/to/backup_knowledge_base.sh >> /var/log/backup.log 2>&1
```

---

## 性能优化

### 数据库优化

```sql
-- 添加索引
ALTER TABLE knowledge_item ADD INDEX idx_search (knowledge_base_id, updated_at);
ALTER TABLE knowledge_relation ADD INDEX idx_relation (source_item_id, target_item_id);

-- 定期分析表
OPTIMIZE TABLE knowledge_item;
OPTIMIZE TABLE knowledge_base;
```

### 缓存策略

```python
# 使用 Redis 缓存热点数据
import redis
import json

cache = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_items(kb_id, page=1):
    cache_key = f"kb:{kb_id}:items:page:{page}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 从数据库获取
    items = fetch_items_from_db(kb_id, page)
    
    # 缓存 5 分钟
    cache.setex(cache_key, 300, json.dumps(items))
    return items
```

### 分页优化

```sql
-- 使用游标分页替代 OFFSET
SELECT * FROM knowledge_item 
WHERE knowledge_base_id = ? AND id < ? 
ORDER BY id DESC 
LIMIT 20;
```

---

## 故障排查

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无法连接数据库 | 连接信息错误 | 检查环境变量配置 |
| 知识条目创建失败 | 表不存在 | 运行 schema_knowledge_base.sql |
| 搜索无结果 | 索引缺失 | 重建索引 |
| 图谱加载慢 | 数据量过大 | 增加缓存或分页加载 |
| 写入超时 | 事务锁等待 | 优化查询或增加超时时间 |

### 日志分析

```bash
# 查看错误日志
tail -f logs/error.log | grep "knowledge_base"

# 查看慢查询
grep "slow query" logs/app.log

# 查看访问量
awk '{print $7}' logs/access.log | sort | uniq -c | sort -rn | head -20
```

### 调试模式

```bash
# 启用调试模式
export FLASK_DEBUG=1
python app.py

# 或代码中启用
app.config['DEBUG'] = True
app.config['SQLALCHEMY_ECHO'] = True
```

---

## 安全建议

1. **数据库安全**
   - 使用强密码
   - 限制数据库用户权限
   - 启用 SSL 连接

2. **API 安全**
   - 实现请求频率限制
   - 添加 CSRF 防护
   - 使用 HTTPS

3. **数据安全**
   - 定期备份
   - 敏感数据加密
   - 访问日志审计

---

## 扩展阅读

- [API 接口文档](./knowledge-base-api.md)
- [用户操作手册](./knowledge-base-user-guide.md)
- [知识图谱文档](./knowledge-graph.md)
