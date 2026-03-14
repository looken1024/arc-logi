"""
异步任务技能 - 创建和管理异步任务

A skill for creating and managing async tasks.
"""

import sys
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill

try:
    import pymysql
except ImportError:
    pymysql = None


class AsyncTaskSkill(BaseSkill):
    """异步任务技能"""

    def get_name(self) -> str:
        return "async_task"

    def get_description(self) -> str:
        return "创建异步任务，任务会在后台通过 opencode run --thinking 执行。适用于需要较长时间处理的任务，例如代码分析、文件处理、报告生成等。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list", "get", "delete", "get_output"],
                    "description": "操作类型：create-创建异步任务，list-列出异步任务，get-获取单个任务详情，delete-删除任务，get_output-获取任务输出",
                    "default": "create"
                },
                "task_id": {
                    "type": "integer",
                    "description": "异步任务ID（用于get、delete、get_output操作）"
                },
                "task_name": {
                    "type": "string",
                    "description": "任务名称，用于标识任务"
                },
                "task_description": {
                    "type": "string",
                    "description": "任务描述，详细说明需要执行什么工作"
                },
                "scheduled_at": {
                    "type": "string",
                    "description": "计划执行时间，格式为 YYYY-MM-DD HH:MM:SS，默认为立即执行"
                },
                "page": {
                    "type": "integer",
                    "description": "页码（用于list操作分页）",
                    "default": 1,
                    "minimum": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页数量（用于list操作分页）",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": []
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行异步任务操作

        Args:
            **kwargs: 包含操作参数和 _username

        Returns:
            Dict[str, Any]: 操作结果
        """
        action = kwargs.get('action', 'create')
        
        if action == 'create':
            return self._create_async_task(**kwargs)
        elif action == 'list':
            return self._list_async_tasks(**kwargs)
        elif action == 'get':
            return self._get_async_task(**kwargs)
        elif action == 'delete':
            return self._delete_async_task(**kwargs)
        elif action == 'get_output':
            return self._get_async_task_output(**kwargs)
        else:
            return {
                "success": False,
                "error": f"不支持的操作: {action}"
            }

    def _get_username(self, kwargs):
        """从 kwargs 获取用户名"""
        username = kwargs.get('_username')
        if not username:
            raise ValueError("未提供用户名，请先登录")
        return username

    def _get_db_config(self):
        """获取数据库配置"""
        if pymysql is None:
            raise ImportError("pymysql 库未安装，请运行: pip install pymysql")
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'arc_logi_chat'),
            'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
            'cursorclass': pymysql.cursors.DictCursor
        }

    def _get_db_connection(self):
        """获取数据库连接"""
        if pymysql is None:
            raise ImportError("pymysql 库未安装，请运行: pip install pymysql")
        return pymysql.connect(**self._get_db_config())

    def _convert_datetime_fields(self, obj):
        """将 datetime 字段转换为 ISO 格式字符串"""
        if not obj:
            return obj
        for field in ['scheduled_at', 'created_at', 'updated_at', 'started_at', 'completed_at']:
            if field in obj and obj[field] and isinstance(obj[field], datetime):
                obj[field] = obj[field].isoformat()
        return obj

    def _create_opencode_command(self, task_description: str) -> str:
        """构建 opencode run --thinking 命令"""
        escaped_description = task_description.replace('"', '\\"')
        return f'opencode run --thinking "{escaped_description}"'

    def _parse_scheduled_at(self, scheduled_at_str: str) -> Optional[datetime]:
        """解析计划执行时间字符串"""
        if not scheduled_at_str:
            return None
        
        try:
            return datetime.strptime(scheduled_at_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(scheduled_at_str, '%Y-%m-%d %H:%M')
            except ValueError:
                raise ValueError(f"计划执行时间格式无效，请使用 YYYY-MM-DD HH:MM:SS 格式，当前值: {scheduled_at_str}")

    def _create_async_task(self, **kwargs):
        """创建异步任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        task_name = kwargs.get('task_name')
        task_description = kwargs.get('task_description')
        scheduled_at_str = kwargs.get('scheduled_at')
        
        if not task_name:
            return {"success": False, "error": "缺少必要参数: task_name"}
        
        if not task_description:
            return {"success": False, "error": "缺少必要参数: task_description"}
        
        scheduled_at = None
        if scheduled_at_str:
            try:
                scheduled_at = self._parse_scheduled_at(scheduled_at_str)
            except ValueError as e:
                return {"success": False, "error": str(e)}
        
        command = self._create_opencode_command(task_description)
        
        execution_id = str(uuid.uuid4())
        
        if scheduled_at:
            status = 'scheduled'
        else:
            status = 'pending'
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                if scheduled_at:
                    cursor.execute(
                        "INSERT INTO async_tasks (username, task_name, description, command, status, execution_id, scheduled_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (username, task_name, task_description, command, status, execution_id, scheduled_at)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO async_tasks (username, task_name, description, command, status, execution_id) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (username, task_name, task_description, command, status, execution_id)
                    )
                task_id = cursor.lastrowid
                connection.commit()
                
                cursor.execute(
                    "SELECT id, task_name, description, command, status, execution_id, scheduled_at, created_at, updated_at, started_at, completed_at "
                    "FROM async_tasks WHERE id = %s",
                    (task_id,)
                )
                task = cursor.fetchone()
                task = self._convert_datetime_fields(task)
                
                message = "任务已添加到调度队列，将自动执行"
                if scheduled_at:
                    message = f"任务已创建，计划在 {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')} 执行"
                
                return {
                    "success": True,
                    "message": message,
                    "task": task
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"创建异步任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _list_async_tasks(self, **kwargs):
        """列出异步任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 20)
        offset = (page - 1) * page_size
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) as total FROM async_tasks WHERE username = %s",
                    (username,)
                )
                total = cursor.fetchone()['total']
                
                cursor.execute(
                    "SELECT id, task_name, description, command, status, execution_id, scheduled_at, created_at, updated_at, started_at, completed_at "
                    "FROM async_tasks WHERE username = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (username, page_size, offset)
                )
                tasks = cursor.fetchall()
                
                tasks = [self._convert_datetime_fields(task) for task in tasks]
                
                return {
                    "success": True,
                    "tasks": tasks,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size
                    }
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"获取异步任务列表失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _execute_task_in_background(self, task_id, execution_id, command):
        """在后台执行异步任务"""
        import subprocess
        import threading
        import queue
        
        def update_output_in_db(output_text, error_msg=None, status=None):
            """更新数据库中的输出"""
            try:
                connection = self._get_db_connection()
                with connection.cursor() as cursor:
                    if status:
                        cursor.execute(
                            "UPDATE async_tasks SET status = %s, output = %s, error_message = %s, completed_at = CURRENT_TIMESTAMP WHERE execution_id = %s",
                            (status, output_text, error_msg, execution_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE async_tasks SET output = %s WHERE execution_id = %s",
                            (output_text, execution_id)
                        )
                    connection.commit()
            except Exception as e:
                print(f"更新异步任务输出失败: {e}")
            finally:
                if connection:
                    connection.close()
        
        def read_stream(stream, output_queue):
            """从流中读取行并放入队列"""
            try:
                for line in iter(stream.readline, ''):
                    output_queue.put(line)
                stream.close()
            except Exception as e:
                output_queue.put(f"\n流读取错误: {e}")
        
        output_lines = []
        error_message = None
        status = 'running'
        
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE async_tasks SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (task_id,)
                )
                connection.commit()
            connection.close()
            
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_queue = queue.Queue()
            
            stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, output_queue), daemon=True)
            stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, output_queue), daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            while proc.poll() is None or not output_queue.empty():
                try:
                    line = output_queue.get(timeout=0.5)
                    if line:
                        output_lines.append(line)
                        update_output_in_db(''.join(output_lines))
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"处理输出时出错: {e}")
            
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            
            returncode = proc.returncode
            if returncode == 0:
                status = 'completed'
            else:
                status = 'failed'
                error_message = f"Exit code: {returncode}"
            
            update_output_in_db(''.join(output_lines), error_message, status)
            
        except subprocess.TimeoutExpired:
            error_message = "执行超时（超过1小时）"
            status = 'failed'
            update_output_in_db(''.join(output_lines), error_message, status)
        except Exception as e:
            error_message = str(e)
            status = 'failed'
            update_output_in_db(''.join(output_lines), error_message, status)

    def _get_async_task(self, **kwargs):
        """获取单个异步任务详情"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        task_id = kwargs.get('task_id')
        if not task_id:
            return {"success": False, "error": "缺少必要参数: task_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, task_name, description, command, status, execution_id, scheduled_at, created_at, updated_at, started_at, completed_at, output, error_message "
                    "FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                task = cursor.fetchone()
                
                if not task:
                    return {"success": False, "error": "异步任务不存在或无权访问"}
                
                task = self._convert_datetime_fields(task)
                return {"success": True, "task": task}
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"获取异步任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _delete_async_task(self, **kwargs):
        """删除异步任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        task_id = kwargs.get('task_id')
        if not task_id:
            return {"success": False, "error": "缺少必要参数: task_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                if not cursor.fetchone():
                    return {"success": False, "error": "异步任务不存在或无权访问"}
                
                cursor.execute(
                    "DELETE FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                connection.commit()
                
                return {"success": True, "message": "异步任务删除成功"}
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"删除异步任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _get_async_task_output(self, **kwargs):
        """获取异步任务输出"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        task_id = kwargs.get('task_id')
        if not task_id:
            return {"success": False, "error": "缺少必要参数: task_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, output, error_message, status FROM async_tasks WHERE id = %s AND username = %s",
                    (task_id, username)
                )
                task = cursor.fetchone()
                
                if not task:
                    return {"success": False, "error": "异步任务不存在或无权访问"}
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": task['status'],
                    "output": task['output'] or '',
                    "error_message": task['error_message']
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"获取异步任务输出失败: {str(e)}"}
        finally:
            if connection:
                connection.close()


if __name__ == "__main__":
    skill = AsyncTaskSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\nParameters schema:")
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    print(f"\nTest execution (模拟):")
    print("需要提供 _username 参数进行测试")
