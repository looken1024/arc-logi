# 🚀 快速启动指南

## 第一次使用

### 1. 安装依赖 (首次)

如果是第一次启动,需要安装依赖:

```bash
# 进入项目目录
cd chat

# 创建虚拟环境(推荐)
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

确保 `.env` 文件存在并配置了正确的 API Key:

```env
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 3. 启动服务

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

### 4. 访问应用

在浏览器打开: **http://localhost:5000**

## 首次使用流程

### 步骤 1: 注册账户

1. 访问 http://localhost:5000
2. 自动跳转到登录页
3. 点击底部"立即注册"链接
4. 填写信息:
   - 用户名: 至少3个字符 (例: `demo`)
   - 邮箱: 可选
   - 密码: 至少6个字符 (例: `123456`)
   - 确认密码: 再次输入密码
5. 点击"注册"按钮
6. 注册成功后自动跳转到登录页

### 步骤 2: 登录

1. 输入刚注册的用户名和密码
2. (可选)勾选"记住我"
3. 点击"登录"按钮
4. 登录成功,进入聊天页面

### 步骤 3: 开始对话

1. 在底部输入框输入消息
2. 按 Enter 发送 (Shift+Enter 换行)
3. 等待 AI 回复

或点击欢迎页面的示例提示词快速开始!

### 步骤 4: 切换主题(可选)

1. 点击右上角设置图标 ⚙️
2. 选择喜欢的主题:
   - 🌙 深色 (默认)
   - ☀️ 浅色
   - 💙 蓝色
   - 💚 绿色
   - 💜 紫色
3. 主题立即生效并自动保存

## 常用操作

### 创建新对话
- 点击左上角"➕ 新对话"按钮

### 查看历史对话
- 点击左侧对话列表中的任意对话

### 删除对话
- 鼠标悬停在对话上
- 点击右侧出现的删除图标 🗑️

### 切换模型
- 点击顶部下拉菜单选择模型
- DeepSeek Chat: 通用对话
- DeepSeek Coder: 编程专用

### 退出登录
- 鼠标悬停在左下角用户名上
- 点击退出图标 🚪

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift + Enter` | 换行 |

## 故障排查

### 问题 1: 无法启动服务

**症状**: 运行 `python app.py` 报错

**解决方案**:
```bash
# 检查 Python 版本 (需要 3.8+)
python --version

# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### 问题 2: API 请求失败

**症状**: 发送消息后提示 "Model Not Exist" 或其他错误

**解决方案**:
1. 检查 `.env` 文件中的 API Key 是否正确
2. 检查 `OPENAI_BASE_URL` 是否匹配 API 提供商
3. DeepSeek API 使用模型: `deepseek-chat` 或 `deepseek-coder`
4. OpenAI API 使用模型: `gpt-3.5-turbo` 或 `gpt-4`

### 问题 3: 登录后跳转到登录页

**症状**: 刚登录完又回到登录页

**解决方案**:
1. 检查浏览器是否禁用了 Cookie
2. 清除浏览器缓存和 Cookie
3. 使用无痕模式测试
4. 检查浏览器控制台错误信息

### 问题 4: 主题切换不生效

**症状**: 点击主题后界面没有变化

**解决方案**:
1. 刷新页面
2. 清除浏览器缓存
3. 检查浏览器控制台错误信息

### 问题 5: 重启后数据丢失

**说明**: 这是正常现象!

当前版本使用内存存储,重启服务会丢失:
- 所有用户账户
- 所有对话历史
- 所有设置

**解决方案**: 生产环境请使用数据库(见下方)

## 生产环境部署

⚠️ **重要**: 当前版本仅适合开发测试!

生产环境建议:

1. **使用数据库**
   ```bash
   pip install flask-sqlalchemy
   # 配置 SQLite/PostgreSQL/MySQL
   ```

2. **使用生产服务器**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **配置 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书

4. **设置环境变量**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=生成强随机密钥
   ```

## 下一步

- 📖 查看 [FEATURES.md](FEATURES.md) 了解完整功能
- ✅ 使用 [TEST_CHECKLIST.md](TEST_CHECKLIST.md) 测试所有功能
- 💡 查看代码学习实现细节

## 需要帮助?

遇到问题? 请:
1. 查看上方"故障排查"部分
2. 检查终端错误信息
3. 检查浏览器控制台错误
4. 提交 Issue 描述问题

---

**开始您的 AI 对话之旅! 🎉**
