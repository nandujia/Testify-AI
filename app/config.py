"""
配置文件
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import BaseModel


class LLMSettings(BaseModel):
    """LLM 配置"""
    api_type: str = "glm"
    model_name: str = "glm-4"
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class KnowledgeSettings(BaseModel):
    """知识库配置"""
    enabled: bool = True
    storage_dir: str = "./data/knowledge"
    embedding_provider: str = "local"
    embedding_model: str = "text-embedding-ada-002"
    embedding_api_key: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50


class LearningSettings(BaseModel):
    """学习配置"""
    enabled: bool = True
    storage_dir: str = "./data/learning"
    auto_promote: bool = True  # 自动将重复错误提升为最佳实践


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "DemandTest Platform"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    
    # 爬虫配置
    CRAWLER_TIMEOUT: int = 60
    CRAWLER_HEADLESS: bool = True
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    EXPORT_DIR: str = "./exports"
    DATA_DIR: str = "./data"
    CONFIG_DIR: str = "./data/config"
    SESSION_DIR: str = "./data/sessions"
    
    # OCR 配置
    OCR_API_KEY: str = ""
    OCR_API_URL: str = "https://api.ocr.space/parse/image"
    
    # LLM 配置
    LLM_API_TYPE: str = "glm"
    LLM_MODEL_NAME: str = "glm-4"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: Optional[str] = None
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # 知识库配置
    KB_ENABLED: bool = True
    KB_STORAGE_DIR: str = "./data/knowledge"
    KB_EMBEDDING_PROVIDER: str = "local"
    KB_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    KB_CHUNK_SIZE: int = 500
    
    # 学习配置
    LEARNING_ENABLED: bool = True
    LEARNING_STORAGE_DIR: str = "./data/learning"
    
    # 会话配置
    SESSION_TIMEOUT: int = 3600
    SESSION_MAX_HISTORY: int = 50
    
    def get_llm_config(self) -> LLMSettings:
        return LLMSettings(
            api_type=self.LLM_API_TYPE,
            model_name=self.LLM_MODEL_NAME,
            api_key=self.LLM_API_KEY,
            base_url=self.LLM_BASE_URL,
            temperature=self.LLM_TEMPERATURE,
            max_tokens=self.LLM_MAX_TOKENS
        )
    
    def get_knowledge_config(self) -> KnowledgeSettings:
        return KnowledgeSettings(
            enabled=self.KB_ENABLED,
            storage_dir=self.KB_STORAGE_DIR,
            embedding_provider=self.KB_EMBEDDING_PROVIDER,
            embedding_model=self.KB_EMBEDDING_MODEL,
            chunk_size=self.KB_CHUNK_SIZE
        )
    
    def get_learning_config(self) -> LearningSettings:
        return LearningSettings(
            enabled=self.LEARNING_ENABLED,
            storage_dir=self.LEARNING_STORAGE_DIR
        )
    
    class Config:
        env_file = ".env"


settings = Settings()
