"""
技能注册表
"""

from typing import Dict, List, Optional, Type
from .base import BaseSkill


class SkillRegistry:
    """技能注册表"""
    
    _skills: Dict[str, Type[BaseSkill]] = {}
    _instances: Dict[str, BaseSkill] = {}
    
    @classmethod
    def register(cls, skill_class: Type[BaseSkill]) -> None:
        """注册技能"""
        cls._skills[skill_class.name] = skill_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseSkill]]:
        """获取技能类"""
        return cls._skills.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有技能"""
        return list(cls._skills.keys())
    
    @classmethod
    def create_instance(
        cls,
        name: str,
        llm=None,
        knowledge_base=None
    ) -> Optional[BaseSkill]:
        """创建技能实例"""
        skill_class = cls.get(name)
        if skill_class:
            return skill_class(llm=llm, knowledge_base=knowledge_base)
        return None
    
    @classmethod
    def get_or_create(
        cls,
        name: str,
        llm=None,
        knowledge_base=None
    ) -> Optional[BaseSkill]:
        """获取或创建技能实例（缓存）"""
        cache_key = name
        if cache_key not in cls._instances:
            instance = cls.create_instance(name, llm, knowledge_base)
            if instance:
                cls._instances[cache_key] = instance
        return cls._instances.get(cache_key)
    
    @classmethod
    def clear_instances(cls) -> None:
        """清空实例缓存"""
        cls._instances.clear()
