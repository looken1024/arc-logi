# Knowledge Base Skill - 知识库技能

## 功能概述

知识库技能提供智能化的知识管理和分析能力，支持知识的创建、查询、版本管理和智能分析。

## 核心功能

### 1. 知识写入 (Write)
- 支持结构化数据存储：文本、标签、分类、元数据
- 自动版本管理和历史记录
- 智能分类和标签推荐
- 批量导入支持

### 2. 知识查询 (Read/Search)
- 全文搜索和语义搜索
- 多维度筛选：关键词、标签、分类、时间范围
- 知识关联发现和推荐
- 模糊匹配和拼写纠错

### 3. 知识分析 (Analyze)
- 知识图谱构建和可视化
- 趋势分析和热点发现
- 知识质量评估
- 自动摘要和关键信息提取

## 使用方法

### 在对话中使用

用户可以通过自然语言与知识库交互：

```
用户: 将"Python最佳实践包括：使用虚拟环境、遵循PEP8、编写单元测试"写入知识库
用户: 查询知识库中关于Python的所有内容
用户: 分析知识库的内容趋势
用户: 知识库有哪些分类？
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | 操作类型：write/search/analyze/list/stats |
| content | string | 否 | 知识内容（write时必填） |
| title | string | 否 | 知识标题 |
| tags | array | 否 | 标签列表 |
| category | string | 否 | 分类 |
| knowledge_base_id | integer | 否 | 知识库ID（默认使用用户主知识库） |
| query | string | 否 | 搜索关键词（search时使用） |
| filters | object | 否 | 筛选条件 |

## 技术架构

### 数据库设计
- `knowledge_base`: 知识库主表
- `knowledge_item`: 知识条目表
- `knowledge_relation`: 知识关系表
- `knowledge_tag`: 标签表
- `knowledge_version`: 版本历史表
- `knowledge_category`: 分类表
- `knowledge_history`: 操作历史表

### API 端点
- `GET /api/knowledge-bases` - 获取知识库列表
- `POST /api/knowledge-bases` - 创建知识库
- `GET /api/knowledge-bases/<id>/items` - 获取知识条目
- `POST /api/knowledge-bases/<id>/items` - 创建知识条目
- `GET /api/knowledge-bases/<id>/search` - 搜索知识
- `GET /api/knowledge-bases/<id>/graph` - 获取知识图谱
- `GET /api/knowledge-bases/<id>/stats` - 获取统计信息

### 权限管理
- 用户级权限：每个用户有独立的知识库
- 知识库级权限：公开/私有/指定用户访问
- 操作级权限：读/写/管理

## 扩展功能

### 知识图谱
- 节点类型：text、qa、concept、procedure
- 关系类型：related、parent、child、similar、tag
- 支持 vis.js 可视化

### 智能分析
- 基于 OpenAI 的语义分析
- 自动标签推荐
- 相似知识推荐
- 知识完整性评估

## 示例响应

### 写入成功
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Python最佳实践",
    "content": "...",
    "tags": ["python", "best-practices"],
    "version": 1,
    "created_at": "2026-03-19T10:00:00Z"
  }
}
```

### 搜索结果
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "suggestions": ["python", "practices"]
  }
}
```

### 统计信息
```json
{
  "success": true,
  "data": {
    "total_items": 100,
    "total_knowledge_bases": 5,
    "total_tags": 50,
    "top_tags": [...],
    "recent_activity": [...],
    "growth_trend": [...]
  }
}
```

## 注意事项

1. **数据安全**：敏感信息在存储前会被脱敏处理
2. **版本控制**：每次修改都会创建新版本，支持回滚
3. **性能优化**：使用索引和缓存提升查询效率
4. **容量限制**：单知识库最大10000条记录
