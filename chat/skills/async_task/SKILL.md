# Async Task Skill

异步任务技能，用于创建后台异步执行的任务。

## 功能描述

此技能用于创建异步任务，任务会在后台通过 `opencode run --thinking` 命令执行。当用户请求执行一个需要较长时间的任务，或者需要在后台处理某些工作时，可以使用此技能。

## 使用场景

- 用户请求："帮我分析一下这个代码文件"
- 用户请求："帮我写一个爬虫脚本"
- 用户请求："帮我整理一下这个文件夹中的文件"
- 用户请求："帮我生成一个报告"

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_name | string | 是 | 任务名称，用于标识任务 |
| task_description | string | 是 | 任务描述，详细说明需要执行什么工作 |
| scheduled_at | string | 否 | 计划执行时间，格式为 YYYY-MM-DD HH:MM:SS，默认为立即执行 |

## 返回值

返回 JSON 对象，包含以下字段：

```json
{
  "success": true,
  "task_id": 123,
  "task_name": "任务名称",
  "status": "pending",
  "message": "任务已创建，将在后台执行"
}
```

## 使用示例

### 示例 1: 创建即时异步任务

**用户**: 帮我分析一下这个代码文件

**AI 调用**:
```json
{
  "function": "async_task",
  "arguments": {
    "task_name": "分析代码文件",
    "task_description": "分析项目中的代码文件结构和复杂度"
  }
}
```

**返回**:
```json
{
  "success": true,
  "task_id": 123,
  "task_name": "分析代码文件",
  "status": "pending",
  "message": "任务已创建，将在后台通过 opencode run --thinking 执行"
}
```

### 示例 2: 创建定时异步任务

**用户**: 每天早上9点帮我生成一份报告

**AI 调用**:
```json
{
  "function": "async_task",
  "arguments": {
    "task_name": "生成日报",
    "task_description": "生成每日的运营报告",
    "scheduled_at": "2024-01-01 09:00:00"
  }
}
```

**返回**:
```json
{
  "success": true,
  "task_id": 124,
  "task_name": "生成日报",
  "status": "scheduled",
  "scheduled_at": "2024-01-01 09:00:00",
  "message": "任务已创建，计划在 2024-01-01 09:00:00 执行"
}
```

## 技术实现

- **主脚本**: `skill.py` - 技能核心实现
- **文档**: `SKILL.md` - 详细使用文档
- **执行方式**: 通过 `opencode run --thinking` 在后台执行任务
- **任务管理**: 任务存储在数据库的 async_tasks 表中

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "success": false,
  "error": "创建任务失败: [错误详情]"
}
```

## 版本历史

- **v1.0** (2025-03-14): 初始版本
  - 支持创建异步任务
  - 支持即时执行和定时执行

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
