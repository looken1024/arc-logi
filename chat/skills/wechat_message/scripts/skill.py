"""
微信消息发送技能 - 通过微信机器人Webhook发送消息

A skill for sending messages via WeChat bot webhook.
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


class WechatMessageSkill(BaseSkill):
    """通过微信机器人Webhook发送消息的技能"""

    def get_name(self) -> str:
        return "wechat_message"

    def get_description(self) -> str:
        return "通过微信机器人的Webhook发送消息到微信群聊或个人。支持发送文本消息、Markdown消息、图文消息等。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "description": "微信机器人Webhook URL，用于发送消息的地址",
                },
                "message": {
                    "type": "string",
                    "description": "要发送的消息内容。支持纯文本或JSON格式的消息",
                },
                "msg_type": {
                    "type": "string",
                    "description": "消息类型，支持 text、markdown、news 等类型，默认为 text",
                    "default": "text"
                }
            },
            "required": ["webhook_url", "message"]
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行微信消息发送

        Args:
            **kwargs: 包含 webhook_url, message, msg_type 等参数

        Returns:
            Dict[str, Any]: 发送结果
        """
        webhook_url = kwargs.get('webhook_url')
        message = kwargs.get('message')
        msg_type = kwargs.get('msg_type', 'text')
        
        # 参数验证
        if not webhook_url:
            return {
                "success": False,
                "message": "缺少必需参数: webhook_url",
                "response": None
            }
        
        if not message:
            return {
                "success": False,
                "message": "缺少必需参数: message",
                "response": None
            }
        try:
            # 验证webhook_url格式
            if not webhook_url.startswith(('http://', 'https://')):
                return {
                    "success": False,
                    "message": "无效的Webhook URL: 必须以 http:// 或 https:// 开头",
                    "response": None
                }
            
            # 准备请求数据
            if msg_type == "text" and not message.startswith('{'):
                # 如果是纯文本消息且不是JSON格式，则包装为标准文本消息格式
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": message
                    }
                }
            else:
                # 尝试解析为JSON格式的消息
                try:
                    payload = json.loads(message)
                    # 确保包含msgtype字段
                    if "msgtype" not in payload:
                        payload["msgtype"] = msg_type
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，则作为纯文本处理
                    payload = {
                        "msgtype": msg_type,
                        "text": {
                            "content": message
                        }
                    }
            
            # 发送请求
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                webhook_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            # 处理响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            # 检查微信API响应（企业微信机器人API）
            if response.status_code == 200 and response_data.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "消息发送成功",
                    "response": {
                        "status_code": response.status_code,
                        "data": response_data
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"消息发送失败: {response_data.get('errmsg', '未知错误')}",
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
    skill = WechatMessageSkill()
    print(f"技能名称: {skill.name}")
    print(f"描述: {skill.description}")
    print(f"\n参数定义:")
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    
    # 注意：这里不会实际发送请求，因为需要有效的webhook_url
    print(f"\n测试执行 - 使用无效URL（预期会失败）:")
    result = skill.execute(
        webhook_url="https://example.com/webhook",
        message="测试消息",
        msg_type="text"
    )
    print(result)
