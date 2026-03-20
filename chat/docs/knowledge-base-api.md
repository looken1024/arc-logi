# 知识库 API 接口文档

## 概述

本文档描述知识库管理系统的 RESTful API 接口。

**Base URL**: `/api/knowledge-bases`

**认证**: 需要登录会话，使用 `credentials: 'same-origin'` 携带 Cookie

---

## 知识库管理

### 获取知识库列表

```
GET /api/knowledge-bases
```

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "技术文档",
    "description": "技术相关知识",
    "username": "user1",
    "item_count": 25,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
]
```

---

### 创建知识库

```
POST /api/knowledge-bases
```

**请求体**:
```json
{
  "name": "新知识库",
  "description": "知识库描述"
}
```

**响应**: `201 Created`
```json
{
  "id": 2,
  "name": "新知识库",
  "description": "知识库描述",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### 获取知识库详情

```
GET /api/knowledge-bases/{id}
```

**响应**: `200 OK`
```json
{
  "id": 1,
  "name": "技术文档",
  "description": "技术相关知识",
  "item_count": 25,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

---

### 更新知识库

```
PUT /api/knowledge-bases/{id}
```

**请求体**:
```json
{
  "name": "更新后的名称",
  "description": "更新后的描述"
}
```

---

### 删除知识库

```
DELETE /api/knowledge-bases/{id}
```

**响应**: `204 No Content`

---

## 知识条目管理

### 获取知识条目列表

```
GET /api/knowledge-bases/{kb_id}/items
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 (默认: 1) |
| page_size | int | 每页数量 (默认: 20) |
| type | string | 过滤类型: text/qa/concept/procedure |

**响应**:
```json
[
  {
    "id": 1,
    "title": "Python 基础",
    "content": "Python 是一门...",
    "type": "text",
    "tags": ["python", "编程"],
    "view_count": 100,
    "like_count": 5,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
]
```

---

### 创建知识条目

```
POST /api/knowledge-bases/{kb_id}/items
```

**请求体**:
```json
{
  "title": "JavaScript 基础",
  "content": "JavaScript 是一门...",
  "type": "text",
  "tags": ["javascript", "编程"]
}
```

**类型选项**:
- `text`: 文本
- `qa`: 问答
- `concept`: 概念
- `procedure`: 流程

---

### 获取知识条目详情

```
GET /api/knowledge-items/{id}
```

---

### 更新知识条目

```
PUT /api/knowledge-items/{id}
```

**请求体**:
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "tags": ["新标签"]
}
```

---

### 删除知识条目

```
DELETE /api/knowledge-items/{id}
```

---

## 搜索功能

### 搜索知识

```
GET /api/knowledge-bases/{kb_id}/search
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词 |
| type | string | 知识类型过滤 |
| tags | string | 标签过滤 (逗号分隔) |
| date_from | string | 开始日期 (YYYY-MM-DD) |
| date_to | string | 结束日期 (YYYY-MM-DD) |
| page | int | 页码 |
| page_size | int | 每页数量 |

**响应**:
```json
{
  "items": [...],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "suggestions": ["python", "practices"]
}
```

---

## 知识关系

### 获取知识关系

```
GET /api/knowledge-bases/{kb_id}/relations
```

**响应**:
```json
[
  {
    "id": 1,
    "source_item_id": 1,
    "source_title": "Python 基础",
    "target_item_id": 2,
    "target_title": "Python 进阶",
    "relation_type": "related"
  }
]
```

---

### 创建知识关系

```
POST /api/knowledge-bases/{kb_id}/relations
```

**请求体**:
```json
{
  "source_item_id": 1,
  "target_item_id": 2,
  "relation_type": "related"
}
```

**关系类型**:
- `related`: 相关
- `parent`: 父级
- `child`: 子级
- `similar`: 相似
- `tag`: 标签
- `reference`: 引用

---

### 删除知识关系

```
DELETE /api/knowledge-relations/{id}
```

---

## 知识图谱

### 获取图谱数据

```
GET /api/knowledge-bases/{kb_id}/graph
```

**响应**:
```json
{
  "nodes": [
    {"id": "item_1", "label": "Python基础", "type": "text"},
    {"id": "tag_1", "label": "python", "type": "tag"}
  ],
  "edges": [
    {"from": "item_1", "to": "tag_1", "type": "has_tag"}
  ]
}
```

---

### 导出图谱

```
POST /api/knowledge-bases/{kb_id}/graph/export
```

**请求体**:
```json
{
  "format": "png"
}
```

**格式选项**: `png`, `svg`

---

## 版本管理

### 获取版本历史

```
GET /api/knowledge-items/{id}/versions
```

**响应**:
```json
{
  "item_id": 1,
  "versions": [
    {
      "version_number": 2,
      "title": "更新后的标题",
      "content": "更新后的内容",
      "created_at": "2024-01-15T14:30:00Z",
      "created_by": "user1"
    },
    {
      "version_number": 1,
      "title": "原始标题",
      "content": "原始内容",
      "created_at": "2024-01-01T10:00:00Z",
      "created_by": "user1"
    }
  ],
  "total": 2
}
```

---

### 回滚版本

```
POST /api/knowledge-items/{id}/rollback
```

**请求体**:
```json
{
  "version_number": 1
}
```

---

## 统计分析

### 获取统计信息

```
GET /api/knowledge-bases/{kb_id}/stats
```

**响应**:
```json
{
  "total_items": 100,
  "total_knowledge_bases": 5,
  "total_tags": 50,
  "items_by_type": {
    "text": 60,
    "qa": 25,
    "concept": 10,
    "procedure": 5
  },
  "recent_activity": [
    {"date": "2024-01-15", "count": 5},
    {"date": "2024-01-14", "count": 3}
  ],
  "growth_trend": [
    {"date": "2024-01-01", "count": 2},
    {"date": "2024-01-02", "count": 5}
  ]
}
```

---

## 错误响应

所有错误响应遵循以下格式:

```json
{
  "error": "错误信息"
}
```

**HTTP 状态码**:
- `200`: 成功
- `201`: 创建成功
- `204`: 删除成功
- `400`: 请求参数错误
- `401`: 未登录
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器错误
