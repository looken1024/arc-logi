import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

try:
    from skills.base import BaseSkill
    from app import get_db_connection
except ImportError:
    from skills.base import BaseSkill
    import pymysql
    from contextlib import contextmanager
    
    @contextmanager
    def get_db_connection():
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'arc_logi_chat'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            yield connection
        finally:
            connection.close()


class KnowledgeBaseSkill(BaseSkill):
    
    def get_name(self) -> str:
        return "knowledge_base"
    
    def get_description(self) -> str:
        return (
            "知识库管理技能，支持知识的创建、查询、分析和管理。"
            "可以执行以下操作：write（写入知识）、search（搜索知识）、"
            "analyze（分析知识）、list（列出知识库）、stats（统计信息）、"
            "delete（删除知识）、update（更新知识）"
        )
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型：write（写入）、search（搜索）、analyze（分析）、list（列出）、stats（统计）、delete（删除）、update（更新）",
                    "enum": ["write", "search", "analyze", "list", "stats", "delete", "update", "graph", "versions", "rollback"]
                },
                "content": {
                    "type": "string",
                    "description": "知识内容（write/update时必填）"
                },
                "title": {
                    "type": "string",
                    "description": "知识标题"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签列表，如 ['python', '最佳实践']"
                },
                "category": {
                    "type": "string",
                    "description": "分类名称"
                },
                "item_type": {
                    "type": "string",
                    "description": "知识类型：text（文本）、qa（问答）、concept（概念）、procedure（流程）",
                    "enum": ["text", "qa", "concept", "procedure"],
                    "default": "text"
                },
                "knowledge_base_id": {
                    "type": "integer",
                    "description": "知识库ID，不指定则使用主知识库"
                },
                "item_id": {
                    "type": "integer",
                    "description": "知识条目ID（delete/update/versions/rollback时使用）"
                },
                "query": {
                    "type": "string",
                    "description": "搜索关键词（search时使用）"
                },
                "filters": {
                    "type": "object",
                    "description": "筛选条件：{tags: [], categories: [], date_from: '', date_to: '', item_type: ''}",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "categories": {"type": "array", "items": {"type": "string"}},
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                        "item_type": {"type": "string"}
                    }
                },
                "page": {
                    "type": "integer",
                    "description": "页码（从1开始）",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页数量",
                    "default": 20
                },
                "username": {
                    "type": "string",
                    "description": "用户名（用于权限验证）"
                }
            },
            "required": ["action"]
        }
    
    def to_function_definition(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_base",
            "description": self.get_description(),
            "parameters": self.get_parameters()
        }
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        try:
            handlers = {
                "write": self._write_knowledge,
                "search": self._search_knowledge,
                "analyze": self._analyze_knowledge,
                "list": self._list_knowledge_bases,
                "stats": self._get_stats,
                "delete": self._delete_knowledge,
                "update": self._update_knowledge,
                "graph": self._get_knowledge_graph,
                "versions": self._get_versions,
                "rollback": self._rollback_version
            }
            
            handler = handlers.get(action)
            if not handler:
                return {"success": False, "error": f"未知操作: {action}"}
            
            return handler(**kwargs)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_or_create_default_knowledge_base(self, username: str) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE username = %s AND name = '默认知识库' LIMIT 1",
                (username,)
            )
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            cursor.execute(
                "INSERT INTO knowledge_base (name, description, username, created_at, updated_at) "
                "VALUES (%s, %s, %s, NOW(), NOW())",
                ('默认知识库', '用户默认知识库', username)
            )
            conn.commit()
            return cursor.lastrowid
    
    def _ensure_tables_exist(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            tables_to_create = [
                """
                CREATE TABLE IF NOT EXISTS knowledge_tag (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    color VARCHAR(20) DEFAULT '#1890ff',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS knowledge_category (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    parent_id INT DEFAULT NULL,
                    knowledge_base_id INT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS knowledge_version (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT NOT NULL,
                    version_number INT NOT NULL,
                    title VARCHAR(200),
                    content TEXT,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(50),
                    FOREIGN KEY (item_id) REFERENCES knowledge_item(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS knowledge_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    action VARCHAR(20) NOT NULL,
                    old_data JSON,
                    new_data JSON,
                    username VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]
            
            for sql in tables_to_create:
                cursor.execute(sql)
            conn.commit()
    
    def _write_knowledge(self, content: str, title: Optional[str] = None,
                         tags: Optional[List[str]] = None, category: Optional[str] = None,
                         item_type: str = "text", knowledge_base_id: Optional[int] = None,
                         username: str = "default", **kwargs) -> Dict[str, Any]:
        
        self._ensure_tables_exist()
        
        if not content:
            return {"success": False, "error": "知识内容不能为空"}
        
        if not title:
            title = content[:50] + "..." if len(content) > 50 else content
        
        if not knowledge_base_id:
            knowledge_base_id = self._get_or_create_default_knowledge_base(username)
        
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO knowledge_item (knowledge_base_id, title, content, type, created_at, updated_at, content_hash) "
                "VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)",
                (knowledge_base_id, title, content, item_type, content_hash)
            )
            item_id = cursor.lastrowid
            
            if tags:
                for tag_name in tags:
                    cursor.execute(
                        "INSERT IGNORE INTO knowledge_tag (name) VALUES (%s)",
                        (tag_name,)
                    )
                    cursor.execute("SELECT id FROM knowledge_tag WHERE name = %s", (tag_name,))
                    tag = cursor.fetchone()
                    if tag:
                        cursor.execute(
                            "INSERT INTO knowledge_relation (knowledge_base_id, source_item_id, target_item_id, relation_type) "
                            "VALUES (%s, %s, %s, 'tag')",
                            (knowledge_base_id, item_id, tag['id'])
                        )
            
            if category:
                cursor.execute(
                    "INSERT INTO knowledge_category (name, knowledge_base_id) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE name=name",
                    (category, knowledge_base_id)
                )
                cursor.execute("SELECT id FROM knowledge_category WHERE name = %s AND knowledge_base_id = %s",
                              (category, knowledge_base_id))
                cat = cursor.fetchone()
                if cat:
                    cursor.execute(
                        "UPDATE knowledge_item SET category_id = %s WHERE id = %s",
                        (cat['id'], item_id)
                    )
            
            cursor.execute(
                "INSERT INTO knowledge_version (item_id, version_number, title, content, created_by) "
                "VALUES (%s, 1, %s, %s, %s)",
                (item_id, title, content, username)
            )
            
            cursor.execute(
                "INSERT INTO knowledge_history (item_id, action, new_data, username) "
                "VALUES (%s, 'create', %s, %s)",
                (item_id, json.dumps({"title": title, "type": item_type}), username)
            )
            
            cursor.execute(
                "UPDATE knowledge_base SET updated_at = NOW() WHERE id = %s",
                (knowledge_base_id,)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "data": {
                    "id": item_id,
                    "title": title,
                    "content": content,
                    "tags": tags or [],
                    "category": category,
                    "type": item_type,
                    "version": 1,
                    "knowledge_base_id": knowledge_base_id,
                    "created_at": datetime.now().isoformat()
                }
            }
    
    def _search_knowledge(self, query: Optional[str] = None,
                          knowledge_base_id: Optional[int] = None,
                          filters: Optional[Dict] = None,
                          page: int = 1, page_size: int = 20,
                          username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if not knowledge_base_id:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE username = %s AND name = '默认知识库' LIMIT 1",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    knowledge_base_id = result['id']
            
            where_clauses = []
            params = []
            
            if knowledge_base_id:
                where_clauses.append("ki.knowledge_base_id = %s")
                params.append(knowledge_base_id)
            
            if query:
                where_clauses.append("(ki.title LIKE %s OR ki.content LIKE %s)")
                search_term = f"%{query}%"
                params.extend([search_term, search_term])
            
            if filters:
                if filters.get('item_type'):
                    where_clauses.append("ki.type = %s")
                    params.append(filters['item_type'])
                
                if filters.get('tags'):
                    tag_ids = []
                    for tag in filters['tags']:
                        cursor.execute("SELECT id FROM knowledge_tag WHERE name = %s", (tag,))
                        tag_result = cursor.fetchone()
                        if tag_result:
                            tag_ids.append(tag_result['id'])
                    if tag_ids:
                        placeholders = ','.join(['%s'] * len(tag_ids))
                        where_clauses.append(f"ki.id IN (SELECT source_item_id FROM knowledge_relation WHERE relation_type = 'tag' AND target_item_id IN ({placeholders}))")
                        params.extend(tag_ids)
                
                if filters.get('date_from'):
                    where_clauses.append("ki.created_at >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    where_clauses.append("ki.created_at <= %s")
                    params.append(filters['date_to'])
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            cursor.execute(
                f"SELECT COUNT(*) as total FROM knowledge_item ki WHERE {where_sql}",
                params
            )
            total = cursor.fetchone()['total']
            
            offset = (page - 1) * page_size
            cursor.execute(
                f"""
                SELECT ki.*, GROUP_CONCAT(DISTINCT kt.name) as tag_names
                FROM knowledge_item ki
                LEFT JOIN knowledge_relation kr ON ki.id = kr.source_item_id AND kr.relation_type = 'tag'
                LEFT JOIN knowledge_tag kt ON kr.target_item_id = kt.id
                WHERE {where_sql}
                GROUP BY ki.id
                ORDER BY ki.updated_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset]
            )
            items = cursor.fetchall()
            
            for item in items:
                if item.get('tag_names'):
                    item['tags'] = item['tag_names'].split(',')
                else:
                    item['tags'] = []
                item.pop('tag_names', None)
            
            suggestions = []
            if query and total == 0:
                cursor.execute(
                    "SELECT DISTINCT name FROM knowledge_tag WHERE name LIKE %s LIMIT 5",
                    (f"%{query}%",)
                )
                suggestions = [r['name'] for r in cursor.fetchall()]
            
            return {
                "success": True,
                "data": {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size,
                    "suggestions": suggestions
                }
            }
    
    def _analyze_knowledge(self, knowledge_base_id: Optional[int] = None,
                           username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if not knowledge_base_id:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE username = %s AND name = '默认知识库' LIMIT 1",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    knowledge_base_id = result['id']
            
            cursor.execute(
                """
                SELECT type, COUNT(*) as count 
                FROM knowledge_item 
                WHERE knowledge_base_id = %s 
                GROUP BY type
                """,
                (knowledge_base_id,)
            )
            type_distribution = {r['type']: r['count'] for r in cursor.fetchall()}
            
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM knowledge_item
                WHERE knowledge_base_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
                """,
                (knowledge_base_id,)
            )
            growth_trend = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT kt.name, COUNT(*) as count
                FROM knowledge_relation kr
                JOIN knowledge_tag kt ON kr.target_item_id = kt.id
                WHERE kr.relation_type = 'tag'
                GROUP BY kt.id, kt.name
                ORDER BY count DESC
                LIMIT 10
                """
            )
            top_tags = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT 
                    AVG(LENGTH(content)) as avg_length,
                    MAX(LENGTH(content)) as max_length,
                    MIN(LENGTH(content)) as min_length
                FROM knowledge_item
                WHERE knowledge_base_id = %s
                """,
                (knowledge_base_id,)
            )
            content_stats = cursor.fetchone()
            
            cursor.execute(
                """
                SELECT COUNT(*) as total_items,
                       COUNT(DISTINCT type) as unique_types
                FROM knowledge_item
                WHERE knowledge_base_id = %s
                """,
                (knowledge_base_id,)
            )
            overview = cursor.fetchone()
            
            return {
                "success": True,
                "data": {
                    "overview": overview,
                    "type_distribution": type_distribution,
                    "growth_trend": growth_trend,
                    "top_tags": top_tags,
                    "content_stats": content_stats,
                    "insights": self._generate_insights(type_distribution, growth_trend, top_tags, content_stats)
                }
            }
    
    def _generate_insights(self, type_dist: Dict, growth: List, tags: List, content: Dict) -> List[str]:
        insights = []
        
        total = sum(type_dist.values()) if type_dist else 0
        if total == 0:
            return ["当前知识库为空，建议添加一些知识条目"]
        
        if type_dist:
            most_common = max(type_dist.items(), key=lambda x: x[1])
            insights.append(f"知识类型以「{most_common[0]}」为主，共{most_common[1]}条")
        
        if growth:
            recent = sum(g['count'] for g in growth[-7:] if g)
            earlier = sum(g['count'] for g in growth[-14:-7] if g)
            if recent > earlier:
                insights.append(f"近7天新增{recent}条知识，较前期增长{((recent-earlier)/max(earlier,1)*100):.1f}%")
        
        if tags:
            insights.append(f"最热门标签：「{tags[0]['name']}」（{tags[0]['count']}次使用）")
        
        if content and content.get('avg_length'):
            insights.append(f"平均知识条目长度：{content['avg_length']:.0f}字符")
        
        return insights
    
    def _list_knowledge_bases(self, username: str = "default", **kwargs) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT kb.*, COUNT(ki.id) as item_count
                FROM knowledge_base kb
                LEFT JOIN knowledge_item ki ON kb.id = ki.knowledge_base_id
                WHERE kb.username = %s
                GROUP BY kb.id
                ORDER BY kb.updated_at DESC
                """,
                (username,)
            )
            bases = cursor.fetchall()
            
            return {
                "success": True,
                "data": {
                    "knowledge_bases": bases,
                    "total": len(bases)
                }
            }
    
    def _get_stats(self, knowledge_base_id: Optional[int] = None,
                   username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if not knowledge_base_id:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE username = %s AND name = '默认知识库' LIMIT 1",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    knowledge_base_id = result['id']
            
            stats = {}
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM knowledge_base WHERE username = %s",
                (username,)
            )
            stats['total_knowledge_bases'] = cursor.fetchone()['count']
            
            if knowledge_base_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM knowledge_item WHERE knowledge_base_id = %s",
                    (knowledge_base_id,)
                )
                stats['total_items'] = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT COUNT(*) as count FROM knowledge_version WHERE item_id IN "
                    "(SELECT id FROM knowledge_item WHERE knowledge_base_id = %s)",
                    (knowledge_base_id,)
                )
                stats['total_versions'] = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT COUNT(DISTINCT name) as count FROM knowledge_tag kt "
                    "JOIN knowledge_relation kr ON kt.id = kr.target_item_id "
                    "WHERE kr.knowledge_base_id = %s AND kr.relation_type = 'tag'",
                    (knowledge_base_id,)
                )
                stats['total_tags'] = cursor.fetchone()['count']
                
                cursor.execute(
                    "SELECT type, COUNT(*) as count FROM knowledge_item "
                    "WHERE knowledge_base_id = %s GROUP BY type",
                    (knowledge_base_id,)
                )
                stats['items_by_type'] = {r['type']: r['count'] for r in cursor.fetchall()}
                
                cursor.execute(
                    "SELECT DATE(created_at) as date, COUNT(*) as count "
                    "FROM knowledge_item WHERE knowledge_base_id = %s "
                    "GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 10",
                    (knowledge_base_id,)
                )
                stats['recent_activity'] = cursor.fetchall()
            
            return {"success": True, "data": stats}
    
    def _delete_knowledge(self, item_id: int, username: str = "default", **kwargs) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO knowledge_history (item_id, action, old_data, username) "
                "SELECT id, 'delete', JSON_OBJECT('title', title, 'content', content), %s "
                "FROM knowledge_item WHERE id = %s",
                (username, item_id)
            )
            
            cursor.execute(
                "DELETE FROM knowledge_item WHERE id = %s",
                (item_id,)
            )
            conn.commit()
            
            return {"success": True, "data": {"id": item_id, "deleted": True}}
    
    def _update_knowledge(self, item_id: int, content: Optional[str] = None,
                          title: Optional[str] = None, tags: Optional[List[str]] = None,
                          username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM knowledge_item WHERE id = %s",
                (item_id,)
            )
            old_item = cursor.fetchone()
            
            if not old_item:
                return {"success": False, "error": "知识条目不存在"}
            
            updates = []
            params = []
            
            if title:
                updates.append("title = %s")
                params.append(title)
            if content:
                updates.append("content = %s")
                params.append(content)
                content_hash = hashlib.md5(content.encode()).hexdigest()
                updates.append("content_hash = %s")
                params.append(content_hash)
            
            updates.append("updated_at = NOW()")
            
            if updates:
                cursor.execute(
                    f"UPDATE knowledge_item SET {', '.join(updates)} WHERE id = %s",
                    params + [item_id]
                )
            
            cursor.execute("SELECT version_number FROM knowledge_version WHERE item_id = %s ORDER BY version_number DESC LIMIT 1", (item_id,))
            result = cursor.fetchone()
            new_version = (result['version_number'] if result else 0) + 1
            
            cursor.execute(
                "INSERT INTO knowledge_version (item_id, version_number, title, content, created_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (item_id, new_version, title or old_item['title'], content or old_item['content'], username)
            )
            
            cursor.execute(
                "INSERT INTO knowledge_history (item_id, action, old_data, new_data, username) "
                "VALUES (%s, 'update', %s, %s, %s)",
                (item_id, json.dumps({"title": old_item['title'], "content": old_item['content']}),
                 json.dumps({"title": title, "content": content}), username)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "data": {
                    "id": item_id,
                    "version": new_version,
                    "updated_at": datetime.now().isoformat()
                }
            }
    
    def _get_knowledge_graph(self, knowledge_base_id: Optional[int] = None,
                             username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if not knowledge_base_id:
                cursor.execute(
                    "SELECT id FROM knowledge_base WHERE username = %s AND name = '默认知识库' LIMIT 1",
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    knowledge_base_id = result['id']
            
            cursor.execute(
                """
                SELECT id, title, type, content 
                FROM knowledge_item 
                WHERE knowledge_base_id = %s
                """,
                (knowledge_base_id,)
            )
            items = cursor.fetchall()
            
            cursor.execute(
                """
                SELECT kr.*, kt.name as tag_name
                FROM knowledge_relation kr
                LEFT JOIN knowledge_tag kt ON kr.target_item_id = kt.id AND kr.relation_type = 'tag'
                WHERE kr.knowledge_base_id = %s
                """,
                (knowledge_base_id,)
            )
            relations = cursor.fetchall()
            
            nodes = []
            edges = []
            
            for item in items:
                nodes.append({
                    "id": f"item_{item['id']}",
                    "label": item['title'][:30],
                    "type": item['type'],
                    "title": item['title']
                })
            
            for rel in relations:
                if rel['relation_type'] == 'tag':
                    nodes.append({
                        "id": f"tag_{rel['target_item_id']}",
                        "label": rel['tag_name'],
                        "type": "tag"
                    })
                    edges.append({
                        "from": f"item_{rel['source_item_id']}",
                        "to": f"tag_{rel['target_item_id']}",
                        "type": "has_tag"
                    })
                elif rel['source_item_id']:
                    edges.append({
                        "from": f"item_{rel['source_item_id']}",
                        "to": f"item_{rel['target_item_id']}",
                        "type": rel['relation_type']
                    })
            
            return {
                "success": True,
                "data": {
                    "nodes": nodes,
                    "edges": edges
                }
            }
    
    def _get_versions(self, item_id: int, **kwargs) -> Dict[str, Any]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT version_number, title, content, created_at, created_by
                FROM knowledge_version
                WHERE item_id = %s
                ORDER BY version_number DESC
                """,
                (item_id,)
            )
            versions = cursor.fetchall()
            
            return {
                "success": True,
                "data": {
                    "item_id": item_id,
                    "versions": versions,
                    "total": len(versions)
                }
            }
    
    def _rollback_version(self, item_id: int, version_number: int,
                          username: str = "default", **kwargs) -> Dict[str, Any]:
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM knowledge_version WHERE item_id = %s AND version_number = %s",
                (item_id, version_number)
            )
            target_version = cursor.fetchone()
            
            if not target_version:
                return {"success": False, "error": "版本不存在"}
            
            cursor.execute(
                "UPDATE knowledge_item SET title = %s, content = %s, updated_at = NOW() WHERE id = %s",
                (target_version['title'], target_version['content'], item_id)
            )
            
            cursor.execute(
                "SELECT version_number FROM knowledge_version WHERE item_id = %s ORDER BY version_number DESC LIMIT 1",
                (item_id,)
            )
            current_version = cursor.fetchone()['version_number']
            
            cursor.execute(
                "INSERT INTO knowledge_version (item_id, version_number, title, content, created_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (item_id, current_version + 1, target_version['title'], target_version['content'], username)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "data": {
                    "item_id": item_id,
                    "rolled_back_to_version": version_number,
                    "new_version": current_version + 1
                }
            }


_knowledge_base_skill = KnowledgeBaseSkill()

def get_skill():
    return _knowledge_base_skill

if __name__ == "__main__":
    skill = KnowledgeBaseSkill()
    print("=== Knowledge Base Skill Test ===")
    print(f"Name: {skill.get_name()}")
    print(f"Description: {skill.get_description()}")
    print(f"Parameters: {json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False)}")
    
    result = skill.execute(action="stats", username="test")
    print(f"\nStats Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
