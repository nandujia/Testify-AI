"""
LLM 工厂
"""

from typing import Dict, Type, Optional
from .base import BaseLLM, LLMConfig
from .custom import CustomLLM


class LLMFactory:
    """LLM 工厂类"""
    
    _registry: Dict[str, Type[BaseLLM]] = {}
    _instances: Dict[str, BaseLLM] = {}
    
    @classmethod
    def register(cls, api_type: str, llm_class: Type[BaseLLM]) -> None:
        cls._registry[api_type.lower()] = llm_class
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        api_type = config.api_type.lower()
        
        # 所有内置模型都使用 CustomLLM (OpenAI 兼容)
        if api_type in cls._registry:
            llm_class = cls._registry[api_type]
            return llm_class(config)
        
        # 自定义模型
        return CustomLLM.from_config(config)
    
    @classmethod
    def create_from_profile(cls, profile) -> BaseLLM:
        """从配置档案创建 LLM"""
        from .custom import CustomLLM
        return CustomLLM(profile)
    
    @classmethod
    def get_or_create(cls, config: LLMConfig, cache_key: Optional[str] = None) -> BaseLLM:
        key = cache_key or f"{config.api_type}:{config.model_name}"
        
        if key not in cls._instances:
            cls._instances[key] = cls.create(config)
        
        return cls._instances[key]
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> BaseLLM:
        config = LLMConfig(**config_dict)
        return cls.create(config)
    
    @classmethod
    def list_supported(cls) -> list:
        return ["glm", "gpt", "qwen", "ernie", "openai_compatible", "ollama", "custom"]
    
    @classmethod
    def clear_cache(cls) -> None:
        cls._instances.clear()
