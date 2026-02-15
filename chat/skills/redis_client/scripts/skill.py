"""
Redis 客户端技能 - 连接远程 Redis 并执行常见读写操作

A skill for connecting to remote Redis and performing common read/write operations.
"""

import sys
import os
import json
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill

try:
    import redis
except ImportError:
    redis = None


class RedisClientSkill(BaseSkill):
    """Redis 客户端技能"""

    def get_name(self) -> str:
        return "redis_client"

    def get_description(self) -> str:
        return "连接远程 Redis 并执行常见的读写操作，包括设置/获取值、哈希操作、列表操作、集合操作等。"

    def get_parameters(self) -> Dict[str, Any]:
        from typing import Dict, Any
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "Redis 服务器地址（IP 或域名）",
                    "default": "localhost"
                },
                "port": {
                    "type": "integer",
                    "description": "Redis 端口号",
                    "default": 6379
                },
                "password": {
                    "type": "string",
                    "description": "Redis 密码（如有）",
                    "default": ""
                },
                "db": {
                    "type": "integer",
                    "description": "Redis 数据库编号（0-15）",
                    "default": 0
                },
                "operation": {
                    "type": "string",
                    "enum": ["get", "set", "delete", "exists", "keys", "hget", "hset", "hgetall", "lpush", "rpush", "lrange", "sadd", "smembers", "sismember", "zadd", "zrange", "info", "ping", "flushdb"],
                    "description": "要执行的 Redis 操作类型"
                },
                "key": {
                    "type": "string",
                    "description": "Redis 键名"
                },
                "value": {
                    "type": "string",
                    "description": "要设置的值（用于 set, hset, lpush, rpush, sadd, zadd 操作）"
                },
                "field": {
                    "type": "string",
                    "description": "哈希字段名（用于 hget, hset 操作）"
                },
                "score": {
                    "type": "number",
                    "description": "有序集合分数（用于 zadd 操作）"
                },
                "start": {
                    "type": "integer",
                    "description": "列表/集合起始索引（用于 lrange, zrange）",
                    "default": 0
                },
                "end": {
                    "type": "integer",
                    "description": "列表/集合结束索引（用于 lrange, zrange，-1 表示末尾）",
                    "default": -1
                },
                "pattern": {
                    "type": "string",
                    "description": "键匹配模式（用于 keys 操作）",
                    "default": "*"
                }
            },
            "required": ["operation"]
        }

    def execute(self, host: str = "localhost", port: int = 6379, password: str = "", db: int = 0, 
                operation: str = "ping", key: str = None, value: str = None, field: str = None, 
                score: float = None, start: int = 0, end: int = -1, pattern: str = "*", **kwargs) -> Dict[str, Any]:
        """
        执行 Redis 操作

        Args:
            host: Redis 服务器地址
            port: Redis 端口
            password: Redis 密码
            db: Redis 数据库编号
            operation: 操作类型
            key: 键名
            value: 值
            field: 哈希字段
            score: 有序集合分数
            start: 起始索引
            end: 结束索引
            pattern: 键匹配模式

        Returns:
            Dict[str, Any]: 操作结果
        """
        if redis is None:
            return {
                "success": False,
                "error": "redis Python 库未安装，请运行: pip install redis"
            }

        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password if password else None,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            if operation == "ping":
                result = client.ping()
                return {
                    "success": True,
                    "result": result,
                    "message": "PONG" if result else "Redis 连接失败"
                }

            elif operation == "info":
                info = client.info()
                return {
                    "success": True,
                    "result": info,
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime_days": info.get("uptime_days")
                }

            elif operation == "flushdb":
                result = client.flushdb()
                return {
                    "success": True,
                    "result": result,
                    "message": "数据库已清空" if result else "操作失败"
                }

            elif operation == "get":
                if not key:
                    return {"success": False, "error": "get 操作需要指定 key 参数"}
                result = client.get(key)
                return {
                    "success": True,
                    "key": key,
                    "value": result,
                    "exists": result is not None
                }

            elif operation == "set":
                if not key or value is None:
                    return {"success": False, "error": "set 操作需要指定 key 和 value 参数"}
                result = client.set(key, value)
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "value": value,
                    "message": f"已设置 {key} = {value}"
                }

            elif operation == "delete":
                if not key:
                    return {"success": False, "error": "delete 操作需要指定 key 参数"}
                result = client.delete(key)
                return {
                    "success": True,
                    "result": result,
                    "deleted": result > 0,
                    "message": f"已删除 {result} 个键"
                }

            elif operation == "exists":
                if not key:
                    return {"success": False, "error": "exists 操作需要指定 key 参数"}
                result = client.exists(key)
                return {
                    "success": True,
                    "key": key,
                    "exists": result > 0,
                    "count": result
                }

            elif operation == "keys":
                result = client.keys(pattern)
                return {
                    "success": True,
                    "pattern": pattern,
                    "keys": result,
                    "count": len(result)
                }

            elif operation == "hget":
                if not key or not field:
                    return {"success": False, "error": "hget 操作需要指定 key 和 field 参数"}
                result = client.hget(key, field)
                return {
                    "success": True,
                    "key": key,
                    "field": field,
                    "value": result,
                    "exists": result is not None
                }

            elif operation == "hset":
                if not key or not field or value is None:
                    return {"success": False, "error": "hset 操作需要指定 key、field 和 value 参数"}
                result = client.hset(key, field, value)
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "field": field,
                    "value": value,
                    "message": f"已设置哈希 {key} 的字段 {field} = {value}"
                }

            elif operation == "hgetall":
                if not key:
                    return {"success": False, "error": "hgetall 操作需要指定 key 参数"}
                result = client.hgetall(key)
                return {
                    "success": True,
                    "key": key,
                    "fields": result,
                    "count": len(result)
                }

            elif operation == "lpush":
                if not key or value is None:
                    return {"success": False, "error": "lpush 操作需要指定 key 和 value 参数"}
                result = client.lpush(key, value)
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "value": value,
                    "message": f"已左插入 {value} 到列表 {key}"
                }

            elif operation == "rpush":
                if not key or value is None:
                    return {"success": False, "error": "rpush 操作需要指定 key 和 value 参数"}
                result = client.rpush(key, value)
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "value": value,
                    "message": f"已右插入 {value} 到列表 {key}"
                }

            elif operation == "lrange":
                if not key:
                    return {"success": False, "error": "lrange 操作需要指定 key 参数"}
                result = client.lrange(key, start, end)
                return {
                    "success": True,
                    "key": key,
                    "start": start,
                    "end": end,
                    "items": result,
                    "count": len(result)
                }

            elif operation == "sadd":
                if not key or value is None:
                    return {"success": False, "error": "sadd 操作需要指定 key 和 value 参数"}
                result = client.sadd(key, value)
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "value": value,
                    "message": f"已添加 {value} 到集合 {key}"
                }

            elif operation == "smembers":
                if not key:
                    return {"success": False, "error": "smembers 操作需要指定 key 参数"}
                result = client.smembers(key)
                return {
                    "success": True,
                    "key": key,
                    "members": list(result),
                    "count": len(result)
                }

            elif operation == "sismember":
                if not key or value is None:
                    return {"success": False, "error": "sismember 操作需要指定 key 和 value 参数"}
                result = client.sismember(key, value)
                return {
                    "success": True,
                    "key": key,
                    "value": value,
                    "is_member": result
                }

            elif operation == "zadd":
                if not key or value is None or score is None:
                    return {"success": False, "error": "zadd 操作需要指定 key、value 和 score 参数"}
                result = client.zadd(key, {value: score})
                return {
                    "success": True,
                    "result": result,
                    "key": key,
                    "value": value,
                    "score": score,
                    "message": f"已添加 {value} (score={score}) 到有序集合 {key}"
                }

            elif operation == "zrange":
                if not key:
                    return {"success": False, "error": "zrange 操作需要指定 key 参数"}
                result = client.zrange(key, start, end, withscores=True)
                return {
                    "success": True,
                    "key": key,
                    "start": start,
                    "end": end,
                    "items": [{"member": m, "score": s} for m, s in result],
                    "count": len(result)
                }

            else:
                return {
                    "success": False,
                    "error": f"不支持的操作: {operation}"
                }

        except redis.ConnectionError as e:
            return {
                "success": False,
                "error": f"Redis 连接失败: {str(e)}",
                "host": host,
                "port": port
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Redis 操作失败: {str(e)}",
                "operation": operation
            }


if __name__ == "__main__":
    skill = RedisClientSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\nTest ping:")
    print(skill.execute(operation="ping"))
    print(f"\nTest info:")
    print(skill.execute(operation="info"))
