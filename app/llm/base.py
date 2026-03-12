"""
LLM 抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """消息模型"""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


class LLMConfig(BaseModel):
    """LLM 配置"""
    model_name: str
    api_type: str
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    
    class Config:
        extra = "allow"


class BaseLLM(ABC):
    """LLM 抽象基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        pass
    
    @abstractmethod
    def chat_with_context(
        self,
        messages: List[Message],
        context: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        pass
    
    @abstractmethod
    async def achat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        pass
    
    def build_messages(
        self,
        system_prompt: Optional[str] = None,
        user_message: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> List[Message]:
        messages = []
        
        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        
        if history:
            for msg in history:
                messages.append(Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                ))
        
        if user_message:
            messages.append(Message(role=MessageRole.USER, content=user_message))
        
        return messages
