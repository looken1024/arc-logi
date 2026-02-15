# Redis Client Skill

连接远程 Redis 并执行常见读写操作的技能。

## 功能描述

此技能用于连接远程 Redis 服务器并执行常见的读写操作。当用户询问 Redis 相关操作时，AI 可以调用此技能来获取或设置 Redis 数据。

## 使用场景

- 查看 Redis 连接状态："检查 Redis 是否连接"
- 获取 Redis 信息："查看 Redis 服务器信息"
- 设置键值："设置 test_key 为 hello"
- 获取键值："获取 test_key 的值"
- 删除键："删除 test_key"
- 检查键是否存在："检查 test_key 是否存在"
- 列出所有键："列出所有键"
- 哈希操作：设置/获取哈希表字段
- 列表操作：左/右插入、范围查询
- 集合操作：添加成员、查看成员
- 有序集合操作：添加带分数的成员

## 参数说明

### connection parameters

#### host (可选)
- **类型**: string
- **默认值**: localhost
- **描述**: Redis 服务器地址（IP 或域名）

#### port (可选)
- **类型**: integer
- **默认值**: 6379
- **描述**: Redis 端口号

#### password (可选)
- **类型**: string
- **默认值**: (空)
- **描述**: Redis 密码（如有）

#### db (可选)
- **类型**: integer
- **默认值**: 0
- **描述**: Redis 数据库编号（0-15）

### operation parameters

#### operation (必填)
- **类型**: string
- **枚举值**: `get`, `set`, `delete`, `exists`, `keys`, `hget`, `hset`, `hgetall`, `lpush`, `rpush`, `lrange`, `sadd`, `smembers`, `sismember`, `zadd`, `zrange`, `info`, `ping`, `flushdb`
- **描述**: 要执行的 Redis 操作类型

#### key (可选)
- **类型**: string
- **描述**: Redis 键名

#### value (可选)
- **类型**: string
- **描述**: 要设置的值（用于 set, hset, lpush, rpush, sadd, zadd 操作）

#### field (可选)
- **类型**: string
- **描述**: 哈希字段名（用于 hget, hset 操作）

#### score (可选)
- **类型**: number
- **描述**: 有序集合分数（用于 zadd 操作）

#### start (可选)
- **类型**: integer
- **默认值**: 0
- **描述**: 列表/集合起始索引（用于 lrange, zrange）

#### end (可选)
- **类型**: integer
- **默认值**: -1
- **描述**: 列表/集合结束索引（用于 lrange, zrange，-1 表示末尾）

#### pattern (可选)
- **类型**: string
- **默认值**: *
- **描述**: 键匹配模式（用于 keys 操作）

## 操作说明

### 连接测试
- **ping**: 测试 Redis 连接，返回 PONG

### 服务器信息
- **info**: 获取 Redis 服务器详细信息（版本、内存使用、运行时长等）
- **flushdb**: 清空当前数据库（危险操作）

### 字符串操作
- **get**: 获取指定键的值
- **set**: 设置指定键的值
- **delete**: 删除指定键
- **exists**: 检查键是否存在

### 键操作
- **keys**: 列出匹配模式的键

### 哈希操作
- **hget**: 获取哈希表中指定字段的值
- **hset**: 设置哈希表中指定字段的值
- **hgetall**: 获取哈希表中所有字段和值

### 列表操作
- **lpush**: 在列表左侧插入值
- **rpush**: 在列表右侧插入值
- **lrange**: 获取列表指定范围的元素

### 集合操作
- **sadd**: 添加成员到集合
- **smembers**: 获取集合所有成员
- **sismember**: 检查值是否是集合成员

### 有序集合操作
- **zadd**: 添加成员到有序集合（带分数）
- **zrange**: 获取有序集合指定范围的成员（按分数升序）

## 返回值

返回 JSON 对象，包含 `success` 字段表示操作是否成功。

### 成功示例

```json
{
  "success": true,
  "key": "test_key",
  "value": "hello",
  "exists": true
}
```

```json
{
  "success": true,
  "result": "PONG",
  "message": "PONG"
}
```

### 错误示例

```json
{
  "success": false,
  "error": "Redis 连接失败: Connection refused",
  "host": "localhost",
  "port": 6379
}
```

## 使用示例

### 示例 1: 测试连接

**用户**: 检查 Redis 是否可以连接

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "ping",
    "host": "localhost",
    "port": 6379
  }
}
```

**返回**:
```json
{
  "success": true,
  "result": true,
  "message": "PONG"
}
```

---

### 示例 2: 设置键值

**用户**: 在 Redis 中设置 my_key 为 "hello world"

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "set",
    "key": "my_key",
    "value": "hello world"
  }
}
```

**返回**:
```json
{
  "success": true,
  "result": true,
  "key": "my_key",
  "value": "hello world",
  "message": "已设置 my_key = hello world"
}
```

---

### 示例 3: 获取键值

**用户**: 获取 my_key 的值

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "get",
    "key": "my_key"
  }
}
```

**返回**:
```json
{
  "success": true,
  "key": "my_key",
  "value": "hello world",
  "exists": true
}
```

---

### 示例 4: 哈希操作

**用户**: 在 Redis 哈希表 user:1 中设置 name 字段为 "张三"

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "hset",
    "key": "user:1",
    "field": "name",
    "value": "张三"
  }
}
```

---

### 示例 5: 列表操作

**用户**: 在列表 mylist 右侧插入 "world"

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "rpush",
    "key": "mylist",
    "value": "world"
  }
}
```

---

### 示例 6: 查看 Redis 信息

**用户**: 查看 Redis 服务器信息

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "info"
  }
}
```

**返回**:
```json
{
  "success": true,
  "result": {...},
  "redis_version": "7.0.0",
  "used_memory": "1.5MB",
  "uptime_days": 10
}
```

---

### 示例 7: 连接远程 Redis

**用户**: 连接 192.168.1.100:6380 的 Redis，设置密码为 mypass

**AI 调用**:
```json
{
  "function": "redis_client",
  "arguments": {
    "operation": "ping",
    "host": "192.168.1.100",
    "port": 6380,
    "password": "mypass"
  }
}
```

## 技术实现

- **主脚本**: `skill.py` - 技能核心实现
- **依赖**: `redis` Python 库
- **连接超时**: 5秒
- **响应解码**: 自动解码为字符串

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "success": false,
  "error": "错误详情",
  "host": "连接地址",
  "port": 端口号
}
```

常见错误：
- `redis ConnectionError`: 连接失败，检查 host/port/password
- `redis TimeoutError`: 操作超时
- 参数错误: 返回错误提示

## 注意事项

1. **安全性**: 不要在日志中暴露密码
2. **连接超时**: 默认5秒超时
3. **危险操作**: `flushdb` 会清空数据库，请谨慎使用
4. **大数据**: `keys` 操作可能阻塞 Redis，建议使用 `scan` 替代

## 版本历史

- **v1.0** (2024-02-15): 初始版本
  - 支持字符串、哈希、列表、集合、有序集合操作
  - 支持连接远程 Redis
  - 支持密码认证

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
