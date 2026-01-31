#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skills 系统测试脚本

测试所有已注册的技能是否正常工作
"""

import sys
import io
from skills import register_all_skills
from datetime import datetime

# 设置输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*50}")
        print(f"  {title}")
        print('='*50)
    else:
        print('-'*50)


def test_skill_registry():
    """测试技能注册表"""
    print_separator("测试技能注册表")
    
    registry = register_all_skills()
    
    print(f"✅ 技能注册表初始化成功")
    print(f"📊 已注册技能数量: {len(registry)}")
    print(f"📋 技能列表: {', '.join(registry.list_skills())}")
    
    return registry


def test_date_skill(registry):
    """测试日期技能"""
    print_separator("测试 get_current_date 技能")
    
    # 测试 1: 获取完整信息
    print("\n测试 1: 获取完整日期时间信息")
    result = registry.execute_skill("get_current_date", format="full")
    
    if result['success']:
        data = result['data']
        print(f"✅ 执行成功")
        print(f"   年份: {data.get('year')}")
        print(f"   月份: {data.get('month')}")
        print(f"   日期: {data.get('day')}")
        print(f"   星期: {data.get('weekday')}")
        print(f"   时间: {data.get('hour')}:{data.get('minute')}:{data.get('second')}")
        print(f"   格式化: {data.get('formatted')}")
        print(f"   描述: {data.get('description')}")
    else:
        print(f"❌ 执行失败: {result.get('error')}")
    
    # 测试 2: 仅获取日期
    print("\n测试 2: 仅获取日期")
    result = registry.execute_skill("get_current_date", format="date")
    
    if result['success']:
        data = result['data']
        print(f"✅ 执行成功")
        print(f"   格式化: {data.get('formatted')}")
        print(f"   ISO 格式: {data.get('iso_format')}")
    else:
        print(f"❌ 执行失败: {result.get('error')}")
    
    # 测试 3: 仅获取时间
    print("\n测试 3: 仅获取时间")
    result = registry.execute_skill("get_current_date", format="time")
    
    if result['success']:
        data = result['data']
        print(f"✅ 执行成功")
        print(f"   格式化: {data.get('formatted')}")
    else:
        print(f"❌ 执行失败: {result.get('error')}")
    
    # 测试 4: 获取时间戳
    print("\n测试 4: 获取时间戳")
    result = registry.execute_skill("get_current_date", format="timestamp")
    
    if result['success']:
        data = result['data']
        print(f"✅ 执行成功")
        print(f"   时间戳(秒): {data.get('timestamp')}")
        print(f"   时间戳(毫秒): {data.get('timestamp_ms')}")
    else:
        print(f"❌ 执行失败: {result.get('error')}")


def test_function_definitions(registry):
    """测试函数定义生成"""
    print_separator("测试 OpenAI Function Definitions")
    
    definitions = registry.get_all_function_definitions()
    
    print(f"✅ 生成了 {len(definitions)} 个函数定义")
    
    for i, func_def in enumerate(definitions, 1):
        print(f"\n函数 {i}:")
        print(f"   名称: {func_def.get('name')}")
        print(f"   描述: {func_def.get('description')[:50]}...")
        print(f"   参数类型: {func_def.get('parameters', {}).get('type')}")
        props = func_def.get('parameters', {}).get('properties', {})
        if props:
            print(f"   参数列表: {', '.join(props.keys())}")


def test_error_handling(registry):
    """测试错误处理"""
    print_separator("测试错误处理")
    
    # 测试不存在的技能
    print("\n测试 1: 调用不存在的技能")
    result = registry.execute_skill("non_existent_skill")
    
    if not result['success']:
        print(f"✅ 正确处理: {result.get('error')}")
    else:
        print(f"❌ 应该返回错误")
    
    # 测试无效参数
    print("\n测试 2: 传递无效参数")
    result = registry.execute_skill("get_current_date", format="invalid_format")
    
    if result['success']:
        print(f"✅ 技能处理了无效参数")
    else:
        print(f"⚠️  技能拒绝了无效参数: {result.get('error')}")


def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("🧪 Skills 系统测试")
    print("="*50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 初始化注册表
        registry = test_skill_registry()
        
        # 测试日期技能
        test_date_skill(registry)
        
        # 测试函数定义
        test_function_definitions(registry)
        
        # 测试错误处理
        test_error_handling(registry)
        
        print_separator()
        print("\n✅ 所有测试完成！")
        print("\n💡 提示: 启动服务后，可以通过以下方式测试：")
        print("   1. 访问 http://localhost:5000/api/skills 查看技能列表")
        print("   2. 在对话中询问：今天几号？现在几点？")
        print("   3. 使用 POST /api/skills/get_current_date 手动调用")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
