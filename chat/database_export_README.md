# 数据库导出文件说明

## 导出信息

- **数据库名称**: arc_logi_chat
- **导出时间**: 2026-04-23 08:37:00
- **MySQL 版本**: 8.0.45
- **主机**: localhost

## 数据库字符集信息

- **字符集**: utf8mb4
- **排序规则**: utf8mb4_unicode_ci

## 导出的表列表 (共33个表)

1. agent_skills
2. agents
3. async_tasks
4. conversations
5. knowledge_base
6. knowledge_category
7. knowledge_history
8. knowledge_item
9. knowledge_item_tag
10. knowledge_relation
11. knowledge_tag
12. knowledge_version
13. open_source_projects
14. papers
15. popular_searches
16. preset_groups
17. preset_items
18. prompts
19. research
20. research_reviews
21. schedule_executions
22. schedules
23. short_urls
24. user_preferences
25. user_profile
26. user_skills
27. users
28. workflow_edges
29. workflow_executions
30. workflow_node_executions
31. workflow_nodes
32. workflow_search_history
33. workflows

## 输出文件

### 1. database_structure.sql
- **大小**: ~75KB
- **内容**: 所有表的 CREATE TABLE 语句
- **包含**: 表结构、索引、约束、外键关系

### 2. database_data.sql
- **大小**: ~3.7MB
- **内容**: 所有表的 INSERT 语句
- **包含**: 所有表中的数据（除 knowledge_version 表）

### 3. database_complete.sql
- **大小**: ~3.8MB
- **内容**: 完整的结构和数据
- **包含**: CREATE TABLE + INSERT 语句，带 DROP TABLE 语句

## 连接信息

```
主机: localhost
端口: 3306
用户名: root
数据库: arc_logi_chat
字符集: utf8mb4
```

## 使用方法

### 导入完整数据库
```bash
mysql -u root arc_logi_chat < database_complete.sql
```

### 仅导入结构
```bash
mysql -u root arc_logi_chat < database_structure.sql
```

### 仅导入数据（需要先创建结构）
```bash
mysql -u root arc_logi_chat < database_data.sql
```

### 导出新数据
```bash
mysqldump -h localhost -u root arc_logi_chat > backup.sql
```

## 注意事项

1. 导入前请确保数据库存在: `CREATE DATABASE IF NOT EXISTS arc_logi_chat;`
2. 如果使用空密码，命令中可省略 `-p` 参数
3. `knowledge_version` 表在数据导出时被排除（可能包含大量历史版本数据）