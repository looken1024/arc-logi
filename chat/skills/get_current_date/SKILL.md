# Get Current Date Skill

获取当前日期和时间信息的技能。

## 功能描述

此技能用于获取当前的日期和时间信息，包括年、月、日、星期、时间等。当用户询问"今天几号？"、"现在几点？"、"星期几？"等问题时，AI 可以调用此技能获取准确的时间信息。

## 使用场景

- 询问当前日期："今天几号？"
- 询问当前时间："现在几点了？"
- 询问星期几："今天星期几？"
- 询问完整日期时间："现在是什么时间？"
- 获取时间戳："给我当前的时间戳"

## 参数说明

### format (可选)
- **类型**: string
- **枚举值**: `full`, `date`, `time`, `datetime`, `timestamp`
- **默认值**: `full`
- **描述**: 返回格式
  - `full`: 完整信息（日期+星期+时间+人性化描述）
  - `date`: 仅日期（年月日）
  - `time`: 仅时间（时分秒）
  - `datetime`: 日期时间（年月日+时分秒）
  - `timestamp`: Unix 时间戳

### timezone (可选)
- **类型**: string
- **默认值**: `Asia/Shanghai`
- **描述**: 时区设置
  - 示例: `Asia/Shanghai`, `UTC`, `America/New_York`

## 返回值

返回 JSON 对象，包含以下字段：

```json
{
  "year": 2024,
  "month": 1,
  "day": 31,
  "hour": 15,
  "minute": 30,
  "second": 45,
  "weekday": "星期三",
  "weekday_number": 3,
  "timezone": "Asia/Shanghai",
  "formatted": "2024年1月31日 星期三 15:30:45",
  "iso_format": "2024-01-31T15:30:45",
  "timestamp": 1706688645,
  "description": "现在是2024年1月31日，星期三，下午15点30分。下午好！"
}
```

根据 `format` 参数不同，返回的字段会有所调整。

## 使用示例

### 示例 1: 获取完整日期时间（默认）

**用户**: 今天几号？

**AI 调用**:
```json
{
  "function": "get_current_date",
  "arguments": {}
}
```

**返回**:
```json
{
  "year": 2024,
  "month": 1,
  "day": 31,
  "formatted": "2024年1月31日 星期三 15:30:45",
  "description": "现在是2024年1月31日，星期三，下午15点30分。下午好！"
}
```

**AI 回复**: 今天是2024年1月31日，星期三。下午好！

---

### 示例 2: 仅获取日期

**用户**: 今天是几月几号？

**AI 调用**:
```json
{
  "function": "get_current_date",
  "arguments": {
    "format": "date"
  }
}
```

**返回**:
```json
{
  "year": 2024,
  "month": 1,
  "day": 31,
  "formatted": "2024年1月31日",
  "iso_format": "2024-01-31"
}
```

**AI 回复**: 今天是2024年1月31日。

---

### 示例 3: 仅获取时间

**用户**: 现在几点了？

**AI 调用**:
```json
{
  "function": "get_current_date",
  "arguments": {
    "format": "time"
  }
}
```

**返回**:
```json
{
  "hour": 15,
  "minute": 30,
  "second": 45,
  "formatted": "15:30:45",
  "iso_format": "15:30:45"
}
```

**AI 回复**: 现在是下午3点30分。

---

### 示例 4: 获取时间戳

**用户**: 给我当前的时间戳

**AI 调用**:
```json
{
  "function": "get_current_date",
  "arguments": {
    "format": "timestamp"
  }
}
```

**返回**:
```json
{
  "timestamp": 1706688645,
  "timestamp_ms": 1706688645000
}
```

**AI 回复**: 当前的 Unix 时间戳是 1706688645（毫秒: 1706688645000）。

## 技术实现

- **主脚本**: `skill.py` - 技能核心实现
- **辅助脚本**: `scripts/` - 实用工具脚本目录
- **文档**: `SKILL.md` - 详细使用文档
- **依赖**: Python 标准库 (`datetime`, `locale`)
- **时区支持**: 可配置，默认使用 Asia/Shanghai
- **本地化**: 支持中文星期显示
- **人性化**: 自动判断时段（早上/中午/下午/晚上/深夜）并生成问候语

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "error": "获取日期时间失败: [错误详情]"
}
```

## 版本历史

- **v1.0** (2024-01-31): 初始版本
  - 支持多种格式返回
  - 支持时区配置
  - 人性化时间描述
  - 中文星期显示

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
