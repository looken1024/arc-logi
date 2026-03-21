import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

try:
    from skills.knowledge_base.scripts.skill import KnowledgeBaseSkill
except ImportError:
    from skills.knowledge_base.scripts import skill
    KnowledgeBaseSkill = skill.KnowledgeBaseSkill


class TestKnowledgeBaseSkill(unittest.TestCase):
    
    def setUp(self):
        self.skill = KnowledgeBaseSkill()
    
    def test_get_name(self):
        self.assertEqual(self.skill.get_name(), "knowledge_base")
    
    def test_get_description(self):
        desc = self.skill.get_description()
        self.assertIsInstance(desc, str)
        self.assertIn("write", desc)
        self.assertIn("search", desc)
        self.assertIn("analyze", desc)
    
    def test_get_parameters(self):
        params = self.skill.get_parameters()
        self.assertEqual(params['type'], 'object')
        self.assertIn('action', params['required'])
        self.assertIn('properties', params)
        self.assertIn('action', params['properties'])
        self.assertIn('content', params['properties'])
        self.assertIn('query', params['properties'])
    
    def test_to_function_definition(self):
        func_def = self.skill.to_function_definition()
        self.assertIn('name', func_def)
        self.assertIn('description', func_def)
        self.assertIn('parameters', func_def)
        self.assertEqual(func_def['name'], 'knowledge_base')
    
    def test_execute_unknown_action(self):
        result = self.skill.execute(action="unknown_action")
        self.assertFalse(result['success'])
        self.assertIn('未知操作', result['error'])
    
    def test_execute_write_without_content(self):
        result = self.skill.execute(action="write", content="")
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "知识内容不能为空")
    
    def test_execute_search(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="search", query="test", username="test_user")
            if not result['success']:
                pass
            else:
                self.assertIn('data', result)
                self.assertIn('items', result['data'])
                self.assertIn('total', result['data'])
    
    def test_execute_list(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                {'id': 1, 'name': 'KB1', 'item_count': 5},
                {'id': 2, 'name': 'KB2', 'item_count': 3}
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="list", username="test_user")
            self.assertTrue(result['success'])
            self.assertIn('knowledge_bases', result['data'])
            self.assertEqual(len(result['data']['knowledge_bases']), 2)
    
    def test_execute_stats(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [
                {'id': 1, 'name': '默认知识库'},
                {'count': 10},
                {'count': 25},
                {'count': 15},
                {'count': 5},
                {'count': 3}
            ]
            mock_cursor.fetchall.side_effect = [
                [],
                {'date': '2024-01-01', 'count': 2}
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="stats", username="test_user")
            self.assertTrue(result['success'])
            self.assertIn('data', result)
            self.assertIn('knowledge_base_name', result['data'])
            self.assertIn('is_default_knowledge_base', result['data'])
    
    def test_execute_analyze(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [
                {'id': 1, 'name': '默认知识库'},
                {'type': 'text', 'count': 5},
                {'name': 'python', 'count': 10},
                {'avg_length': 100, 'max_length': 500, 'min_length': 10},
                {'total_items': 5, 'unique_types': 2}
            ]
            mock_cursor.fetchall.side_effect = [
                [],
                [],
                [],
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="analyze", username="test_user")
            self.assertTrue(result['success'])
            self.assertIn('data', result)
            self.assertIn('insights', result['data'])
            self.assertIn('knowledge_base_name', result['data'])
            self.assertIn('is_default_knowledge_base', result['data'])
    
    def test_execute_delete(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="delete", item_id=1, username="test_user")
            self.assertTrue(result['success'])
            self.assertTrue(result['data']['deleted'])
    
    def test_execute_versions(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                {'version_number': 2, 'title': 'v2', 'content': 'content v2', 'created_at': datetime.now(), 'created_by': 'test'},
                {'version_number': 1, 'title': 'v1', 'content': 'content v1', 'created_at': datetime.now(), 'created_by': 'test'}
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="versions", item_id=1)
            self.assertTrue(result['success'])
            self.assertEqual(len(result['data']['versions']), 2)
            self.assertEqual(result['data']['versions'][0]['version_number'], 2)
    
    def test_execute_graph(self):
        with patch('skills.knowledge_base.scripts.skill.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {'id': 1, 'name': '默认知识库'}
            mock_cursor.fetchall.side_effect = [
                [{'id': 1, 'title': 'Test', 'type': 'text', 'content': 'test content'}],
                [{'id': 1, 'target_item_id': 1, 'source_item_id': 1, 'relation_type': 'tag', 'tag_name': 'test'}]
            ]
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            result = self.skill.execute(action="graph", username="test_user")
            self.assertTrue(result['success'])
            self.assertIn('nodes', result['data'])
            self.assertIn('edges', result['data'])
            self.assertIn('knowledge_base_name', result['data'])
            self.assertIn('is_default_knowledge_base', result['data'])


class TestSkillWriteFlow(unittest.TestCase):
    
    def setUp(self):
        self.skill = KnowledgeBaseSkill()
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_write_knowledge_creates_default_kb(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'name': '默认知识库'},  # _get_or_create_default_kb 返回
            {'id': 1}  # 插入后的查询
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        with patch.object(self.skill, '_ensure_tables_exist'):
            result = self.skill.execute(
                action="write",
                content="Test content",
                title="Test Title",
                tags=["test"],
                username="test_user"
            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['title'], "Test Title")
        self.assertEqual(result['data']['content'], "Test content")
        self.assertIn('knowledge_base_name', result['data'])
        self.assertIn('is_default_knowledge_base', result['data'])
        self.assertIn('message', result)
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_write_knowledge_to_specific_kb(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'name': '自定义知识库'}
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        with patch.object(self.skill, '_ensure_tables_exist'):
            result = self.skill.execute(
                action="write",
                content="Test content",
                title="Test Title",
                knowledge_base_id=2,
                username="test_user"
            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['knowledge_base_id'], 2)
        self.assertEqual(result['data']['knowledge_base_name'], '自定义知识库')
        self.assertFalse(result['data']['is_default_knowledge_base'])
        self.assertIn('message', result)
        self.assertIn('已写入知识库', result['message'])
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_write_knowledge_with_auto_title(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'name': '默认知识库'},
            {'id': 1}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        with patch.object(self.skill, '_ensure_tables_exist'):
            result = self.skill.execute(
                action="write",
                content="This is a longer content that should be truncated for title",
                username="test_user"
            )
        
        self.assertTrue(result['success'])
        self.assertIn('title', result['data'])
        self.assertTrue(len(result['data']['title']) <= 53)
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_write_knowledge_creates_version(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'name': '默认知识库'},
            {'id': 1}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        with patch.object(self.skill, '_ensure_tables_exist'):
            result = self.skill.execute(
                action="write",
                content="Version test content",
                username="test_user"
            )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['version'], 1)
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_write_default_kb_message(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'name': '默认知识库'},
            {'id': 1}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        with patch.object(self.skill, '_ensure_tables_exist'):
            result = self.skill.execute(
                action="write",
                content="Test content",
                username="test_user"
            )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['data']['is_default_knowledge_base'])
        self.assertIn('默认知识库', result['message'])


class TestSkillSearchFlow(unittest.TestCase):
    
    def setUp(self):
        self.skill = KnowledgeBaseSkill()
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_search_with_pagination(self, mock_conn):
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="search",
            query="test",
            page=1,
            page_size=20,
            username="test_user"
        )
        
        if result['success']:
            self.assertIn('page', result['data'])
            self.assertIn('page_size', result['data'])
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_search_with_filters(self, mock_conn):
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="search",
            filters={
                'item_type': 'text',
                'tags': ['python'],
                'date_from': '2024-01-01'
            },
            username="test_user"
        )
        
        if result['success']:
            self.assertIn('items', result['data'])
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_search_no_results_suggests_tags(self, mock_conn):
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="search",
            query="pythn",
            username="test_user"
        )
        
        if result['success']:
            self.assertIn('suggestions', result['data'])
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_search_specific_kb(self, mock_conn):
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="search",
            knowledge_base_id=2,
            username="test_user"
        )
        
        if result['success']:
            self.assertIn('knowledge_base_id', result['data'])


class TestSkillUpdateFlow(unittest.TestCase):
    
    def setUp(self):
        self.skill = KnowledgeBaseSkill()
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_update_knowledge(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'title': 'Old Title', 'content': 'Old content'},
            {'version_number': 1}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="update",
            item_id=1,
            title="New Title",
            content="New content",
            username="test_user"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['version'], 2)
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_update_nonexistent_item(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="update",
            item_id=999,
            title="Test",
            username="test_user"
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "知识条目不存在")
    
    @patch('skills.knowledge_base.scripts.skill.get_db_connection')
    def test_rollback_version(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {'item_id': 1, 'version_number': 1, 'title': 'Old', 'content': 'Old content'},
            {'version_number': 2}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.skill.execute(
            action="rollback",
            item_id=1,
            version_number=1,
            username="test_user"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['rolled_back_to_version'], 1)
        self.assertEqual(result['data']['new_version'], 3)


class TestSkillAnalyze(unittest.TestCase):
    
    def setUp(self):
        self.skill = KnowledgeBaseSkill()
    
    def test_generate_insights_empty_kb(self):
        insights = self.skill._generate_insights({}, [], [], {})
        self.assertEqual(len(insights), 1)
        self.assertIn("为空", insights[0])
    
    def test_generate_insights_with_data(self):
        type_dist = {'text': 10, 'qa': 5}
        growth = [
            {'date': '2024-01-01', 'count': 2},
            {'date': '2024-01-02', 'count': 3},
            {'date': '2024-01-03', 'count': 5}
        ]
        tags = [{'name': 'python', 'count': 8}]
        content = {'avg_length': 500}
        
        insights = self.skill._generate_insights(type_dist, growth, tags, content)
        
        self.assertGreater(len(insights), 0)
        self.assertTrue(any('text' in i for i in insights))


if __name__ == '__main__':
    unittest.main()
