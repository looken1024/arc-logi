"""
Skills 模块 - AI 对话平台的技能系统

技能系统允许 AI 调用预定义的功能来增强对话能力。

每个技能都是一个独立的文件夹，包含：
- SKILL.md: 技能文档（功能说明、参数、示例等）
- skill.py: 技能实现代码
- 其他资源文件（可选）

技能会被自动发现和加载。
"""

import os
import sys
import importlib.util
from pathlib import Path
from .base import BaseSkill, SkillRegistry


def discover_skills(skills_dir: str = None) -> dict:
    """
    自动发现所有技能
    
    扫描 skills 目录下的所有子文件夹，查找包含 SKILL.md 的文件夹。
    
    Args:
        skills_dir: skills 目录路径，默认为当前模块所在目录
        
    Returns:
        dict: {skill_name: skill_dir_path} 映射
    """
    if skills_dir is None:
        skills_dir = os.path.dirname(os.path.abspath(__file__))
    
    discovered_skills = {}
    
    # 遍历 skills 目录
    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        
        # 只处理文件夹
        if not os.path.isdir(item_path):
            continue
        
        # 跳过特殊目录
        if item.startswith('_') or item.startswith('.'):
            continue
        
        # 检查是否包含 SKILL.md
        skill_md = os.path.join(item_path, 'SKILL.md')
        if os.path.isfile(skill_md):
            discovered_skills[item] = item_path
    
    return discovered_skills


def load_skill(skill_name: str, skill_path: str) -> BaseSkill:
    """
    动态加载一个技能
    
    Args:
        skill_name: 技能名称（文件夹名）
        skill_path: 技能目录的完整路径
        
    Returns:
        BaseSkill: 技能实例
    """
    skill_file = os.path.join(skill_path, 'scripts', 'skill.py')
    
    # 如果存在 scripts/skill.py，按原有方式加载
    if os.path.isfile(skill_file):
        return load_skill_from_file(skill_name, skill_file)
    
    # 否则，创建基于 SKILL.md 的简单技能
    skill_md_path = os.path.join(skill_path, 'SKILL.md')
    return load_skill_from_md(skill_name, skill_path, skill_md_path)


def load_skill_from_file(skill_name: str, skill_path: str) -> BaseSkill:
    """从 scripts/skill.py 加载技能"""
    try:
        # 确保项目根目录在路径中
        skill_dir = os.path.dirname(skill_path)  # scripts 目录
        parent_dir = os.path.dirname(skill_dir)  # get_current_date 目录
        skills_dir = os.path.dirname(parent_dir)  # skills 目录
        project_root = os.path.dirname(skills_dir)  # 项目根目录
        
        # 添加项目根目录到路径（skills 包所在位置）
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # 使用 importlib 动态加载模块
        spec = importlib.util.spec_from_file_location(f"skills.{skill_name}", skill_path)
        if spec is None:
            raise ImportError(f"无法从路径 {skill_path} 创建模块规范")
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"skills.{skill_name}"] = module
        spec.loader.exec_module(module)
        
        # 查找 BaseSkill 的子类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseSkill) and 
                attr is not BaseSkill):
                return attr()
        
        raise ValueError(f"在 {skill_path} 中未找到 BaseSkill 的子类")
        
    except Exception as e:
        raise ImportError(f"加载技能 '{skill_name}' 失败: {str(e)}")


def load_skill_from_md(skill_name: str, skill_path: str, skill_md_path: str) -> BaseSkill:
    """从 SKILL.md 创建简单技能（无需 scripts/skill.py）"""
    from skills.base import BaseSkill
    
    description = skill_name.replace('-', ' ').replace('_', ' ').title()
    
    # 读取 SKILL.md 内容
    skill_md = ""
    if os.path.isfile(skill_md_path):
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            skill_md = f.read()
    
    class SimpleSkill(BaseSkill):
        def get_name(self):
            return skill_name
        
        def get_description(self):
            return description
        
        def get_parameters(self):
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        def execute(self, **kwargs):
            return {
                "success": True,
                "message": f"Skill '{skill_name}' 已执行（基于 SKILL.md）",
                "skill_md": skill_md
            }
    
    return SimpleSkill()


def register_all_skills() -> SkillRegistry:
    """
    自动发现并注册所有技能
    
    Returns:
        SkillRegistry: 包含所有已注册技能的注册表
    """
    registry = SkillRegistry()
    
    # 发现所有技能
    discovered = discover_skills()
    
    print(f"\n🔍 发现 {len(discovered)} 个技能:")
    for skill_name, skill_path in discovered.items():
        print(f"   📁 {skill_name}")
    
    print(f"\n📥 开始加载技能...")
    
    # 加载并注册每个技能
    for skill_name, skill_path in discovered.items():
        try:
            skill_instance = load_skill(skill_name, skill_path)
            skill_dir = os.path.dirname(skill_path)
            registry.register(skill_instance, skill_dir)
        except Exception as e:
            print(f"   ❌ {skill_name}: {str(e)}")
    
    print(f"\n✅ 技能加载完成！共注册 {len(registry)} 个技能\n")
    
    return registry


__all__ = ['BaseSkill', 'SkillRegistry', 'register_all_skills', 'discover_skills', 'load_skill']
