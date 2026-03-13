"""
QQ消息发送技能 - 通过QQ机器人HTTP API发送消息

A skill for sending messages via QQ bot HTTP API.
"""

import sys
import os
import json
from typing import Dict, Any
import requests

# Add project root to path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import BaseSkill with fallback for standalone execution
try:
    from skills.base import BaseSkill
except ImportError:
    # Fallback for standalone execution
    from base import BaseSkill


class QQMessageSkill(BaseSkill):
    """通过QQ机器人HTTP API发送消息的技能"""

    def get_name(self) -> str:
        return "qq_message"

    def get_description(self) -> str:
        return "通过QQ机器人的HTTP API发送消息到QQ好友、群聊或讨论组。支持发送文本消息、图片消息等。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_url": {
                    "type": "string",
                    "description": "QQ机器人HTTP API地址，用于发送消息的端点",
                },
                "message": {
                    "type": "string",
                    "description": "要发送的消息内容。支持纯文本或JSON格式的消息",
                },
                "message_type": {
                    "type": "string",
                    "description": "消息发送类型，支持 private_msg（私聊）、group_msg（群消息） 等类型，默认为 private_msg",
                    "default": "private_msg"
                }
            },
            "required": ["api_url", "message"]
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行QQ消息发送

        Args:
            **kwargs: 包含 api_url, message, message_type 等参数

        Returns:
            Dict[str, Any]: 发送结果
        """
        api_url = kwargs.get('api_url')
        message = kwargs.get('message')
        message_type = kwargs.get('message_type', 'private_msg')
        
        # 参数验证
        if not api_url:
            return {
                "success": False,
                "message": "缺少必需参数: api_url",
                "response": None
            }
        
        if not message:
            return {
                "success": False,
                "message": "缺少必需参数: message",
                "response": None
            }
        try:
            # 验证api_url格式
            if not api_url.startswith(('http://', 'https://')):
                return {
                    "success": False,
                    "message": "无效的API URL: 必须以 http:// 或 https:// 开头",
                    "response": None
                }
            
            # 准备请求数据
            if not message.startswith('{'):
                # 如果是纯文本消息且不是JSON格式，则包装为标准格式
                # 默认根据message_type决定发送对象
                if message_type == "group_msg":
                    payload = {
                        "message": message
                    }
                    # 群消息可能需要group_id，但这里保持简单，由调用者在message中提供
                else:  # private_msg 或其他
                    payload = {
                        "message": message
                    }
                    # 私聊消息可能需要user_id，同样由调用者在message中提供
            else:
                # 尝试解析为JSON格式的消息
                try:
                    payload = json.loads(message)
                    # 如果没有指定消息类型字段，添加默认类型
                    # 这里假设消息内容本身已经包含了必要的字段如user_id或group_id
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，则作为纯文本处理
                    if message_type == "group_msg":
                        payload = {
                            "message": message
                        }
                    else:
                        payload = {
                            "message": message
                        }
            
            # 发送请求
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            # 处理响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            # 检查响应状态
            if response.status_code == 200:
                # 检查业务层面的成功状态（不同框架可能有不同的返回格式）
                # 常见的成功标志：status == "ok" 或 retcode == 0
                if (isinstance(response_data, dict) and 
                    ((response_data.get("status") == "ok") or 
                     (response_data.get("retcode") == 0) or
                     (response_data.get("code") == 0))):
                    return {
                        "success": True,
                        "message": "消息发送成功",
                        "response": {
                            "status_code": response.status_code,
                            "data": response_data
                        }
                    }
                else:
                    # 即使业务层面失败，只要HTTP返回200也算发送成功（但可能有业务错误）
                    return {
                        "success": True,
                        "message": "消息已发送（API返回200）",
                        "response": {
                            "status_code": response.status_code,
                            "data": response_data
                        }
                    }
            else:
                return {
                    "success": False,
                    "message": f"消息发送失败: HTTP {response.status_code}",
                    "response": {
                        "status_code": response.status_code,
                        "data": response_data
                    }
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "请求超时，请检查网络连接",
                "response": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"网络请求失败: {str(e)}",
                "response": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"发送失败: {str(e)}",
                "response": None
            }


# 独立测试
if __name__ == "__main__":
    skill = QQMessageSkill()
    print(f"技能名称: {skill.name}")
    print(f"描述: {skill.description}")
    print(f"\n参数定义:")
    import json
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    
    # 注意：这里不会实际发送请求，因为需要有效的api_url
    print(f"\n测试执行 - 使用无效URL（预期会失败）:")
    result = skill.execute(
        api_url="https://example.com/api",
        message="测试消息",
        message_type="private_msg"
    )
    print(result)
