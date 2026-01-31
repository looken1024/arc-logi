# AI Chat Platform

一个类似 DeepSeek 风格的 AI 对话平台，使用 Python Flask 后端和现代化的前端界面。

## ✨ 特性

- 🎨 **现代化界面** - 参考 DeepSeek 的深色主题设计
- 💬 **实时流式对话** - 支持流式返回，实时显示 AI 回复
- 🤖 **多模型支持** - 支持 GPT-3.5、GPT-4、DeepSeek 等模型
- 💾 **对话管理** - 自动保存对话历史，支持查看和删除
- 📱 **响应式设计** - 完美适配桌面和移动设备
- 🎯 **简洁易用** - 直观的用户界面，快速上手
- 🔐 **用户系统** - 注册/登录，对话隔离，会话管理
- 🎨 **主题切换** - 5种主题随心选择，设置自动保存
- 👤 **用户信息** - 显示用户名，个性化体验

## 🆕 最新更新

### v2.0 新功能
- ✅ **用户注册和登录系统**
- ✅ **5种主题颜色可选** (深色/浅色/蓝色/绿色/紫色)
- ✅ **用户对话隔离** (每个用户只能看到自己的对话)
- ✅ **主题设置持久化** (自动保存偏好设置)
- ✅ **会话管理** (7天免登录)
- ✅ **显示用户名** (聊天界面显示当前用户)

详见 [FEATURES.md](FEATURES.md) 查看完整功能说明。

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装步骤

1. **克隆或进入项目目录**

```bash
cd chat
```

2. **创建虚拟环境(推荐)**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

复制 `.env.example` 为 `.env` 并填入你的 API Key:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

**使用 DeepSeek API:**

```env
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

5. **运行应用**

```bash
python app.py
```

6. **访问应用**

打开浏览器访问: http://localhost:5000

## 📁 项目结构

```
chat/
├── app.py                 # Flask 后端主文件
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── .gitignore            # Git 忽略文件
├── README.md             # 项目说明
├── templates/
│   └── index.html        # 主页模板
└── static/
    ├── css/
    │   └── style.css     # 样式文件
    └── js/
        └── main.js       # 前端交互逻辑
```

## 🎯 功能说明

### 对话功能

- **发送消息**: 在输入框输入消息，按 Enter 发送(Shift+Enter 换行)
- **流式回复**: AI 回复会实时逐字显示
- **新建对话**: 点击左上角"新对话"按钮创建新对话
- **查看历史**: 左侧边栏显示所有对话历史
- **删除对话**: 鼠标悬停在对话上，点击删除图标

### 模型切换

在顶部模型选择器中可以切换不同的 AI 模型:
- GPT-3.5 Turbo (快速、经济)
- GPT-4 (强大、准确)
- DeepSeek Chat (高性价比)

### 快捷示例

首页提供了快速示例提示词，点击即可快速开始对话。

## 🔧 API 接口

### POST /api/chat
发送消息并获取 AI 回复(流式)

**请求体:**
```json
{
  "message": "你好",
  "conversation_id": "uuid",
  "model": "gpt-3.5-turbo"
}
```

**响应:** Server-Sent Events (SSE) 流

### GET /api/conversations
获取所有对话列表

### GET /api/conversations/{id}
获取特定对话的消息历史

### DELETE /api/conversations/{id}
删除特定对话

## 🎨 界面特性

- **深色主题**: 护眼的深色界面
- **流畅动画**: 消息渐入、打字效果等
- **代码高亮**: 支持代码块格式化显示
- **Markdown 支持**: 支持基础 Markdown 格式
- **响应式布局**: 自适应不同屏幕尺寸

## 🔐 安全建议

1. **不要将 `.env` 文件提交到版本控制**
2. **定期更换 API Key**
3. **在生产环境中使用 HTTPS**
4. **添加用户认证和授权机制**
5. **使用数据库存储对话(而非内存)**

## 📝 开发建议

### 使用数据库

当前对话存储在内存中，重启服务会丢失。建议在生产环境中使用数据库:

```python
# 可选数据库
- SQLite (简单、文件存储)
- PostgreSQL (强大、可扩展)
- MongoDB (文档型、灵活)
```

### 添加用户系统

```python
from flask_login import LoginManager, UserMixin, login_required
```

### 部署到生产环境

```bash
# 使用 gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 或使用 Nginx 反向代理
```

## 🐛 常见问题

**Q: API 请求失败怎么办?**
A: 检查 `.env` 文件中的 API Key 是否正确，以及网络连接是否正常。

**Q: 如何使用 DeepSeek API?**
A: 在 `.env` 中设置 `OPENAI_BASE_URL=https://api.deepseek.com/v1` 和相应的 API Key。

**Q: 对话历史丢失了?**
A: 当前版本使用内存存储，重启服务会丢失数据。请参考"使用数据库"部分进行改进。

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**享受与 AI 的对话吧! 🚀**
