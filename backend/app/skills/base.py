"""Skill base class"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from ..core.session import SessionState


class SkillResult(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    message: str = ""
    error: Optional[str] = None
    suggestion: Optional[str] = None


class BaseSkill(ABC):
    
    name: str = ""
    description: str = ""
    triggers: List[str] = []
    parameters: Dict[str, Any] = {}
    
    def __init__(self, llm=None, knowledge_base=None):
        self.llm = llm
        self.knowledge_base = knowledge_base
    
    @abstractmethod
    def execute(self, params: Dict[str, Any], session: SessionState) -> SkillResult:
        pass
    
    def can_handle(self, intent: str, params: Dict[str, Any]) -> bool:
        return intent == self.name
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        missing = []
        for param_name, param_info in self.parameters.items():
            if param_info.get("required", False) and param_name not in params:
                missing.append(param_name)
        return missing
    
    def ask_clarification(self, missing_params: List[str]) -> str:
        param_names = {
            "url": "原型链接",
            "pages": "页面名称",
            "format": "导出格式",
            "content": "文档内容"
        }
        names = [param_names.get(p, p) for p in missing_params]
        return f"请提供以下信息：{', '.join(names)}"
