"""
邮件发送技能 - 通过SMTP协议发送邮件

A skill for sending emails via SMTP.
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Any

# Add project root to path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import BaseSkill with fallback for standalone execution
try:
    from skills.base import BaseSkill
except ImportError:
    # Fallback for standalone execution
    from base import BaseSkill


class EmailSenderSkill(BaseSkill):
    """通过SMTP协议发送邮件的技能"""

    def get_name(self) -> str:
        return "email_sender"

    def get_description(self) -> str:
        return "通过SMTP协议发送电子邮件。支持发送纯文本邮件和HTML格式邮件。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "smtp_server": {
                    "type": "string",
                    "description": "SMTP服务器地址",
                },
                "smtp_port": {
                    "type": "integer",
                    "description": "SMTP服务器端口",
                },
                "sender_email": {
                    "type": "string",
                    "description": "发送者邮箱地址",
                },
                "sender_password": {
                    "type": "string",
                    "description": "发送者邮箱密码或授权码",
                },
                "receiver_email": {
                    "type": "string",
                    "description": "接收者邮箱地址，多个地址用逗号分隔",
                },
                "subject": {
                    "type": "string",
                    "description": "邮件主题",
                },
                "content": {
                    "type": "string",
                    "description": "邮件内容",
                },
                "content_type": {
                    "type": "string",
                    "description": "邮件内容类型，支持 plain（纯文本） 或 html（HTML格式），默认为 plain",
                    "default": "plain"
                },
                "use_ssl": {
                    "type": "boolean",
                    "description": "是否使用SSL加密连接，默认为 true",
                    "default": True
                }
            },
            "required": ["smtp_server", "smtp_port", "sender_email", "sender_password", "receiver_email", "subject", "content"]
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行邮件发送

        Args:
            **kwargs: 包含 smtp_server, smtp_port, sender_email, sender_password, 
                     receiver_email, subject, content, content_type, use_ssl 等参数

        Returns:
            Dict[str, Any]: 发送结果
        """
        smtp_server = kwargs.get('smtp_server')
        smtp_port = kwargs.get('smtp_port')
        sender_email = kwargs.get('sender_email')
        sender_password = kwargs.get('sender_password')
        receiver_email = kwargs.get('receiver_email')
        subject = kwargs.get('subject')
        content = kwargs.get('content')
        content_type = kwargs.get('content_type', 'plain')
        use_ssl = kwargs.get('use_ssl', True)
        
        # 参数验证
        required_params = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'receiver_email', 'subject', 'content']
        for param in required_params:
            if not kwargs.get(param):
                return {
                    "success": False,
                    "message": f"缺少必需参数: {param}",
                    "response": None
                }
        
        # 验证content_type参数
        if content_type not in ['plain', 'html']:
            return {
                "success": False,
                "message": "content_type 参数必须是 'plain' 或 'html'",
                "response": None
            }
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = formataddr(["发送者", sender_email])  # 发送者姓名可以自定义
            msg['To'] = receiver_email  # 接收者可以是多个，用逗号分隔
            msg['Subject'] = subject
            
            # 添加邮件正文
            if content_type == 'html':
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送邮件
            if use_ssl:
                # 使用SSL连接
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # 使用普通连接
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()  # 启用TLS加密
            
            # 登录
            server.login(sender_email, sender_password)
            
            # 发送邮件
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email.split(','), text)
            
            # 关闭连接
            server.quit()
            
            return {
                "success": True,
                "message": "邮件发送成功",
                "response": None
            }
            
        except smtplib.SMTPConnectError as e:
            return {
                "success": False,
                "message": f"SMTP连接失败: {str(e)}",
                "response": None
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "message": f"登录认证失败: 用户名或密码错误 - {str(e)}",
                "response": None
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                "success": False,
                "message": f"收件人地址被拒绝: {str(e)}",
                "response": None
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "message": f"SMTP错误: {str(e)}",
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
    skill = EmailSenderSkill()
    print(f"技能名称: {skill.name}")
    print(f"描述: {skill.description}")
    print(f"\n参数定义:")
    import json
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    
    # 注意：这里不会实际发送请求，因为需要有效的SMTP凭据
    print(f"\n测试执行 - 使用无效参数（预期会失败）:")
    result = skill.execute(
        smtp_server="invalid.smtp.server",
        smtp_port=465,
        sender_email="test@example.com",
        sender_password="wrong_password",
        receiver_email="receiver@example.com",
        subject="测试邮件",
        content="这是一封测试邮件",
        content_type="plain",
        use_ssl=True
    )
    print(result)
