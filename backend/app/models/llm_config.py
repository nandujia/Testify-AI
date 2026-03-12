"""
LLM 配置模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class LLMProtocol(str, Enum):
    """LLM 协议类型"""
    OPENAI_COMPATIBLE = "openai_compatible"
    GLM = "glm"
    QWEN = "qwen"
    ERNIE = "ernie"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMProvider(str, Enum):
    """LLM 提供者"""
    BUILTIN = "builtin"
    CUSTOM = "custom"


class LLMProfile(BaseModel):
    """LLM 配置档案"""
    id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    provider: LLMProvider = Field(default=LLMProvider.CUSTOM, description="提供者类型")
    
    base_url: str = Field(..., description="API 地址")
    api_key: Optional[str] = Field(default="", description="API Key")
    model_name: str = Field(..., description="模型标识")
    
    protocol: LLMProtocol = Field(
        default=LLMProtocol.OPENAI_COMPATIBLE,
        description="协议类型"
    )
    
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1)
    top_p: float = Field(default=1.0, ge=0, le=1)
    
    headers: Optional[dict] = Field(default=None, description="自定义请求头")
    request_template: Optional[str] = Field(default=None, description="自定义请求模板")
    response_parser: Optional[str] = Field(default=None, description="自定义响应解析")
    
    is_default: bool = Field(default=False, description="是否默认")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(default=None, description="描述")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LLMProfilesConfig(BaseModel):
    """LLM 配置档案集合"""
    profiles: List[LLMProfile] = []
    default_profile_id: Optional[str] = None
    
    def get_profile(self, profile_id: str) -> Optional[LLMProfile]:
        for p in self.profiles:
            if p.id == profile_id:
                return p
        return None
    
    def get_default(self) -> Optional[LLMProfile]:
        if self.default_profile_id:
            return self.get_profile(self.default_profile_id)
        for p in self.profiles:
            if p.enabled:
                return p
        return None
    
    def add_profile(self, profile: LLMProfile) -> None:
        self.profiles.append(profile)
    
    def remove_profile(self, profile_id: str) -> bool:
        for i, p in enumerate(self.profiles):
            if p.id == profile_id:
                self.profiles.pop(i)
                return True
        return False
    
    def update_profile(self, profile: LLMProfile) -> bool:
        for i, p in enumerate(self.profiles):
            if p.id == profile.id:
                profile.updated_at = datetime.now()
                self.profiles[i] = profile
                return True
        return False


# ========== 应用配置 ==========

class AppConfig(BaseModel):
    """应用配置"""
    # 导出设置
    export_dir: str = Field(default="./exports", description="导出目录")
    export_format: str = Field(default="xlsx", description="默认导出格式")
    
    # 知识库设置
    kb_enabled: bool = Field(default=True, description="启用知识库")
    kb_storage_dir: str = Field(default="./data/knowledge", description="知识库目录")
    
    # 会话设置
    session_timeout: int = Field(default=3600, description="会话超时时间(秒)")
    max_history: int = Field(default=50, description="最大历史记录数")
    
    # 调试设置
    debug_mode: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")


class UserSettings(BaseModel):
    """用户设置"""
    app_config: AppConfig = Field(default_factory=AppConfig)
    default_llm_profile_id: Optional[str] = None
    theme: str = Field(default="light")
    language: str = Field(default="zh-CN")
