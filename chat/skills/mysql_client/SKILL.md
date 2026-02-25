# MySQL Client Skill

连接远程 MySQL 数据库并执行增删改查操作的技能。

## 功能描述

此技能用于连接远程 MySQL 数据库并执行常见的 CRUD 操作。当用户询问 MySQL 数据库相关操作时，AI 可以调用此技能来查询、插入、更新、删除数据。

## 使用场景

- 测试 MySQL 连接："检查 MySQL 是否连接"
- 查看数据库列表："查看所有数据库"
- 查看表列表："查看当前数据库的所有表"
- 查看表结构："查看 users 表结构"
- 查询数据："查询 users 表中所有数据"
- 插入数据："在 users 表插入一条数据"
- 更新数据："更新 users 表中 id 为 1 的用户名称"
- 删除数据："删除 users 表中 id 为 2 的记录"
- 执行自定义 SQL："执行 SQL: SELECT * FROM orders"

## 参数说明

### connection parameters

#### host (可选)
- **类型**: string
- **默认值**: localhost
- **描述**: MySQL 服务器地址（IP 或域名）

#### port (可选)
- **类型**: integer
- **默认值**: 3306
- **描述**: MySQL 端口号

#### user (可选)
- **类型**: string
- **默认值**: root
- **描述**: MySQL 用户名

#### password (可选)
- **类型**: string
- **默认值**: (空)
- **描述**: MySQL 密码

#### database (可选)
- **类型**: string
- **默认值**: (空)
- **描述**: 数据库名称

#### charset (可选)
- **类型**: string
- **默认值**: utf8mb4
- **描述**: 字符编码

### operation parameters

#### operation (必填)
- **类型**: string
- **枚举值**: `query`, `insert`, `update`, `delete`, `execute`, `show_tables`, `show_databases`, `describe`, `ping`
- **描述**: 要执行的 MySQL 操作类型

#### table (可选)
- **类型**: string
- **描述**: 表名（用于 insert, update, delete, describe, show_tables）

#### data (可选)
- **类型**: object
- **描述**: 要插入或更新的数据（JSON 对象，用于 insert, update 操作）

#### condition (可选)
- **类型**: object
- **描述**: 更新/删除条件（JSON 对象，用于 update, delete 操作）

#### sql (可选)
- **类型**: string
- **描述**: 自定义 SQL 语句（用于 execute 操作）

#### limit (可选)
- **类型**: integer
- **默认值**: 100
- **描述**: 查询结果返回数量限制

## 操作说明

### 连接测试
- **ping**: 测试 MySQL 连接，返回连接状态

### 数据库操作
- **show_databases**: 显示所有数据库
- **show_tables**: 显示指定数据库的所有表
- **describe**: 显示表结构（字段、类型、主键等）

### CRUD 操作
- **query**: 查询数据（支持条件查询）
- **insert**: 插入数据
- **update**: 更新数据（需要条件）
- **delete**: 删除数据（需要条件）

### 高级操作
- **execute**: 执行任意 SQL 语句

## 返回值

返回 JSON 对象，包含 `success` 字段表示操作是否成功。

### 成功示例

```json
{
  "success": true,
  "message": "MySQL 连接成功"
}
```

```json
{
  "success": true,
  "table": "users",
  "data": [
    {"id": 1, "name": "张三", "age": 25},
    {"id": 2, "name": "李四", "age": 30}
  ],
  "count": 2
}
```

```json
{
  "success": true,
  "table": "users",
  "affected_rows": 1,
  "insert_id": 3,
  "message": "成功插入 1 行数据"
}
```

### 错误示例

```json
{
  "success": false,
  "error": "MySQL 连接失败: Connection refused",
  "host": "localhost",
  "port": 3306
}
```

```json
{
  "success": false,
  "error": "query 操作需要指定 table 参数"
}
```

## 使用示例

### 示例 1: 测试连接

**用户**: 检查 MySQL 是否可以连接

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "ping",
    "host": "localhost",
    "user": "root",
    "password": "mypassword"
  }
}
```

**返回**:
```json
{
  "success": true,
  "result": {"result": 1},
  "message": "MySQL 连接成功"
}
```

---

### 示例 2: 查看数据库

**用户**: 查看所有数据库

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "show_databases",
    "host": "localhost",
    "user": "root",
    "password": "mypassword"
  }
}
```

**返回**:
```json
{
  "success": true,
  "databases": ["information_schema", "mysql", "test_db"],
  "count": 3
}
```

---

### 示例 3: 查看表结构

**用户**: 查看 users 表的结构

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "describe",
    "database": "myapp",
    "table": "users"
  }
}
```

**返回**:
```json
{
  "success": true,
  "table": "users",
  "columns": [
    {"field": "id", "type": "int", "null": "NO", "key": "PRI", "extra": "auto_increment"},
    {"field": "name", "type": "varchar(100)", "null": "YES", "key": "", "extra": ""},
    {"field": "email", "type": "varchar(255)", "null": "NO", "key": "UNI", "extra": ""}
  ],
  "count": 3
}
```

---

### 示例 4: 查询数据

**用户**: 查询 users 表中 age 大于 20 的用户

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "query",
    "database": "myapp",
    "table": "users",
    "condition": {"status": "active"},
    "limit": 10
  }
}
```

**返回**:
```json
{
  "success": true,
  "table": "users",
  "data": [
    {"id": 1, "name": "张三", "age": 25, "status": "active"},
    {"id": 2, "name": "李四", "age": 30, "status": "active"}
  ],
  "count": 2
}
```

---

### 示例 5: 插入数据

**用户**: 在 users 表插入一条新用户

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "insert",
    "database": "myapp",
    "table": "users",
    "data": {
      "name": "王五",
      "email": "wang@example.com",
      "age": 28,
      "status": "active"
    }
  }
}
```

**返回**:
```json
{
  "success": true,
  "table": "users",
  "affected_rows": 1,
  "insert_id": 5,
  "message": "成功插入 1 行数据"
}
```

---

### 示例 6: 更新数据

**用户**: 更新 users 表中 id 为 1 的用户的年龄

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "update",
    "database": "myapp",
    "table": "users",
    "data": {"age": 26},
    "condition": {"id": 1}
  }
}
```

**返回**:
```json
{
  "success": true,
  "table": "users",
  "affected_rows": 1,
  "message": "成功更新 1 行数据"
}
```

---

### 示例 7: 删除数据

**用户**: 删除 users 表中 id 为 2 的记录

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "delete",
    "database": "myapp",
    "table": "users",
    "condition": {"id": 2}
  }
}
```

**返回**:
```json
{
  "success": true,
  "table": "users",
  "affected_rows": 1,
  "message": "成功删除 1 行数据"
}
```

---

### 示例 8: 执行自定义 SQL

**用户**: 执行自定义 SQL 查询订单

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "execute",
    "database": "myapp",
    "sql": "SELECT o.id, o.total, u.name FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.status = 'pending' LIMIT 20"
  }
}
```

**返回**:
```json
{
  "success": true,
  "sql": "SELECT o.id, o.total, u.name FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.status = 'pending' LIMIT 20",
  "data": [
    {"id": 100, "total": 199.99, "name": "张三"},
    {"id": 101, "total": 299.50, "name": "李四"}
  ],
  "count": 2
}
```

---

### 示例 9: 连接远程 MySQL

**用户**: 连接 192.168.1.100:3306 的 MySQL，数据库为 myapp

**AI 调用**:
```json
{
  "function": "mysql_client",
  "arguments": {
    "operation": "show_tables",
    "host": "192.168.1.100",
    "port": 3306,
    "user": "myuser",
    "password": "mypassword",
    "database": "myapp"
  }
}
```

## 技术实现

- **主脚本**: `scripts/skill.py` - 技能核心实现
- **依赖**: `pymysql` Python 库
- **连接超时**: 10秒
- **读写超时**: 30秒
- **游标类型**: DictCursor（返回字典而非元组）

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "success": false,
  "error": "错误详情",
  "operation": "操作类型"
}
```

常见错误：
- `pymysql.Error`: MySQL 执行错误，检查 SQL 语法
- `ConnectionError`: 连接失败，检查 host/port/user/password
- `参数错误`: 缺少必要参数，返回相应提示

## 注意事项

1. **安全性**: 不要在日志中暴露密码
2. **连接超时**: 默认 10 秒超时
3. **防误操作**: update 和 delete 操作必须提供 condition 条件，防止全表操作
4. **SQL 注入**: 使用参数化查询，防止 SQL 注入
5. **字符编码**: 默认使用 utf8mb4，支持 emoji

## 版本历史

- **v1.0** (2024-02-25): 初始版本
  - 支持完整的 CRUD 操作
  - 支持连接远程 MySQL
  - 支持自定义 SQL 执行
  - 支持查看数据库和表结构

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
