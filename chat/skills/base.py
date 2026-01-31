"""
基础技能类和技能注册表
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import os


class BaseSkill(ABC):
    """技能基类
    
    每个技能应该：
    1. 继承此类
    2. 实现所有抽象方法
    3. 放在独立的文件夹中，文件夹名即为技能标识
    4. 包含 SKILL.md 文档说明
    """
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters = self.get_parameters()
        self.skill_dir = None  # 技能所在目录，由注册表设置
        self.skill_md = None   # SKILL.md 内容，由注册表加载
    
    @abstractmethod
    def get_name(self) -> str:
        """返回技能名称（函数名）"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """返回技能描述（简短说明）"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """返回技能参数定义（JSON Schema 格式）"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            **kwargs: 技能参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    def to_function_definition(self) -> Dict[str, Any]:
        """转换为 OpenAI Function Calling 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def get_skill_readme(self) -> Optional[str]:
        """获取技能的 SKILL.md 内容"""
        if self.skill_md:
            return self.skill_md
        
        if self.skill_dir:
            md_path = os.path.join(self.skill_dir, 'SKILL.md')
            if os.path.isfile(md_path):
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        self.skill_md = f.read()
                        return self.skill_md
                except Exception as e:
                    return f"读取 SKILL.md 失败: {str(e)}"
        
        return None


class SkillRegistry:
    """技能注册表
    
    管理所有已注册的技能，提供查询、执行等功能。
    """
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_dirs: Dict[str, str] = {}  # {skill_name: skill_directory}
    
    def register(self, skill: BaseSkill, skill_dir: str = None) -> None:
        """
        注册一个技能
        
        Args:
            skill: 技能实例
            skill_dir: 技能所在目录（可选）
        """
        self._skills[skill.name] = skill
        
        # 设置技能目录
        if skill_dir:
            skill.skill_dir = skill_dir
            self._skill_dirs[skill.name] = skill_dir
        
        # 尝试加载 SKILL.md
        skill.get_skill_readme()
        
        print(f"   ✅ {skill.name}")
    
    def unregister(self, skill_name: str) -> None:
        """注销一个技能"""
        if skill_name in self._skills:
            del self._skills[skill_name]
            print(f"🗑️  技能已注销: {skill_name}")
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """获取指定技能实例"""
        return self._skills.get(skill_name)
    
    def get_skill_dir(self, skill_name: str) -> Optional[str]:
        """获取指定技能的目录路径"""
        return self._skill_dirs.get(skill_name)
    
    def get_skill_readme(self, skill_name: str) -> Optional[str]:
        """获取指定技能的 SKILL.md 内容"""
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get_skill_readme()
        return None
    
    def list_skills(self) -> List[str]:
        """列出所有已注册技能"""
        return list(self._skills.keys())
    
    def get_all_function_definitions(self) -> List[Dict[str, Any]]:
        """获取所有技能的函数定义（用于 OpenAI API）"""
        return [skill.to_function_definition() for skill in self._skills.values()]
    
    def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定技能
        
        Args:
            skill_name: 技能名称
            **kwargs: 技能参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return {
                "success": False,
                "error": f"技能 '{skill_name}' 不存在"
            }
        
        try:
            result = skill.execute(**kwargs)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def __len__(self) -> int:
        """返回已注册技能数量"""
        return len(self._skills)
    
    def __repr__(self) -> str:
        return f"SkillRegistry(skills={len(self._skills)})"
