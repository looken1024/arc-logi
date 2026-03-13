#!/usr/bin/env python3
"""
测试飞书消息技能加载
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skills import register_all_skills

if __name__ == "__main__":
    print("开始测试技能加载...")
    
    try:
        registry = register_all_skills()
        
        print(f"\n✅ 技能加载完成！共注册 {len(registry)} 个技能")
        print("已注册技能:")
        for skill_name in registry.list_skills():
            skill = registry.get_skill(skill_name)
            print(f"  - {skill_name}: {skill.description}")
            
            # 测试技能函数定义
            func_def = skill.to_function_definition()
            print(f"    参数: {func_def['parameters']}")
            
            # 获取技能文档
            readme = registry.get_skill_readme(skill_name)
            if readme and len(readme) > 0:
                print(f"    文档: {readme[:100]}...")
            
            print()
        
        # 特别检查飞书消息技能
        if "feishu_message" in registry.list_skills():
            print("🎉 飞书消息技能加载成功！")
            
            # 测试技能执行（模拟）
            skill = registry.get_skill("feishu_message")
            print("测试技能执行（模拟参数）:")
            result = skill.execute(message="测试消息", webhook_url="https://example.com/hook")
            print(f"结果: {result}")
        else:
            print("❌ 飞书消息技能未加载")
            print("已发现技能:", registry.list_skills())
            
    except Exception as e:
        print(f"❌ 技能加载失败: {e}")
        import traceback
        traceback.print_exc()