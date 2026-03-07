# Schedule Skill

定时任务技能，用于创建和管理定时任务。

## 功能描述

此技能用于创建、查看、更新、删除和执行定时任务。定时任务可以按照指定的 Cron 表达式定期执行 shell 命令或脚本。创建的定时任务将展示在定时任务管理页面，并由后台调度器自动执行。

## 使用场景

- 创建定时任务："创建一个每天凌晨3点备份数据库的定时任务"
- 查看定时任务列表："列出我所有的定时任务"
- 查看定时任务详情："查看ID为5的定时任务详情"
- 更新定时任务："更新ID为5的定时任务的Cron表达式"
- 删除定时任务："删除ID为5的定时任务"
- 立即执行定时任务："立即执行ID为5的定时任务"
- 查看执行记录："查看ID为5的定时任务的执行记录"

## 参数说明

### action (可选)
- **类型**: string
- **枚举值**: `create`, `list`, `get`, `update`, `delete`, `execute`, `get_executions`
- **默认值**: `create`
- **描述**: 操作类型：
  - `create`: 创建定时任务
  - `list`: 列出定时任务
  - `get`: 获取单个任务详情
  - `update`: 更新任务
  - `delete`: 删除任务
  - `execute`: 立即执行任务
  - `get_executions`: 获取任务执行记录

### schedule_id (可选)
- **类型**: integer
- **描述**: 定时任务ID（用于get、update、delete、execute、get_executions操作）

### name (可选)
- **类型**: string
- **描述**: 定时任务名称，用于标识任务（用于create、update操作）

### cron (可选)
- **类型**: string
- **描述**: Cron表达式，定义任务执行时间。例如：'0 * * * *' 表示每小时执行一次（用于create、update操作）

### command (可选)
- **类型**: string
- **描述**: 要执行的命令，可以是 shell 命令或脚本（用于create、update操作）

### description (可选)
- **类型**: string
- **默认值**: ""
- **描述**: 任务描述（用于create、update操作）

### preset (可选)
- **类型**: string
- **默认值**: ""
- **描述**: 预设类型（用于create、update操作）

### status (可选)
- **类型**: string
- **枚举值**: `active`, `paused`
- **默认值**: `active`
- **描述**: 任务状态，active 为激活，paused 为暂停（用于create、update操作）

### filters (可选)
- **类型**: object
- **描述**: 过滤条件（用于list操作）
- **属性**:
  - `status`: 状态过滤，可选值 `active`, `paused`, `all`，默认 `all`

### page (可选)
- **类型**: integer
- **默认值**: 1
- **最小值**: 1
- **描述**: 页码（用于list、get_executions操作分页）

### page_size (可选)
- **类型**: integer
- **默认值**: 20
- **最小值**: 1
- **最大值**: 100
- **描述**: 每页数量（用于list、get_executions操作分页）

## 操作说明

### 创建定时任务 (create)
创建新的定时任务。需要提供 `name`、`cron`、`command` 参数。

### 列出定时任务 (list)
列出当前用户的所有定时任务，支持按状态过滤和分页。

### 获取定时任务详情 (get)
获取指定定时任务的详细信息。需要提供 `schedule_id`。

### 更新定时任务 (update)
更新现有定时任务。需要提供 `schedule_id` 和要更新的字段。

### 删除定时任务 (delete)
删除指定定时任务。需要提供 `schedule_id`。

### 立即执行定时任务 (execute)
立即执行指定定时任务。需要提供 `schedule_id`。注意：实际执行需要通过定时任务管理界面触发。

### 获取执行记录 (get_executions)
获取指定定时任务的执行记录。需要提供 `schedule_id`，支持分页。

## 返回值

返回 JSON 对象，包含 `success` 字段表示操作是否成功。

### 成功示例

#### 创建成功
```json
{
  "success": true,
  "message": "定时任务创建成功",
  "schedule": {
    "id": 5,
    "name": "每日备份",
    "description": "每天凌晨3点备份数据库",
    "cron": "0 3 * * *",
    "preset": "",
    "command": "/home/user/backup.sh",
    "status": "active",
    "last_run_at": null,
    "next_run_at": "2025-03-08T03:00:00",
    "created_at": "2025-03-07T10:30:00",
    "updated_at": "2025-03-07T10:30:00"
  }
}
```

#### 列表成功
```json
{
  "success": true,
  "schedules": [
    {
      "id": 5,
      "name": "每日备份",
      "description": "每天凌晨3点备份数据库",
      "cron": "0 3 * * *",
      "preset": "",
      "command": "/home/user/backup.sh",
      "status": "active",
      "last_run_at": null,
      "next_run_at": "2025-03-08T03:00:00",
      "created_at": "2025-03-07T10:30:00",
      "updated_at": "2025-03-07T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 获取成功
```json
{
  "success": true,
  "schedule": {
    "id": 5,
    "name": "每日备份",
    "description": "每天凌晨3点备份数据库",
    "cron": "0 3 * * *",
    "preset": "",
    "command": "/home/user/backup.sh",
    "status": "active",
    "last_run_at": null,
    "next_run_at": "2025-03-08T03:00:00",
    "created_at": "2025-03-07T10:30:00",
    "updated_at": "2025-03-07T10:30:00"
  }
}
```

#### 更新成功
```json
{
  "success": true,
  "message": "定时任务更新成功",
  "schedule": {
    "id": 5,
    "name": "每日备份更新",
    "description": "每天凌晨4点备份数据库",
    "cron": "0 4 * * *",
    "preset": "",
    "command": "/home/user/backup.sh",
    "status": "active",
    "last_run_at": null,
    "next_run_at": "2025-03-08T04:00:00",
    "created_at": "2025-03-07T10:30:00",
    "updated_at": "2025-03-07T11:00:00"
  }
}
```

#### 删除成功
```json
{
  "success": true,
  "message": "定时任务删除成功"
}
```

#### 执行记录成功
```json
{
  "success": true,
  "executions": [
    {
      "id": 1,
      "execution_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "output": "Backup completed successfully",
      "error_message": null,
      "started_at": "2025-03-07T03:00:01",
      "completed_at": "2025-03-07T03:00:05",
      "created_at": "2025-03-07T03:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

### 错误示例

#### 缺少参数
```json
{
  "success": false,
  "error": "缺少必要参数: name, cron, command"
}
```

#### 任务不存在
```json
{
  "success": false,
  "error": "定时任务不存在或无权访问"
}
```

#### Cron表达式无效
```json
{
  "success": false,
  "error": "Cron 表达式无效: invalid cron expression"
}
```

#### 数据库错误
```json
{
  "success": false,
  "error": "数据库错误: (1045, \"Access denied for user 'root'@'localhost' (using password: YES)\")"
}
```

## 使用示例

### 示例 1: 创建定时任务

**用户**: 创建一个每天凌晨3点备份数据库的定时任务，任务名称为"每日备份"，命令是"/home/user/backup.sh"

**AI 调用**:
```json
{
  "function": "create_schedule",
  "arguments": {
    "action": "create",
    "name": "每日备份",
    "cron": "0 3 * * *",
    "command": "/home/user/backup.sh",
    "description": "每天凌晨3点备份数据库"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "定时任务创建成功",
  "schedule": {
    "id": 5,
    "name": "每日备份",
    "description": "每天凌晨3点备份数据库",
    "cron": "0 3 * * *",
    "preset": "",
    "command": "/home/user/backup.sh",
    "status": "active",
    "last_run_at": null,
    "next_run_at": "2025-03-08T03:00:00",
    "created_at": "2025-03-07T10:30:00",
    "updated_at": "2025-03-07T10:30:00"
  }
}
```

**AI 回复**: 已成功创建定时任务"每日备份"，该任务将于每天凌晨3点执行备份脚本。

---

### 示例 2: 列出定时任务

**用户**: 列出我所有的定时任务

**AI 调用**:
```json
{
  "function": "create_schedule",
  "arguments": {
    "action": "list",
    "filters": {
      "status": "all"
    },
    "page": 1,
    "page_size": 10
  }
}
```

**返回**:
```json
{
  "success": true,
  "schedules": [
    {
      "id": 5,
      "name": "每日备份",
      "description": "每天凌晨3点备份数据库",
      "cron": "0 3 * * *",
      "preset": "",
      "command": "/home/user/backup.sh",
      "status": "active",
      "last_run_at": null,
      "next_run_at": "2025-03-08T03:00:00",
      "created_at": "2025-03-07T10:30:00",
      "updated_at": "2025-03-07T10:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

**AI 回复**: 您共有1个定时任务：
1. **每日备份** (ID: 5)：每天凌晨3点执行，状态：激活，下次执行时间：2025-03-08 03:00:00

---

### 示例 3: 更新定时任务

**用户**: 将ID为5的定时任务的执行时间改为凌晨4点

**AI 调用**:
```json
{
  "function": "create_schedule",
  "arguments": {
    "action": "update",
    "schedule_id": 5,
    "cron": "0 4 * * *",
    "description": "每天凌晨4点备份数据库"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "定时任务更新成功",
  "schedule": {
    "id": 5,
    "name": "每日备份",
    "description": "每天凌晨4点备份数据库",
    "cron": "0 4 * * *",
    "preset": "",
    "command": "/home/user/backup.sh",
    "status": "active",
    "last_run_at": null,
    "next_run_at": "2025-03-08T04:00:00",
    "created_at": "2025-03-07T10:30:00",
    "updated_at": "2025-03-07T11:00:00"
  }
}
```

**AI 回复**: 已成功更新定时任务"每日备份"，执行时间已改为每天凌晨4点。

---

### 示例 4: 删除定时任务

**用户**: 删除ID为5的定时任务

**AI 调用**:
```json
{
  "function": "create_schedule",
  "arguments": {
    "action": "delete",
    "schedule_id": 5
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "定时任务删除成功"
}
```

**AI 回复**: 已成功删除ID为5的定时任务。

---

### 示例 5: 查看执行记录

**用户**: 查看ID为5的定时任务的执行记录

**AI 调用**:
```json
{
  "function": "create_schedule",
  "arguments": {
    "action": "get_executions",
    "schedule_id": 5,
    "page": 1,
    "page_size": 10
  }
}
```

**返回**:
```json
{
  "success": true,
  "executions": [
    {
      "id": 1,
      "execution_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "output": "Backup completed successfully",
      "error_message": null,
      "started_at": "2025-03-07T03:00:01",
      "completed_at": "2025-03-07T03:00:05",
      "created_at": "2025-03-07T03:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

**AI 回复**: ID为5的定时任务共有1条执行记录：
- 执行时间：2025-03-07 03:00:01，状态：已完成，输出：Backup completed successfully

## 技术实现

- **主脚本**: `scripts/skill.py` - 技能核心实现
- **依赖**: `pymysql`、`croniter` Python 库
- **数据库**: 使用 MySQL 存储定时任务和执行记录
- **调度器**: 后台调度器自动执行定时任务（独立进程）
- **用户隔离**: 每个用户只能访问自己的定时任务

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "success": false,
  "error": "错误详情"
}
```

常见错误：
- `ImportError`: 依赖库未安装，请安装 pymysql 和 croniter
- `ValueError`: 参数错误，检查必要参数是否提供
- `pymysql.Error`: 数据库错误，检查数据库连接和权限
- `权限错误`: 用户无权访问该定时任务

## 注意事项

1. **Cron表达式**: 使用标准 Cron 表达式格式（分 时 日 月 周）
2. **命令安全性**: 确保执行的命令是安全的，避免注入攻击
3. **用户隔离**: 每个用户只能管理自己的定时任务
4. **执行环境**: 命令在服务器环境中执行，确保有足够的权限
5. **日志记录**: 所有执行记录都会保存，便于排查问题

## 版本历史

- **v1.0** (2025-03-07): 初始版本
  - 支持创建、查看、更新、删除定时任务
  - 支持查看执行记录
  - 支持分页和过滤

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License