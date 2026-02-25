"""
MySQL 客户端技能 - 连接远程 MySQL 并执行常见的增删改查操作

A skill for connecting to remote MySQL and performing common CRUD operations.
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None


class MySQLClientSkill(BaseSkill):
    """MySQL 客户端技能"""

    def get_name(self) -> str:
        return "mysql_client"

    def get_description(self) -> str:
        return "连接远程 MySQL 数据库并执行增删改查操作，包括查询数据、插入数据、更新数据、删除数据、创建表等。"

    def get_parameters(self) -> Dict[str, Any]:
        from typing import Dict, Any
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "MySQL 服务器地址（IP 或域名）",
                    "default": "localhost"
                },
                "port": {
                    "type": "integer",
                    "description": "MySQL 端口号",
                    "default": 3306
                },
                "user": {
                    "type": "string",
                    "description": "MySQL 用户名",
                    "default": "root"
                },
                "password": {
                    "type": "string",
                    "description": "MySQL 密码",
                    "default": ""
                },
                "database": {
                    "type": "string",
                    "description": "数据库名称",
                    "default": ""
                },
                "charset": {
                    "type": "string",
                    "description": "字符编码",
                    "default": "utf8mb4"
                },
                "operation": {
                    "type": "string",
                    "enum": ["query", "insert", "update", "delete", "execute", "show_tables", "show_databases", "describe", "ping"],
                    "description": "要执行的 MySQL 操作类型"
                },
                "table": {
                    "type": "string",
                    "description": "表名（用于 insert, update, delete, describe, show_tables）"
                },
                "data": {
                    "type": "object",
                    "description": "要插入或更新的数据（JSON 对象，用于 insert, update 操作）"
                },
                "condition": {
                    "type": "object",
                    "description": "更新/删除条件（JSON 对象，用于 update, delete 操作）"
                },
                "sql": {
                    "type": "string",
                    "description": "自定义 SQL 语句（用于 execute 操作）"
                },
                "limit": {
                    "type": "integer",
                    "description": "查询结果返回数量限制",
                    "default": 100
                }
            },
            "required": ["operation"]
        }

    def _get_connection(self, host: str, port: int, user: str, password: str, database: str, charset: str):
        """建立 MySQL 连接"""
        return pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database if database else None,
            charset=charset,
            cursorclass=DictCursor,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )

    def execute(self, host: str = "localhost", port: int = 3306, user: str = "root", 
                password: str = "", database: str = "", charset: str = "utf8mb4",
                operation: str = "ping", table: str = "", data: dict = None, 
                condition: dict = None, sql: str = "", limit: int = 100, **kwargs) -> Dict[str, Any]:
        """
        执行 MySQL 操作

        Args:
            host: MySQL 服务器地址
            port: MySQL 端口
            user: MySQL 用户名
            password: MySQL 密码
            database: 数据库名称
            charset: 字符编码
            operation: 操作类型
            table: 表名
            data: 插入或更新的数据
            condition: 更新/删除条件
            sql: 自定义 SQL 语句
            limit: 查询结果数量限制

        Returns:
            Dict[str, Any]: 操作结果
        """
        if pymysql is None:
            return {
                "success": False,
                "error": "pymysql Python 库未安装，请运行: pip install pymysql"
            }

        if data is None:
            data = {}
        if condition is None:
            condition = {}

        try:
            conn = self._get_connection(host, port, user, password, database, charset)
            
            try:
                if operation == "ping":
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1 as result")
                        result = cursor.fetchone()
                        return {
                            "success": True,
                            "result": result,
                            "message": "MySQL 连接成功"
                        }

                elif operation == "show_databases":
                    with conn.cursor() as cursor:
                        cursor.execute("SHOW DATABASES")
                        results = cursor.fetchall()
                        databases = [row.get('Database') for row in results]
                        return {
                            "success": True,
                            "databases": databases,
                            "count": len(databases)
                        }

                elif operation == "show_tables":
                    if not database:
                        return {"success": False, "error": "show_tables 操作需要指定 database 参数"}
                    with conn.cursor() as cursor:
                        cursor.execute("SHOW TABLES")
                        results = cursor.fetchall()
                        table_key = f"Tables_in_{database}"
                        tables = [row.get(table_key) for row in results]
                        return {
                            "success": True,
                            "database": database,
                            "tables": tables,
                            "count": len(tables)
                        }

                elif operation == "describe":
                    if not table:
                        return {"success": False, "error": "describe 操作需要指定 table 参数"}
                    if not database:
                        return {"success": False, "error": "describe 操作需要指定 database 参数"}
                    with conn.cursor() as cursor:
                        cursor.execute(f"DESCRIBE `{table}`")
                        results = cursor.fetchall()
                        columns = []
                        for row in results:
                            columns.append({
                                "field": row.get("Field"),
                                "type": row.get("Type"),
                                "null": row.get("Null"),
                                "key": row.get("Key"),
                                "default": row.get("Default"),
                                "extra": row.get("Extra")
                            })
                        return {
                            "success": True,
                            "table": table,
                            "columns": columns,
                            "count": len(columns)
                        }

                elif operation == "query":
                    if not table:
                        return {"success": False, "error": "query 操作需要指定 table 参数"}
                    
                    query_sql = f"SELECT * FROM `{table}`"
                    params = []
                    
                    if condition:
                        where_clauses = []
                        for key, value in condition.items():
                            where_clauses.append(f"`{key}` = %s")
                            params.append(value)
                        if where_clauses:
                            query_sql += " WHERE " + " AND ".join(where_clauses)
                    
                    query_sql += f" LIMIT {int(limit)}"
                    
                    with conn.cursor() as cursor:
                        cursor.execute(query_sql, params)
                        results = cursor.fetchall()
                        return {
                            "success": True,
                            "table": table,
                            "data": results,
                            "count": len(results)
                        }

                elif operation == "insert":
                    if not table:
                        return {"success": False, "error": "insert 操作需要指定 table 参数"}
                    if not data:
                        return {"success": False, "error": "insert 操作需要指定 data 参数"}
                    
                    columns = ", ".join([f"`{k}`" for k in data.keys()])
                    placeholders = ", ".join(["%s"] * len(data))
                    insert_sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
                    
                    with conn.cursor() as cursor:
                        affected = cursor.execute(insert_sql, list(data.values()))
                        conn.commit()
                        insert_id = cursor.lastrowid
                        return {
                            "success": True,
                            "table": table,
                            "affected_rows": affected,
                            "insert_id": insert_id,
                            "message": f"成功插入 {affected} 行数据"
                        }

                elif operation == "update":
                    if not table:
                        return {"success": False, "error": "update 操作需要指定 table 参数"}
                    if not data:
                        return {"success": False, "error": "update 操作需要指定 data 参数"}
                    if not condition:
                        return {"success": False, "error": "update 操作需要指定 condition 参数，以防止误更新"}
                    
                    set_clauses = ", ".join([f"`{k}` = %s" for k in data.keys()])
                    where_clauses = ", ".join([f"`{k}` = %s" for k in condition.keys()])
                    update_sql = f"UPDATE `{table}` SET {set_clauses} WHERE {where_clauses}"
                    
                    params = list(data.values()) + list(condition.values())
                    
                    with conn.cursor() as cursor:
                        affected = cursor.execute(update_sql, params)
                        conn.commit()
                        return {
                            "success": True,
                            "table": table,
                            "affected_rows": affected,
                            "message": f"成功更新 {affected} 行数据"
                        }

                elif operation == "delete":
                    if not table:
                        return {"success": False, "error": "delete 操作需要指定 table 参数"}
                    if not condition:
                        return {"success": False, "error": "delete 操作需要指定 condition 参数，以防止误删除"}
                    
                    where_clauses = ", ".join([f"`{k}` = %s" for k in condition.keys()])
                    delete_sql = f"DELETE FROM `{table}` WHERE {where_clauses}"
                    
                    with conn.cursor() as cursor:
                        affected = cursor.execute(delete_sql, list(condition.values()))
                        conn.commit()
                        return {
                            "success": True,
                            "table": table,
                            "affected_rows": affected,
                            "message": f"成功删除 {affected} 行数据"
                        }

                elif operation == "execute":
                    if not sql:
                        return {"success": False, "error": "execute 操作需要指定 sql 参数"}
                    
                    sql_upper = sql.strip().upper()
                    is_select = sql_upper.startswith("SELECT")
                    
                    with conn.cursor() as cursor:
                        cursor.execute(sql)
                        if is_select:
                            results = cursor.fetchall()
                            return {
                                "success": True,
                                "sql": sql,
                                "data": results,
                                "count": len(results)
                            }
                        else:
                            conn.commit()
                            return {
                                "success": True,
                                "sql": sql,
                                "affected_rows": cursor.rowcount,
                                "message": f"SQL 执行成功，影响 {cursor.rowcount} 行"
                            }

                else:
                    return {
                        "success": False,
                        "error": f"不支持的操作: {operation}"
                    }

            finally:
                conn.close()

        except pymysql.Error as e:
            return {
                "success": False,
                "error": f"MySQL 操作失败: {str(e)}",
                "operation": operation
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"执行失败: {str(e)}",
                "operation": operation
            }


if __name__ == "__main__":
    skill = MySQLClientSkill()
    print(f"Skill: {skill.get_name()}")
    print(f"Description: {skill.get_description()}")
    print(f"\nTest ping:")
    print(skill.execute(operation="ping", host="localhost", user="root", password=""))
    print(f"\nTest show_databases:")
    print(skill.execute(operation="show_databases", host="localhost", user="root", password=""))
