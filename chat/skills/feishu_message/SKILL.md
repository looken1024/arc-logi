# 飞书消息发送技能 (feishu_message)

通过飞书（Lark）机器人Webhook发送消息的技能。

## 功能描述

此技能用于通过飞书（Lark）机器人的Webhook发送各种格式的消息到飞书群聊或私聊。支持发送文本消息、富文本消息、卡片消息等。

## 使用场景

- 发送通知消息："发送系统监控告警到运维群"
- 发送工作进度更新："向项目组发送每日工作进度报告"
- 发送错误报告："将异常信息发送给技术支持群"
- 发送定时提醒："向会议室群发送会议提醒"
- 发送数据报表："向管理层发送每日销售数据报告"

## 参数说明

### webhook_url (必需)
- **类型**: string
- **描述**: 飞书机器人Webhook URL，用于发送消息的地址
- **示例**: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

### message (必需)
- **类型**: string
- **描述**: 要发送的消息内容，支持文本消息和JSON格式的卡片消息
- **示例**: "这是一条测试消息" 或 '{"msg_type": "text", "content": {"text": "这是一条测试消息"}}'

### msg_type (可选)
- **类型**: string
- **描述**: 消息类型，支持 text、interactive、post 等类型，默认为 text
- **示例**: "text", "interactive", "post"
- **默认值**: "text"

## 返回值

返回 JSON 对象，包含执行结果：

```json
{
  "success": true,
  "message": "消息发送成功",
  "response": {
    "status_code": 200,
    "data": {
      "code": 0,
      "msg": "success"
    }
  }
}
```

### 字段说明

- **success**: 消息是否发送成功
- **message**: 执行结果描述
- **response**: 飞书API的原始响应（如果可用）

## 使用示例

### 示例 1: 发送简单文本消息

**用户**: 向飞书群发送一条测试消息

**AI 调用**:
```json
{
  "function": "feishu_message",
  "arguments": {
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "message": "这是一条测试消息",
    "msg_type": "text"
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
      "code": 0,
      "msg": "success"
    }
  }
}
```

### 示例 2: 发送富文本消息（使用JSON格式）

**用户**: 发送一条包含链接的富文本消息到项目群

**AI 调用**:
```json
{
  "function": "feishu_message",
  "arguments": {
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "message": "{\"msg_type\": \"post\", \"content\": {\"post\": {\"zh_cn\": {\"title\": \"项目更新\", \"content\": [[{\"tag\": \"text\", \"text\": \"项目进度更新：\"}, {\"tag\": \"a\", \"text\": \"查看详情\", \"href\": \"https://example.com/project\"}]]}}}",
    "msg_type": "post"
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
      "code": 0,
      "msg": "success"
    }
  }
}
```

## 技术实现

- **数据源**: 飞书开放平台 Webhook API
- **API 调用**: 直接POST请求到Webhook URL
- **主脚本**: `skill.py` - 技能核心实现
- **依赖**: `requests` 库（已包含在项目依赖中）
- **错误处理**: 网络超时、无效Webhook URL、消息发送失败等情况都有相应处理
- **消息格式**: 支持纯文本和JSON格式的消息（包括卡片消息）

### API 使用说明

飞书机器人Webhook API:
- 端点: 自定义的Webhook URL（在飞书开放平台创建机器人时获得）
- 方法: POST
- 请求体: JSON格式，包含msg_type和content字段
- 响应: JSON格式，包含code和msg字段

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

- **无效的Webhook URL**: 当提供的Webhook URL格式不正确或不可达时
  ```json
  {
    "success": false,
    "message": "无效的Webhook URL: [具体错误信息]",
    "response": null
  }
  ```

- **网络请求失败**: 当网络连接出现问题或飞书服务不可用时
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

- **消息发送失败**: 当飞书API返回错误时
  ```json
  {
    "success": false,
    "message": "消息发送失败: [飞书返回的错误信息]",
    "response": {"status_code": 400, "data": {"code": 1234567, "msg": "Invalid webhook url"}}
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
  - 支持发送文本消息
  - 支持发送富文本/卡片消息（通过JSON格式）
  - 可配置消息类型
  - 完善的错误处理
  - 详细的使用示例

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License