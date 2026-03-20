# 邮件发送技能 (email_sender)

通过SMTP协议发送邮件的技能。

## 功能描述

此技能用于通过SMTP协议发送电子邮件。支持发送纯文本邮件和HTML格式邮件，可添加附件（未来扩展）。

**系统默认配置**：发件人邮箱和授权码已预设为163邮箱配置，用户只需提供收件人、主题和内容即可发送邮件。

## 使用场景

- 发送系统通知："发送服务器监控告警邮件"
- 发送工作报告："向团队发送每日工作进度报告"
- 发送错误日志："将程序异常信息发送给开发团队"
- 发送定时提醒："向与会者发送会议提醒邮件"
- 发送数据报告："向管理层发送每日销售数据报告"

## 默认配置

系统已预配置以下163邮箱作为默认发件人：

| 配置项 | 默认值 |
|--------|--------|
| SMTP服务器 | smtp.163.com |
| SMTP端口 | 465 (SSL) |
| 发件人邮箱 | 18518007500@163.com |
| 授权码 | 系统预配置 |
| 使用SSL | true |

**注意**：如需使用其他邮箱账户，可以在调用时覆盖SMTP配置参数。

## 参数说明

### receiver_email (必需)
- **类型**: string
- **描述**: 接收者邮箱地址，多个地址用逗号分隔
- **示例**: "user1@example.com,user2@example.com"

### subject (必需)
- **类型**: string
- **描述**: 邮件主题
- **示例**: "系统监控告警 - 需要立即处理"

### content (必需)
- **类型**: string
- **描述**: 邮件内容
- **示例**: "这是一封测试邮件"

### smtp_server (可选)
- **类型**: string
- **描述**: SMTP服务器地址
- **示例**: "smtp.qq.com", "smtp.163.com", "smtp.gmail.com"
- **默认值**: "smtp.163.com"

### smtp_port (可选)
- **类型**: integer
- **描述**: SMTP服务器端口
- **示例**: 465 (SSL), 587 (TLS), 25 (普通)
- **默认值**: 465

### sender_email (可选)
- **类型**: string
- **描述**: 发送者邮箱地址
- **示例**: "user@example.com"
- **默认值**: "18518007500@163.com"

### sender_password (可选)
- **类型**: string
- **描述**: 发送者邮箱密码或授权码（建议使用授权码而非直接密码）
- **示例**: "your_authorization_code"
- **默认值**: 系统预配置

### content_type (可选)
- **类型**: string
- **描述**: 邮件内容类型，支持 plain（纯文本） 或 html（HTML格式），默认为 plain
- **示例**: "plain", "html"
- **默认值**: "plain"

### use_ssl (可选)
- **类型**: boolean
- **描述**: 是否使用SSL加密连接，默认为 true
- **示例**: true, false
- **默认值**: true

## 返回值

返回 JSON 对象，包含执行结果：

```json
{
  "success": true,
  "message": "邮件发送成功",
  "response": null
}
```

### 字段说明

- **success**: 邮件是否发送成功
- **message**: 执行结果描述
- **response**: 预留字段，目前为 null

## 使用示例

### 示例 1: 使用默认配置发送纯文本邮件（推荐）

**用户**: 发送一封测试邮件到个人邮箱

**AI 调用**:
```json
{
  "function": "email_sender",
  "arguments": {
    "receiver_email": "receiver@example.com",
    "subject": "测试邮件",
    "content": "这是一封测试邮件"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "邮件发送成功",
  "response": null
}
```

### 示例 2: 使用默认配置发送HTML格式邮件

**用户**: 发送一封带格式的邮件给团队

**AI 调用**:
```json
{
  "function": "email_sender",
  "arguments": {
    "receiver_email": "team1@example.com,team2@example.com",
    "subject": "项目周报",
    "content": "<h2>项目周报</h2><p>本周完成了以下工作：</p><ul><li>完成模块A开发</li><li>开始模块B测试</li></ul>",
    "content_type": "html"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "邮件发送成功",
  "response": null
}
```

### 示例 3: 使用自定义SMTP配置发送邮件

**用户**: 使用QQ邮箱发送邮件

**AI 调用**:
```json
{
  "function": "email_sender",
  "arguments": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender_email": "123456789@qq.com",
    "sender_password": "your_authorization_code",
    "receiver_email": "receiver@example.com",
    "subject": "测试邮件",
    "content": "这是一封测试邮件"
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "邮件发送成功",
  "response": null
}
```

## 技术实现

- **数据源**: SMTP协议
- **API 调用**: 使用Python的`smtplib`和`email`库发送邮件
- **主脚本**: `skill.py` - 技能核心实现
- **依赖**: Python标准库`smtplib`、`email`（无需额外安装）
- **默认配置**: 系统预配置163邮箱（smtp.163.com）作为默认发件人
- **错误处理**: 连接失败、认证失败、发送失败等情况都有相应处理
- **安全建议**: 
  - 授权码存储在代码中，生产环境建议使用环境变量或配置中心管理
  - 建议使用邮箱授权码而非直接密码，避免敏感信息泄露

### SMTP 常见配置

| 邮箱服务 | SMTP服务器 | SSL端口 | TLS端口 |
|----------|------------|---------|---------|
| QQ邮箱   | smtp.qq.com | 465     | 587     |
| 网易邮箱 | smtp.163.com | 465     | 587     |
| Gmail    | smtp.gmail.com | 465     | 587     |
| Outlook  | smtp.office365.com | 587     | 25      |

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

- **SMTP连接失败**: 当无法连接到SMTP服务器时
  ```json
  {
    "success": false,
    "message": "SMTP连接失败: [具体错误信息]",
    "response": null
  }
  ```

- **认证失败**: 当邮箱用户名或密码/授权码错误时
  ```json
  {
    "success": false,
    "message": "登录认证失败: 用户名或密码错误",
    "response": null
  }
  ```

- **发送失败**: 当邮件发送过程中出现错误时
  ```json
  {
    "success": false,
    "message": "邮件发送失败: [具体错误信息]",
    "response": null
  }
  ```

- **参数验证错误**: 当必要参数缺失或格式不正确时
  ```json
  {
    "success": false,
    "message": "缺少必需参数: smtp_server",
    "response": null
  }
  ```

## 版本历史

- **v1.1** (2026-03-20): 默认配置更新
  - 预配置163邮箱（18518007500@163.com）作为默认发件人
  - 简化调用参数，只需提供收件人、主题和内容即可发送
  - 可选SMTP配置参数支持自定义邮箱发送
  - 更新文档和使用示例

- **v1.0** (2026-03-13): 初始版本
  - 支持发送纯文本邮件
  - 支持发送HTML格式邮件
  - 支持SSL/TLS加密连接
  - 可配置SMTP服务器和端口
  - 完善的错误处理
  - 详细的使用示例

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
