# 数据库导出文件说明

## 导出信息

- **数据库名称**: arc_logi_chat
- **导出时间**: 2026-04-23
- **导出方式**: mysqldump

## 文件说明

### full_dump.sql
完整的数据库导出文件，包含：
- 所有表的 CREATE TABLE 语句（30个表）
- 所有表的数据（INSERT 语句）
- 表结构包含索引和外键定义

## 包含的表 (30个)

1. agent_skills - Agent技能配置
2. agents - Agent信息
3. async_tasks - 异步任务
4. conversations - 对话记录
5. knowledge_base - 知识库
6. knowledge_category - 知识分类
7. knowledge_history - 知识历史
8. knowledge_item - 知识条目
9. knowledge_item_tag - 知识标签关联
10. knowledge_relation - 知识关系
11. knowledge_tag - 知识标签
12. knowledge_version - 知识版本
13. open_source_projects - 开源项目
14. papers - 论文
15. popular_searches - 热门搜索
16. preset_groups - 预设组
17. preset_items - 预设项
18. prompts - 提示词
19. research - 研究
20. research_reviews - 研究评审
21. schedule_executions - 定时执行
22. schedules - 定时任务
23. short_urls - 短链接
24. user_preferences - 用户偏好
25. user_profile - 用户资料
26. user_skills - 用户技能
27. users - 用户
28. workflow_edges - 工作流边
29. workflow_executions - 工作流执行
30. workflow_node_executions - 工作流节点执行
31. workflow_nodes - 工作流节点
32. workflow_search_history - 工作流搜索历史
33. workflows - 工作流

## 导入方法

```bash
# 导入到MySQL
mysql -u root -p arc_logi_chat < full_dump.sql

# 或使用source命令
mysql -u root -p
USE arc_logi_chat;
SOURCE full_dump.sql;
```

## 数据库连接配置

- Host: localhost
- Port: 3306
- User: root
- Password: (空)
- Database: arc_logi_chat
- Charset: utf8mb4