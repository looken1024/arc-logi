# 🎯 ARC-Logic 综合工具集

一个集成多种实用工具的综合项目，包含 AI 对话平台、AI 编程助手、表情包小程序和任务调度系统。

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20JavaScript%20%7C%20TypeScript-orange.svg)
![Platform](https://img.shields.io/badge/platform-Web%20%7C%20CLI-brightgreen.svg)

</div>

---

## 📦 项目概览

本项目包含四个独立但互补的工具应用：

| 项目 | 类型 | 技术栈 | 说明 |
|------|------|--------|------|
| **[Chat](#-chat---ai-对话平台)** | Web 应用 | Python Flask + JavaScript | DeepSeek 风格的 AI 对话平台 |
| **[Coding](#-coding---ai-编程助手)** | CLI 工具 | TypeScript + Node.js | 命令行 AI 编程助手 |
| **[Emoji](#-emoji---表情包小程序)** | Web 应用 | HTML5 + CSS3 + JavaScript | 移动端表情包浏览器 |
| **[Scheduler](#-scheduler---任务调度系统)** | Web 应用 | HTML5 + CSS3 + JavaScript | 可视化任务调度管理 |

---

## 🤖 Chat - AI 对话平台

### 简介
一个功能完整的 AI 对话平台，提供现代化的用户体验，支持多模型、多用户、多主题。

### ✨ 核心特性
- 🎨 **5种主题风格** - 深色/浅色/蓝色/绿色/紫色
- 💬 **实时流式对话** - AI 回复逐字显示
- 🔐 **用户系统** - 注册/登录/会话管理
- 🤖 **多模型支持** - DeepSeek Chat/Coder、GPT-3.5/4
- 📂 **对话管理** - 创建、查看、删除对话历史
- 📱 **响应式设计** - 完美适配各种设备

### 🚀 快速开始

```bash
# 进入项目目录
cd chat

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 .env 文件
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动应用
python app.py

# 访问 http://localhost:5000
```

### 📚 详细文档
查看 [chat/README.md](./chat/README.md) 了解完整功能和使用说明。

---

## 💻 Coding - AI 编程助手

### 简介
强大的命令行 AI 编程工具，类似 Trae，支持代码生成、分析和重构。

### ✨ 核心特性
- 🤖 **多模型支持** - OpenAI GPT、Google Gemini、DeepSeek
- 🎯 **代码生成** - 自然语言生成代码
- 🔍 **代码分析** - 质量检查和改进建议
- 🔧 **代码重构** - 智能重构和优化
- 📁 **文件管理** - 完整的工作区管理
- 💬 **交互式 CLI** - 友好的命令行界面

### 🚀 快速开始

```bash
# 进入项目目录
cd coding

# 安装依赖
npm install

# 构建项目
npm run build

# 全局安装(可选)
npm install -g .

# 初始化配置
aicoding init openai your_api_key
# 或
aicoding init deepseek your_api_key

# 开始使用
aicoding
> generate Create a React component
> analyze src/App.js
> refactor old-code.js use modern ES6 syntax
```

### 📚 详细文档
查看 [coding/README.md](./coding/README.md) 了解完整功能和 API 文档。

---

## 😄 Emoji - 表情包小程序

### 简介
基于 H5 的移动端表情包小程序，支持浏览、搜索、收藏和分享。

### ✨ 核心特性
- 🎯 **表情包管理** - 浏览、搜索、收藏、分享
- 📱 **移动端优化** - 完美适配所有手机屏幕
- 🎨 **分类筛选** - 热门、搞笑、萌系、表情、梗图
- 🌙 **暗黑模式** - 自动适配系统主题
- ⚡ **性能优化** - 图片懒加载、无限滚动
- 💾 **离线收藏** - 本地存储收藏数据

### 🚀 快速开始

```bash
# 进入项目目录
cd emoji

# 直接在浏览器打开
# 方式1: 双击 index.html
# 方式2: 使用本地服务器
python -m http.server 8000
# 访问 http://localhost:8000
```

### 📱 移动端访问
- 支持所有现代移动浏览器
- iOS Safari 12+
- Chrome Mobile 80+
- 微信/支付宝内置浏览器

### 📚 详细文档
查看 [emoji/README.md](./emoji/README.md) 了解配置和部署说明。

---

## 📅 Scheduler - 任务调度系统

### 简介
可视化的任务调度管理系统，支持任务创建、执行监控和依赖管理。

### ✨ 核心特性
- ⏰ **任务调度** - 支持定时、周期性任务
- 📊 **可视化监控** - 实时查看任务状态
- 🔗 **依赖管理** - 任务依赖关系配置
- 📈 **执行统计** - 任务执行历史和统计
- 🎨 **现代化UI** - 简洁美观的用户界面
- 📱 **响应式设计** - 支持移动端操作

### 🚀 快速开始

```bash
# 进入项目目录
cd scheduler

# 在浏览器中打开
# 方式1: 双击 scheduler.html
# 方式2: 使用本地服务器
python -m http.server 8080
# 访问 http://localhost:8080/scheduler.html
```

### 🎯 主要功能
- **新建任务** - 创建单次或周期性任务
- **任务组管理** - 按组织结构管理任务
- **执行监控** - 实时查看任务执行状态
- **依赖配置** - 设置任务执行依赖关系
- **历史记录** - 查看任务执行历史

---

## 🏗️ 项目结构

```
arc-logic/
├── chat/                          # AI 对话平台
│   ├── app.py                    # Flask 后端
│   ├── templates/                # HTML 模板
│   ├── static/                   # 静态资源
│   ├── requirements.txt          # Python 依赖
│   └── README.md                 # 详细文档
│
├── coding/                        # AI 编程助手
│   ├── src/                      # TypeScript 源码
│   ├── dist/                     # 编译输出
│   ├── package.json              # Node.js 配置
│   └── README.md                 # 详细文档
│
├── emoji/                         # 表情包小程序
│   ├── index.html                # 主页面
│   ├── styles.css                # 样式文件
│   ├── script.js                 # 业务逻辑
│   └── README.md                 # 详细文档
│
├── scheduler/                     # 任务调度系统
│   ├── scheduler.html            # 主页面
│   ├── scheduler.css             # 样式文件
│   ├── scheduler.js              # 业务逻辑
│   └── README.md                 # (待创建)
│
├── venv/                          # Python 虚拟环境
└── README.md                      # 本文件
```

---

## 🛠️ 技术栈

### Chat 项目
- **后端**: Python 3.8+, Flask, Flask-CORS
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **AI**: OpenAI API, DeepSeek API
- **安全**: Werkzeug Security, bcrypt

### Coding 项目
- **语言**: TypeScript, Node.js
- **构建**: npm, tsc
- **AI**: OpenAI SDK, Google Gemini, DeepSeek

### Emoji & Scheduler 项目
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **布局**: Flexbox, Grid
- **优化**: 懒加载, 防抖, 本地存储

---

## 📋 环境要求

### 通用要求
- 现代浏览器 (Chrome 80+, Firefox 80+, Safari 12+)
- 网络连接 (用于 AI API 调用)

### Chat 项目
- Python 3.8+
- pip 包管理器
- OpenAI/DeepSeek API Key

### Coding 项目
- Node.js 14+
- npm 或 yarn
- OpenAI/Gemini/DeepSeek API Key

### Emoji & Scheduler 项目
- 无特殊要求，浏览器直接打开

---

## 🚀 快速启动全部项目

### 1. Chat 平台
```bash
cd chat
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # 配置 API Key
python app.py
# 访问 http://localhost:5000
```

### 2. Coding 助手
```bash
cd coding
npm install
npm run build
npm install -g .
aicoding init deepseek your_api_key
aicoding
```

### 3. Emoji 小程序
```bash
cd emoji
python -m http.server 8000
# 访问 http://localhost:8000
```

### 4. Scheduler 系统
```bash
cd scheduler
python -m http.server 8080
# 访问 http://localhost:8080/scheduler.html
```

---

## 📖 使用场景

### Chat 平台适合
- 🎓 学习交流 - 与 AI 进行问答学习
- 💼 工作助手 - 快速获取信息和建议
- 💻 编程辅助 - DeepSeek Coder 专业编程支持
- 📝 内容创作 - 文案、创意、翻译等

### Coding 助手适合
- 🚀 快速开发 - 自动生成样板代码
- 🔍 代码审查 - 分析代码质量
- 🔧 代码重构 - 自动优化代码
- 📚 学习参考 - 生成示例代码

### Emoji 小程序适合
- 💬 聊天沟通 - 快速找到合适的表情
- 🎉 社交分享 - 收藏和分享有趣表情
- 📱 移动端使用 - 随时随地浏览表情包

### Scheduler 系统适合
- ⏰ 任务管理 - 定时任务调度
- 📊 项目监控 - 任务执行状态跟踪
- 🔗 工作流程 - 复杂任务依赖管理
- 📈 数据统计 - 任务执行分析

---

## 🔐 安全说明

### API Key 安全
- ⚠️ **不要将 API Key 提交到版本控制**
- ✅ 使用 `.env` 文件存储敏感信息
- ✅ `.env` 文件已添加到 `.gitignore`
- ✅ 定期更换 API Key

### 数据安全
- Chat 项目当前使用**内存存储**，重启后数据丢失
- 生产环境建议使用数据库（SQLite/PostgreSQL/MongoDB）
- 密码使用 bcrypt 哈希加密存储
- 用户数据完全隔离

### 部署安全
- 🔒 生产环境务必启用 HTTPS
- 🛡️ 配置 CORS 策略限制访问来源
- 🔑 使用强随机密钥（SECRET_KEY）
- 📝 启用日志记录和监控

---

## 🐛 常见问题

### Q1: Chat 平台重启后数据丢失？
**A**: 当前版本使用内存存储，这是正常现象。生产环境请参考 [chat/README.md](./chat/README.md) 配置数据库。

### Q2: Coding 助手 API 调用失败？
**A**: 检查以下几点：
1. API Key 是否正确配置
2. 网络连接是否正常
3. API 配额是否用尽
4. BASE_URL 是否与模型匹配

### Q3: Emoji 小程序图片不显示？
**A**: 当前使用占位图片。修改 `script.js` 中的图片 URL 为实际地址。

### Q4: Scheduler 任务没有真正执行？
**A**: 这是一个前端演示项目。真实任务执行需要后端支持，可以集成 cron 或其他调度器。

### Q5: 如何同时运行多个项目？
**A**: 每个项目使用不同端口：
- Chat: 5000
- Emoji: 8000
- Scheduler: 8080
- Coding: CLI 工具，不占用端口

---

## 🔄 开发计划

### Chat 平台
- [ ] 数据库集成 (SQLite/PostgreSQL)
- [ ] 邮箱验证和密码找回
- [ ] 对话导出功能 (Markdown/PDF)
- [ ] 更多主题和自定义配色
- [ ] 头像上传和个人资料
- [ ] 对话分享功能

### Coding 助手
- [ ] 支持更多 AI 模型
- [ ] 添加代码测试生成
- [ ] 集成代码格式化工具
- [ ] 支持项目模板生成
- [ ] 添加代码补全功能
- [ ] Web UI 界面

### Emoji 小程序
- [ ] 集成真实表情包 API
- [ ] 表情包上传功能
- [ ] 在线编辑表情包
- [ ] 用户评论和评分
- [ ] 批量操作支持
- [ ] PWA 支持离线使用

### Scheduler 系统
- [ ] 后端 API 支持
- [ ] 真实任务执行引擎
- [ ] Cron 表达式支持
- [ ] 任务日志查看
- [ ] 告警通知功能
- [ ] Docker 部署支持

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献

1. **Fork 本仓库**
2. **创建功能分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **开启 Pull Request**

### 贡献类型

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 修复问题
- ✨ 添加新功能
- 🎨 改进 UI/UX

### 代码规范

- 遵循现有代码风格
- 添加必要的注释
- 更新相关文档
- 测试所有更改

---

## 📄 开源协议

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### MIT License 说明

✅ 商业使用
✅ 修改
✅ 分发
✅ 私人使用

⚠️ 无责任保证
⚠️ 无担保

---

## 📧 联系方式

- **问题反馈**: 在 GitHub Issues 中提交
- **功能建议**: 在 Issues 中讨论
- **安全问题**: 请私下联系项目维护者
- **交流讨论**: 欢迎在 Discussions 中参与

---

## 🙏 致谢

### 技术支持
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
- [OpenAI](https://openai.com/) - AI API 服务
- [DeepSeek](https://www.deepseek.com/) - 高性价比 AI 服务
- [Google Gemini](https://deepmind.google/technologies/gemini/) - Google AI

### 开源工具
- [Node.js](https://nodejs.org/) - JavaScript 运行时
- [TypeScript](https://www.typescriptlang.org/) - 类型安全的 JavaScript
- [Font Awesome](https://fontawesome.com/) - 图标库
- [Mermaid](https://mermaid.js.org/) - 图表绘制

### 社区贡献
感谢所有贡献者和使用者！

---

## 🌟 项目亮点

- ✅ **全栈技术栈** - Python, TypeScript, JavaScript
- ✅ **现代化设计** - 响应式、主题切换、流畅动画
- ✅ **AI 驱动** - 集成多个主流 AI 模型
- ✅ **开箱即用** - 详细文档，快速部署
- ✅ **持续更新** - 活跃维护，功能丰富
- ✅ **开源免费** - MIT 协议，自由使用

---

## 📊 项目统计

```
总代码行数: 20,000+
项目数量: 4
支持语言: Python, TypeScript, JavaScript
文档页数: 10+
依赖包数: 50+
```

---

<div align="center">

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐

**感谢使用 ARC-Logic 工具集！**

Made with ❤️ by the Community

[⬆ 回到顶部](#-arc-logic-综合工具集)

</div>
