# Git 使用技能

提供常用 Git 命令的快速参考和说明。

## 功能描述

此技能提供 Git 版本控制系统的常用命令参考，帮助用户快速查找和使用 Git 命令。当用户询问 Git 相关操作时，AI 可以调用此技能提供相应的命令指导。

## 常用命令表格

### 基础操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 初始化仓库 | `git init` | 在当前目录创建新的 Git 仓库 |
| 克隆仓库 | `git clone <url>` | 克隆远程仓库到本地 |
| 查看状态 | `git status` | 查看工作区状态 |
| 查看差异 | `git diff` | 查看未暂存的修改 |
| 添加文件 | `git add <file>` | 将文件添加到暂存区 |
| 提交更改 | `git commit -m "message"` | 提交暂存区的更改 |
| 查看日志 | `git log` | 查看提交历史 |
| 查看帮助 | `git help <command>` | 查看命令帮助 |

### 分支操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看分支 | `git branch` | 列出所有本地分支 |
| 查看远程分支 | `git branch -r` | 列出所有远程分支 |
| 创建分支 | `git branch <name>` | 创建新分支 |
| 切换分支 | `git checkout <branch>` | 切换到指定分支 |
| 创建并切换 | `git checkout -b <name>` | 创建并切换到新分支 |
| 删除分支 | `git branch -d <name>` | 删除本地分支 |
| 合并分支 | `git merge <branch>` | 将指定分支合并到当前分支 |

### 远程操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看远程 | `git remote -v` | 查看远程仓库详情 |
| 添加远程 | `git remote add <name> <url>` | 添加远程仓库 |
| 拉取代码 | `git pull` | 拉取并合并远程更改 |
| 推送代码 | `git push` | 推送到远程仓库 |
| 推送分支 | `git push -u origin <branch>` | 推送分支并设置上游 |

### 撤销操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 撤销修改 | `git checkout -- <file>` | 撤销工作区修改 |
| 取消暂存 | `git reset HEAD <file>` | 取消文件的暂存 |
| 撤销提交 | `git reset --soft HEAD~1` | 撤销最近一次提交（保留修改） |
| 彻底撤销 | `git reset --hard HEAD~1` | 撤销最近一次提交（丢弃修改） |

### 暂存操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 暂存修改 | `git stash` | 暂存当前工作区修改 |
| 查看暂存 | `git stash list` | 查看所有暂存 |
| 恢复暂存 | `git stash pop` | 恢复并删除最近暂存 |
| 删除暂存 | `git stash drop` | 删除最近暂存 |

### 标签操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 创建标签 | `git tag <name>` | 创建轻量标签 |
| 创建附注标签 | `git tag -a <name> -m "msg"` | 创建附注标签 |
| 推送标签 | `git push origin <tag>` | 推送标签到远程 |
| 删除本地标签 | `git tag -d <name>` | 删除本地标签 |
| 删除远程标签 | `git push origin --delete <tag>` | 删除远程标签 |

## 使用场景

- 询问某个 Git 命令："git 怎么撤销提交？"
- 询问如何操作："如何创建分支？"
- 遇到问题寻求帮助："git pull 失败了怎么办？"

## 返回值

返回 JSON 对象，包含命令说明和使用示例：

```json
{
  "command": "git reset --hard HEAD~1",
  "description": "彻底撤销最近一次提交，丢弃所有修改",
  "warning": "此操作不可恢复，请谨慎使用",
  "category": "撤销操作",
  "example": "git reset --hard HEAD~1"
}
```

## 使用示例

### 示例 1: 撤销提交

**用户**: 怎么撤销最后一次提交？

**AI 调用**:
```json
{
  "function": "git_usage",
  "arguments": {
    "command": "reset"
  }
}
```

**返回**:
```json
{
  "command": "git reset --soft HEAD~1",
  "description": "撤销最近一次提交，保留修改在暂存区",
  "category": "撤销操作",
  "alternatives": [
    {
      "command": "git reset --hard HEAD~1",
      "description": "彻底撤销提交，丢弃所有修改"
    }
  ]
}
```

**AI 回复**: 可以使用 `git reset --soft HEAD~1` 来撤销最近一次提交，修改会保留在暂存区。如果想彻底丢弃修改，使用 `git reset --hard HEAD~1`（请谨慎使用）。

### 示例 2: 创建分支

**用户**: 怎么创建并切换到新分支？

**AI 调用**:
```json
{
  "function": "git_usage",
  "arguments": {
    "command": "checkout -b"
  }
}
```

**返回**:
```json
{
  "command": "git checkout -b <branch-name>",
  "description": "创建新分支并立即切换到该分支",
  "category": "分支操作",
  "example": "git checkout -b feature/new-feature"
}
```

## 错误处理

如果执行过程中出现错误，返回格式如下：

```json
{
  "error": "获取 Git 命令帮助失败: [错误详情]"
}
```

## 版本历史

- **v1.0** (2024-02-15): 初始版本
  - 提供常用 Git 命令表格
  - 支持按类别查询命令
  - 提供命令说明和使用示例

## 作者

AI Chat Platform Skills Team

## 许可证

MIT License
