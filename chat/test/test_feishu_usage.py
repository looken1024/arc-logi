#!/usr/bin/env python3
"""
测试飞书消息技能使用示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills import register_all_skills

def test_feishu_skill():
    """测试飞书消息技能"""
    print("=== 测试飞书消息技能 ===")
    
    # 注册所有技能
    registry = register_all_skills()
    
    # 检查飞书消息技能是否存在
    if "feishu_message" not in registry.list_skills():
        print("❌ 飞书消息技能未找到")
        return False
    
    print("✅ 飞书消息技能已找到")
    
    # 获取技能实例
    skill = registry.get_skill("feishu_message")
    print(f"技能名称: {skill.name}")
    print(f"技能描述: {skill.description}")
    
    # 显示参数定义
    print("\n参数定义:")
    import json
    print(json.dumps(skill.get_parameters(), indent=2, ensure_ascii=False))
    
    # 演示如何构建调用参数（不实际发送）
    print("\n=== 参数使用示例 ===")
    example_args = {
        "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-key-here",
        "message": "这是一条测试消息，来自AI助手",
        "msg_type": "text"
    }
    print("发送文本消息示例:")
    print(json.dumps(example_args, indent=2, ensure_ascii=False))
    
    # 发送富文本消息示例
    rich_text_example = {
        "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-key-here",
        "message": "{\"msg_type\": \"post\", \"content\": {\"post\": {\"zh_cn\": {\"title\": \"项目状态更新\", \"content\": [[{\"tag\": \"text\", \"text\": \"项目当前状态：进行中\\n\"}, {\"tag\": \"text\", \"text\": \"已完成任务：需求分析、UI设计\\n\"}, {\"tag\": \"text\", \"text\": \"进行中任务：前端开发、后端接口\\n\"}, {\"tag\": \"text\", \"text\": \"下一步计划：功能测试、BUG修复\"}]}}}}",
        "msg_type": "post"
    }
    print("\n发送富文本消息示例:")
    print(json.dumps(rich_text_example, indent=2, ensure_ascii=False))
    
    # 测试技能执行（使用无效URL，预期会失败但不会崩溃）
    print("\n=== 技能执行测试 ===")
    print("测试执行（使用示例URL，预期会失败）:")
    result = skill.execute(
        webhook_url="https://httpbin.org/status/404",  # 使用返回404的测试URL
        message="测试消息",
        msg_type="text"
    )
    print(f"执行结果: {result}")
    
    # 测试参数验证
    print("\n测试参数验证:")
    result = skill.execute(
        webhook_url="",  # 空URL
        message="测试消息"
    )
    print(f"空URL测试结果: {result}")
    
    result = skill.execute(
        webhook_url="https://example.com/webhook",
        message=""  # 空消息
    )
    print(f"空消息测试结果: {result}")
    
    print("\n✅ 飞书消息技能测试完成")
    return True

if __name__ == "__main__":
    test_feishu_skill()