# 🤖 AI Chat Platform

一个功能完整的 AI 对话平台，采用 DeepSeek 风格设计，提供现代化的用户体验。基于 Python Flask 后端和原生 JavaScript 前端构建。

---

## ✨ 核心特性

### 💬 智能对话
- **实时流式响应** - AI 回复逐字显示，无需等待完整响应
- **多模型支持** - DeepSeek Chat、DeepSeek Coder、GPT-3.5、GPT-4
- **上下文记忆** - 自动维护对话上下文，实现连贯交流
- **Markdown 渲染** - 支持代码高亮、格式化文本

### 🔐 用户系统
- **账户注册/登录** - 安全的用户认证机制
- **会话管理** - 7天自动登录，无需重复输入
- **密码加密** - 使用 bcrypt 哈希加密存储
- **对话隔离** - 每个用户只能访问自己的对话数据

### 🎨 个性化体验
- **5种主题风格**
  - 🌙 深色主题 (默认) - 护眼舒适
  - ☀️ 浅色主题 - 明亮清爽
  - 💙 蓝色主题 - 科技感十足
  - 💚 绿色主题 - 自然清新
  - 💜 紫色主题 - 优雅精致
- **主题持久化** - 自动保存用户偏好，跨设备同步
- **响应式设计** - 完美适配桌面、平板、手机

### 📂 对话管理
- **多对话支持** - 创建和管理多个独立对话
- **历史记录** - 按时间排序，快速查找
- **一键删除** - 轻松管理不需要的对话
- **自动标题** - 根据首条消息自动生成对话标题

---

## 📸 界面预览

- **登录页面** - 简洁的登录/注册界面
- **聊天界面** - 现代化的对话体验
- **主题切换** - 流畅的主题过渡效果
- **移动端** - 优化的触摸操作体验

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- OpenAI API Key 或 DeepSeek API Key

### 环境要求

- Python 3.8+
- pip 包管理器
- OpenAI API Key 或 DeepSeek API Key

### 安装步骤

#### 1. 进入项目目录

```bash
cd chat
```

#### 2. 创建虚拟环境(推荐)

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

#### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

复制 `.env.example` 创建 `.env` 文件:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key:

**使用 OpenAI:**
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

**使用 DeepSeek (推荐):**
```env
OPENAI_API_KEY=your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

#### 5. 启动应用

```bash
python app.py
```

看到以下提示表示启动成功:

```
==================================================
🚀 AI Chat Platform Starting...
==================================================
✅ API Key: 已配置
🔗 API URL: https://api.deepseek.com/v1
📝 访问地址: http://localhost:5000
==================================================
```

#### 6. 访问应用

在浏览器中打开: **http://localhost:5000**

---

## 📖 使用指南

### 首次使用

#### 步骤 1: 注册账户

1. 访问 http://localhost:5000
2. 点击"立即注册"链接
3. 填写注册信息:
   - **用户名**: 至少 3 个字符
   - **邮箱**: 选填
   - **密码**: 至少 6 个字符
   - **确认密码**: 再次输入密码
4. 点击"注册"按钮

#### 步骤 2: 登录系统

1. 输入用户名和密码
2. (可选) 勾选"记住我"保持 7 天登录
3. 点击"登录"按钮

#### 步骤 3: 开始对话

- **发送消息**: 在底部输入框输入内容，按 `Enter` 发送
- **换行**: 按 `Shift + Enter` 在消息中换行
- **快速开始**: 点击欢迎页的示例提示词

### 功能操作

#### 对话管理

- **新建对话**: 点击左上角 "➕ 新对话" 按钮
- **切换对话**: 点击左侧对话列表中的任意对话
- **删除对话**: 鼠标悬停在对话上，点击右侧 🗑️ 图标
- **查看历史**: 对话列表按更新时间自动排序

#### 模型切换

点击顶部的模型下拉菜单，选择不同的 AI 模型:

| 模型 | 适用场景 | 特点 |
|------|---------|------|
| **DeepSeek Chat** | 日常对话、问答 | 高性价比、响应快 |
| **DeepSeek Coder** | 编程、代码分析 | 专业编程能力 |
| **GPT-3.5 Turbo** | 通用任务 | 快速、经济 |
| **GPT-4** | 复杂任务 | 强大、准确 |

#### 主题设置

1. 点击右上角设置图标 ⚙️
2. 在弹出的设置窗口选择主题
3. 主题立即生效并自动保存

#### 退出登录

1. 鼠标悬停在左下角用户名处
2. 点击出现的退出图标 🚪
3. 确认退出

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift + Enter` | 换行 |

### 技能系统

AI 现在可以调用预定义的技能来获取实时信息：

**内置技能：**
- 📅 **get_current_date** - 获取当前日期和时间

**使用示例：**
```
用户: 今天几号？
AI: 今天是2024年1月15日，星期一。

用户: 现在几点了？
AI: 现在是下午3点25分。
```

查看 [skills/README.md](./skills/README.md) 了解如何开发自定义技能。

---

## 🏗️ 项目结构

```
chat/
├── app.py                      # Flask 后端主程序
├── requirements.txt            # Python 依赖列表
├── test_skills.py             # 技能系统测试脚本
├── .env                        # 环境变量配置 (需自行创建)
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略文件
├── run.bat                    # Windows 启动脚本
├── run.sh                     # Linux/Mac 启动脚本
├── fix_dependencies.bat       # 依赖修复脚本
├── README.md                  # 项目说明文档
├── FEATURES.md                # 功能详细说明
├── QUICKSTART.md              # 快速启动指南
├── TEST_CHECKLIST.md          # 测试检查清单
├── templates/                 # HTML 模板
│   ├── index.html            # 主聊天界面
│   ├── login.html            # 登录页面
│   └── register.html         # 注册页面
├── static/                    # 静态资源
│   ├── css/
│   │   ├── style.css         # 主样式文件
│   │   └── auth.css          # 认证页面样式
│   └── js/
│       ├── main.js           # 主交互逻辑
│       ├── login.js          # 登录逻辑
│       └── register.js       # 注册逻辑
├── skills/                    # 技能系统模块 (新增)
│   ├── __init__.py           # 模块初始化
│   ├── base.py               # 基础技能类和注册表
│   ├── date_skill.py         # 日期时间技能
│   └── README.md             # 技能开发文档
└── venv/                      # Python 虚拟环境 (需自行创建)
```
├── QUICKSTART.md              # 快速启动指南
├── TEST_CHECKLIST.md          # 测试检查清单
├── templates/                 # HTML 模板
│   ├── index.html            # 主聊天界面
│   ├── login.html            # 登录页面
│   └── register.html         # 注册页面
├── static/                    # 静态资源
│   ├── css/
│   │   ├── style.css         # 主样式文件
│   │   └── auth.css          # 认证页面样式
│   └── js/
│       ├── main.js           # 主交互逻辑
│       ├── login.js          # 登录逻辑
│       └── register.js       # 注册逻辑
└── venv/                      # Python 虚拟环境 (需自行创建)
```

---

## 🔧 API 接口文档

### 认证接口

#### POST /api/register
用户注册

**请求体:**
```json
{
  "username": "demo",
  "password": "123456",
  "email": "demo@example.com"
}
```

**响应:**
```json
{
  "success": true,
  "message": "注册成功"
}
```

#### POST /api/login
用户登录

**请求体:**
```json
{
  "username": "demo",
  "password": "123456"
}
```

**响应:**
```json
{
  "success": true,
  "username": "demo",
  "theme": "dark"
}
```

#### POST /api/logout
用户登出

**响应:**
```json
{
  "success": true
}
```

### 用户接口

#### GET /api/user
获取当前用户信息 (需要登录)

**响应:**
```json
{
  "username": "demo",
  "email": "demo@example.com",
  "theme": "dark",
  "created_at": "2024-01-01T00:00:00"
}
```

#### PUT /api/user/theme
更新用户主题 (需要登录)

**请求体:**
```json
{
  "theme": "blue"
}
```

**响应:**
```json
{
  "success": true,
  "theme": "blue"
}
```

### 对话接口

#### POST /api/chat
发送消息并获取 AI 回复 (需要登录，流式响应)

**请求体:**
```json
{
  "message": "你好",
  "conversation_id": "uuid-string",
  "model": "deepseek-chat"
}
```

**响应:** Server-Sent Events (SSE) 流

```
data: {"content": "你"}
data: {"content": "好"}
data: {"content": "！"}
data: {"done": true}
```

#### GET /api/conversations
获取所有对话列表 (需要登录)

**响应:**
```json
{
  "conversations": [
    {
      "id": "uuid-string",
      "title": "对话标题",
      "updated_at": "2024-01-01T00:00:00",
      "message_count": 10
    }
  ]
}
```

#### GET /api/conversations/:id
获取特定对话的消息历史 (需要登录和所有权验证)

**响应:**
```json
{
  "conversation_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2024-01-01T00:00:00"
    },
    {
      "role": "assistant",
      "content": "你好！有什么我可以帮助你的吗？",
      "timestamp": "2024-01-01T00:00:01"
    }
  ]
}
```

#### DELETE /api/conversations/:id
删除特定对话 (需要登录和所有权验证)

**响应:**
```json
{
  "success": true
}
```

#### GET /api/models
获取可用模型列表

**响应:**
```json
{
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "description": "强大的对话模型"
    }
  ]
}
```

### 健康检查

#### GET /health
服务健康检查

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## 🎨 技术特性

### 前端技术

- **原生 JavaScript** - 无框架依赖，轻量高效
- **CSS3 动画** - 流畅的过渡效果
- **Server-Sent Events** - 实时流式数据传输
- **Responsive Design** - 移动端优先设计
- **LocalStorage** - 客户端状态缓存

### 后端技术

- **Flask** - 轻量级 Python Web 框架
- **Flask-CORS** - 跨域资源共享支持
- **OpenAI SDK** - 统一的 AI API 接口
- **Werkzeug Security** - 密码安全加密
- **Python dotenv** - 环境变量管理

### 安全特性

- ✅ **密码哈希** - bcrypt 加密存储
- ✅ **会话管理** - Flask Session 安全机制
- ✅ **对话隔离** - 用户数据完全隔离
- ✅ **权限验证** - API 接口访问控制
- ✅ **CORS 配置** - 跨域请求安全策略

---

## ⚠️ 重要说明

### 当前限制

> **⚠️ 本项目当前使用内存存储数据，仅适用于开发和测试！**

- **数据持久性**: 重启服务后所有数据丢失
  - 用户账户
  - 对话历史
  - 主题设置
  
- **并发限制**: 单进程运行，不支持水平扩展
- **缺失功能**: 
  - 邮箱验证
  - 密码找回
  - 头像上传
  - 对话导出

### 生产环境部署建议

如需在生产环境使用，请进行以下升级:

#### 1. 使用数据库

**推荐方案:**
- **SQLite** - 小型应用，单文件存储
- **PostgreSQL** - 大型应用，高并发
- **MongoDB** - 文档型数据，灵活

**数据表设计:**

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    theme VARCHAR(20) DEFAULT 'dark',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话表
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**Flask-SQLAlchemy 集成:**

```bash
pip install flask-sqlalchemy
```

```python
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
```

#### 2. 使用生产级服务器

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务 (4个工作进程)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 3. 配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # SSE 支持
    location /api/chat {
        proxy_pass http://localhost:5000;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
```

#### 4. 启用 HTTPS

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### 5. 环境变量配置

```bash
# 生成强随机密钥
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 设置生产模式
export FLASK_ENV=production

# 配置数据库
export DATABASE_URL=postgresql://user:pass@localhost/chatdb
```

#### 6. 安全加固

- ✅ 启用 CSRF 保护
- ✅ 配置 Rate Limiting
- ✅ 添加日志监控
- ✅ 定期备份数据库
- ✅ 使用 Docker 容器化

---

## 🐛 故障排查

### 问题 1: 启动失败

**症状**: 运行 `python app.py` 报错

**解决方案:**
```bash
# 检查 Python 版本 (需要 3.8+)
python --version

# 重新安装依赖
pip install -r requirements.txt --upgrade

# 检查端口占用
netstat -ano | findstr :5000    # Windows
lsof -i :5000                   # macOS/Linux
```

### 问题 2: API 请求失败

**症状**: 发送消息后提示错误

**解决方案:**
1. 检查 `.env` 文件是否存在
2. 验证 API Key 是否正确
3. 确认 `OPENAI_BASE_URL` 与 API 提供商匹配
4. 检查网络连接
5. 查看终端错误日志

**DeepSeek API 配置:**
```env
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

**OpenAI API 配置:**
```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 问题 3: 登录后立即跳转

**症状**: 登录成功但又回到登录页

**解决方案:**
1. 检查浏览器 Cookie 设置
2. 清除浏览器缓存和 Cookie
3. 尝试无痕/隐私模式
4. 查看浏览器控制台错误
5. 确认 `SECRET_KEY` 已配置

### 问题 4: 主题切换无效

**症状**: 点击主题后界面没变化

**解决方案:**
1. 刷新页面
2. 清除浏览器缓存
3. 检查浏览器控制台错误
4. 验证是否已登录

### 问题 5: 对话历史丢失

**说明**: 这是正常现象！

当前版本使用内存存储，重启服务后所有数据将丢失:
- 用户账户
- 对话历史
- 主题设置

**解决方案**: 参考"生产环境部署建议"部分使用数据库

### 问题 6: 流式响应中断

**症状**: AI 回复到一半停止

**解决方案:**
1. 检查网络连接稳定性
2. 增加 API 超时时间
3. 检查 API 配额是否用尽
4. 查看服务器日志

---

## 📚 文档索引

- **[FEATURES.md](FEATURES.md)** - 详细功能说明和使用方法
- **[QUICKSTART.md](QUICKSTART.md)** - 快速启动和测试指南
- **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** - 完整的功能测试清单

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发建议

- 保持代码风格一致
- 添加必要的注释
- 更新相关文档
- 测试所有功能

---

## 📄 开源协议

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📧 联系方式

- **问题反馈**: 请在 GitHub Issues 中提交
- **功能建议**: 欢迎在 Issues 中讨论
- **安全问题**: 请私下联系维护者

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - 优秀的 Python Web 框架
- [OpenAI](https://openai.com/) - 强大的 AI API
- [DeepSeek](https://www.deepseek.com/) - 高性价比的 AI 服务
- 所有贡献者和使用者

---

<div align="center">

**享受与 AI 的智能对话！ 🚀**

Made with ❤️ by the Community

</div>
