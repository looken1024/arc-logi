"""
定时任务技能 - 创建和管理定时任务

A skill for creating and managing scheduled tasks.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill

try:
    import pymysql
    from croniter import croniter
except ImportError:
    pymysql = None
    croniter = None


class ScheduleSkill(BaseSkill):
    """定时任务技能"""

    def get_name(self) -> str:
        return "create_schedule"

    def get_description(self) -> str:
        return "创建和管理定时任务，包括创建、查看、更新、删除、执行定时任务以及查看执行记录。定时任务按照指定的 Cron 表达式定期执行 shell 命令或脚本。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list", "get", "update", "delete", "execute", "get_executions"],
                    "description": "操作类型：create-创建定时任务，list-列出定时任务，get-获取单个任务详情，update-更新任务，delete-删除任务，execute-立即执行任务，get_executions-获取任务执行记录",
                    "default": "create"
                },
                "schedule_id": {
                    "type": "integer",
                    "description": "定时任务ID（用于get、update、delete、execute、get_executions操作）"
                },
                "name": {
                    "type": "string",
                    "description": "定时任务名称，用于标识任务"
                },
                "cron": {
                    "type": "string",
                    "description": "Cron表达式，定义任务执行时间。例如：'0 * * * *' 表示每小时执行一次"
                },
                "command": {
                    "type": "string",
                    "description": "要执行的命令，可以是 shell 命令或脚本"
                },
                "description": {
                    "type": "string",
                    "description": "任务描述，可选",
                    "default": ""
                },
                "preset": {
                    "type": "string",
                    "description": "预设类型，可选",
                    "default": ""
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "paused"],
                    "description": "任务状态，active 为激活，paused 为暂停",
                    "default": "active"
                },
                "filters": {
                    "type": "object",
                    "description": "过滤条件（用于list操作），例如按状态过滤",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["active", "paused", "all"],
                            "default": "all"
                        }
                    }
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
        执行定时任务操作

        Args:
            **kwargs: 包含操作参数和 _username

        Returns:
            Dict[str, Any]: 操作结果
        """
        action = kwargs.get('action', 'create')
        
        if action == 'create':
            return self._create_schedule(**kwargs)
        elif action == 'list':
            return self._list_schedules(**kwargs)
        elif action == 'get':
            return self._get_schedule(**kwargs)
        elif action == 'update':
            return self._update_schedule(**kwargs)
        elif action == 'delete':
            return self._delete_schedule(**kwargs)
        elif action == 'execute':
            return self._execute_schedule(**kwargs)
        elif action == 'get_executions':
            return self._get_schedule_executions(**kwargs)
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

    def _validate_cron(self, cron_str):
        """验证 cron 表达式并返回下次执行时间"""
        if croniter is None:
            raise ImportError("croniter 库未安装，请运行: pip install croniter")
        try:
            cron = croniter(cron_str, datetime.now())
            return cron.get_next(datetime)
        except Exception as e:
            raise ValueError(f"Cron 表达式无效: {str(e)}")

    def _convert_datetime_fields(self, obj):
        """将 datetime 字段转换为 ISO 格式字符串"""
        if not obj:
            return obj
        for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at', 'started_at', 'completed_at']:
            if field in obj and obj[field] and isinstance(obj[field], datetime):
                obj[field] = obj[field].isoformat()
        return obj

    def _create_schedule(self, **kwargs):
        """创建定时任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        # 获取参数
        name = kwargs.get('name')
        cron = kwargs.get('cron')
        command = kwargs.get('command')
        description = kwargs.get('description', '')
        preset = kwargs.get('preset', '')
        status = kwargs.get('status', 'active')
        
        if not name or not cron or not command:
            return {"success": False, "error": "缺少必要参数: name, cron, command"}
        
        try:
            next_run = self._validate_cron(cron)
        except (ImportError, ValueError) as e:
            return {"success": False, "error": str(e)}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 计算下次执行时间（仅当状态为 active 时）
                next_run_at = next_run if status == 'active' else None
                
                # 插入定时任务
                cursor.execute(
                    "INSERT INTO schedules (name, description, username, cron, preset, command, status, next_run_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (name, description, username, cron, preset, command, status, next_run_at)
                )
                schedule_id = cursor.lastrowid
                connection.commit()
                
                # 获取新创建的定时任务
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE id = %s",
                    (schedule_id,)
                )
                schedule = cursor.fetchone()
                schedule = self._convert_datetime_fields(schedule)
                
                return {
                    "success": True,
                    "message": "定时任务创建成功",
                    "schedule": schedule
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"创建定时任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _list_schedules(self, **kwargs):
        """列出定时任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        filters = kwargs.get('filters', {})
        status_filter = filters.get('status', 'all')
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 20)
        offset = (page - 1) * page_size
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 构建查询条件
                query = "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at FROM schedules WHERE username = %s"
                params = [username]
                
                if status_filter != 'all':
                    query += " AND status = %s"
                    params.append(status_filter)
                
                # 获取总数
                count_query = "SELECT COUNT(*) as total FROM schedules WHERE username = %s"
                count_params = [username]
                if status_filter != 'all':
                    count_query += " AND status = %s"
                    count_params.append(status_filter)
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()['total']
                
                # 获取分页数据
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([page_size, offset])
                
                cursor.execute(query, params)
                schedules = cursor.fetchall()
                
                # 转换日期字段
                schedules = [self._convert_datetime_fields(schedule) for schedule in schedules]
                
                return {
                    "success": True,
                    "schedules": schedules,
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
            return {"success": False, "error": f"获取定时任务列表失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _get_schedule(self, **kwargs):
        """获取单个定时任务详情"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        schedule_id = kwargs.get('schedule_id')
        if not schedule_id:
            return {"success": False, "error": "缺少必要参数: schedule_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                schedule = cursor.fetchone()
                
                if not schedule:
                    return {"success": False, "error": "定时任务不存在或无权访问"}
                
                schedule = self._convert_datetime_fields(schedule)
                return {"success": True, "schedule": schedule}
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"获取定时任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _update_schedule(self, **kwargs):
        """更新定时任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        schedule_id = kwargs.get('schedule_id')
        if not schedule_id:
            return {"success": False, "error": "缺少必要参数: schedule_id"}
        
        # 可更新字段
        updatable_fields = ['name', 'description', 'cron', 'preset', 'command', 'status']
        updates = {}
        for field in updatable_fields:
            if field in kwargs:
                updates[field] = kwargs[field]
        
        if not updates:
            return {"success": False, "error": "没有提供可更新的字段"}
        
        # 验证 cron 表达式（如果提供了的话）
        if 'cron' in updates:
            try:
                next_run = self._validate_cron(updates['cron'])
            except (ImportError, ValueError) as e:
                return {"success": False, "error": str(e)}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 检查任务是否存在且属于该用户
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return {"success": False, "error": "定时任务不存在或无权访问"}
                
                # 构建更新语句
                set_clauses = []
                params = []
                for field, value in updates.items():
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
                
                # 如果更新了 cron 或 status，重新计算 next_run_at
                if 'cron' in updates or 'status' in updates:
                    # 获取当前状态（可能更新后的状态）
                    new_status = updates.get('status')
                    if new_status:
                        status = new_status
                    else:
                        # 查询当前状态
                        cursor.execute("SELECT status FROM schedules WHERE id = %s", (schedule_id,))
                        status = cursor.fetchone()['status']
                    
                    # 计算下次执行时间
                    if status == 'active':
                        cron_str = updates.get('cron')
                        if not cron_str:
                            # 查询当前 cron
                            cursor.execute("SELECT cron FROM schedules WHERE id = %s", (schedule_id,))
                            cron_str = cursor.fetchone()['cron']
                        next_run = self._validate_cron(cron_str)
                        set_clauses.append("next_run_at = %s")
                        params.append(next_run)
                    else:
                        set_clauses.append("next_run_at = NULL")
                
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                
                update_sql = f"UPDATE schedules SET {', '.join(set_clauses)} WHERE id = %s AND username = %s"
                params.extend([schedule_id, username])
                
                cursor.execute(update_sql, params)
                connection.commit()
                
                # 获取更新后的任务
                cursor.execute(
                    "SELECT id, name, description, cron, preset, command, status, last_run_at, next_run_at, created_at, updated_at "
                    "FROM schedules WHERE id = %s",
                    (schedule_id,)
                )
                schedule = cursor.fetchone()
                schedule = self._convert_datetime_fields(schedule)
                
                return {
                    "success": True,
                    "message": "定时任务更新成功",
                    "schedule": schedule
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"更新定时任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _delete_schedule(self, **kwargs):
        """删除定时任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        schedule_id = kwargs.get('schedule_id')
        if not schedule_id:
            return {"success": False, "error": "缺少必要参数: schedule_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 检查任务是否存在且属于该用户
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return {"success": False, "error": "定时任务不存在或无权访问"}
                
                # 删除任务
                cursor.execute(
                    "DELETE FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                connection.commit()
                
                return {"success": True, "message": "定时任务删除成功"}
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"删除定时任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _execute_schedule(self, **kwargs):
        """立即执行定时任务"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        schedule_id = kwargs.get('schedule_id')
        if not schedule_id:
            return {"success": False, "error": "缺少必要参数: schedule_id"}
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 获取任务信息
                cursor.execute(
                    "SELECT id, name, command FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                schedule = cursor.fetchone()
                
                if not schedule:
                    return {"success": False, "error": "定时任务不存在或无权访问"}
                
                # 这里可以调用 scheduler 的立即执行功能
                # 由于 scheduler 在独立进程中运行，我们可以直接插入执行记录并触发执行
                # 简化处理：返回成功，提示用户通过界面执行
                return {
                    "success": True,
                    "message": "立即执行功能需要通过定时任务管理界面操作，请访问 /schedules 页面",
                    "schedule": schedule
                }
                
        except pymysql.Error as e:
            return {"success": False, "error": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"执行定时任务失败: {str(e)}"}
        finally:
            if connection:
                connection.close()

    def _get_schedule_executions(self, **kwargs):
        """获取定时任务执行记录"""
        try:
            username = self._get_username(kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        schedule_id = kwargs.get('schedule_id')
        if not schedule_id:
            return {"success": False, "error": "缺少必要参数: schedule_id"}
        
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 20)
        offset = (page - 1) * page_size
        
        connection = None
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # 检查任务是否存在且属于该用户
                cursor.execute(
                    "SELECT id FROM schedules WHERE id = %s AND username = %s",
                    (schedule_id, username)
                )
                if not cursor.fetchone():
                    return {"success": False, "error": "定时任务不存在或无权访问"}
                
                # 获取执行记录总数
                cursor.execute(
                    "SELECT COUNT(*) as total FROM schedule_executions WHERE schedule_id = %s",
                    (schedule_id,)
                )
                total = cursor.fetchone()['total']
                
                # 获取分页执行记录
                cursor.execute(
                    "SELECT id, execution_id, status, output, error_message, started_at, completed_at, created_at "
                    "FROM schedule_executions WHERE schedule_id = %s "
                    "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (schedule_id, page_size, offset)
                )
                executions = cursor.fetchall()
                
                executions = [self._convert_datetime_fields(execution) for execution in executions]
                
                return {
                    "success": True,
                    "executions": executions,
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
            return {"success": False, "error": f"获取执行记录失败: {str(e)}"}
        finally:
            if connection:
                connection.close()


if __name__ == "__main__":
    skill = ScheduleSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\nParameters schema:")
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    print(f"\nTest execution (模拟):")
    print("需要提供 _username 参数进行测试")