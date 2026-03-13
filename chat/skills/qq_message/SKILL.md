# QQ消息发送技能 (qq_message)

通过QQ机器人HTTP API发送消息的技能。

## 功能描述

此技能用于通过QQ机器人的HTTP API发送各种格式的消息到QQ好友、群聊或讨论组。支持发送文本消息、图片消息等（取决于具体的QQ机器人实现）。

## 使用场景

- 发送通知消息："发送系统监控告警到运维QQ群"
- 发送工作进度更新："向项目组发送每日工作进度报告"
- 发送错误报告："将异常信息发送给技术支持QQ群"
- 发送定时提醒："向会议室QQ群发送会议提醒"
- 发送数据报表："向管理层发送每日销售数据报告"

## 参数说明

### api_url (必需)
- **类型**: string
- **描述**: QQ机器人HTTP API地址，用于发送消息的端点
- **示例**: "http://localhost:5700/send_private_msg" 或 "http://localhost:5700/send_group_msg"

### message (必需)
- **类型**: string
- **描述**: 要发送的消息内容。支持纯文本或JSON格式的消息
- **示例**: 
  - 纯文本: "这是一条测试消息"
  - JSON格式: '{"user_id": 123456789, "message": "这是一条测试消息"}'

### message_type (可选)
- **类型**: string
- **描述**: 消息发送类型，支持 private_msg（私聊）、group_msg（群消息） 等类型，默认为 private_msg
- **示例**: "private_msg", "group_msg"
- **默认值**: "private_msg"

## 返回值

返回 JSON 对象，包含执行结果：

```json
{
  "success": true,
  "message": "消息发送成功",
  "response": {
    "status_code": 200,
    "data": {
      "status": "ok",
      "message_id": 123456
    }
  }
}
```

### 字段说明

- **success**: 消息是否发送成功
- **message**: 执行结果描述
- **response**: QQ机器人API的原始响应（如果可用）

## 使用示例

### 示例 1: 发送私聊消息

**用户**: 向QQ好友发送一条测试消息

**AI 调用**:
```json
{
  "function": "qq_message",
  "arguments": {
    "api_url": "http://localhost:5700/send_private_msg",
    "message": "这是一条测试消息",
    "message_type": "private_msg"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "消息发送成功",
  "response": {
    "status_code": 200,
    "data": {
      "status": "ok",
      "message_id": 123456
    }
  }
}
```

### 示例 2: 发送群聊消息（使用JSON格式）

**用户**: 发送一条消息到QQ群

**AI 调用**:
```json
{
  "function": "qq_message",
  "arguments": {
    "api_url": "http://localhost:5700/send_group_msg",
    "message": "{\"group_id\": 123456789, \"message\": \"这是一条群消息测试\"}",
    "message_type": "group_msg"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "消息发送成功",
  "response": {
    "status_code": 200,
    "data": {
      "status": "ok",
      "message_id": 123457
    }
  }
}
```

## 技术实现

- **数据源**: QQ机器人 HTTP API（如go-cqhttp、NoneBot等框架提供的API）
- **API 调用**: 直接POST请求到API URL
- **主脚本**: `skill.py` - 技能核心实现
- **依赖**: `requests` 库（已包含在项目依赖中）
- **错误处理**: 网络超时、无效API URL、消息发送失败等情况都有相应处理
- **消息格式**: 支持纯文本和JSON格式的消息

### 常见QQ机器人框架API示例

#### go-cqhttp API
- 私聊消息: POST http://localhost:5700/send_private_msg
  参数: {"user_id": 123456789, "message": "hello"}
- 群聊消息: POST http://localhost:5700/send_group_msg
  参数: {"group_id": 123456789, "message": "hello"}

#### NoneBot API (类似)
- 私聊消息: POST http://localhost:8080/send_private_msg
- 群聊消息: POST http://localhost:8080/send_group_msg

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "success": false,
  "message": "错误描述信息",
  "response": null
}
```

### 常见错误

- **无效的API URL**: 当提供的API URL格式不正确或不可达时
  ```json
  {
    "success": false,
    "message": "无效的API URL: [具体错误信息]",
    "response": null
  }
  ```

- **网络请求失败**: 当网络连接出现问题或QQ机器人服务不可用时
  ```json
  {
    "success": false,
    "message": "网络请求失败: [具体错误信息]",
    "response": null
  }
  ```

- **请求超时**: 当网络请求超时时（默认10秒）
  ```json
  {
    "success": false,
    "message": "请求超时，请检查网络连接",
    "response": null
  }
  ```

- **消息发送失败**: 当QQ机器人API返回错误时
  ```json
  {
    "success": false,
    "message": "消息发送失败: [QQ机器人返回的错误信息]",
    "response": {"status_code": 400, "data": {"status": "failed", "msg": "API调用失败"}}
  }
  ```

- **消息格式错误**: 当提供的消息JSON格式不正确时
  ```json
  {
    "success": false,
    "message": "消息格式错误: [JSON解析错误信息]",
    "response": null
  }
  ```

## 版本历史

- **v1.0** (2026-03-13): 初始版本
  - 支持发送私聊消息
  - 支持发送群聊消息
  - 支持纯文本和JSON格式的消息
  - 可配置消息发送类型
  - 完善的错误处理
  - 详细的使用示例

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
