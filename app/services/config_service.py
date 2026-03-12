"""
配置存储服务
"""

import json
from pathlib import Path
from typing import Optional, List
from ..models.llm_config import LLMProfile, LLMProfilesConfig, AppConfig, UserSettings


class ConfigService:
    """配置存储服务"""
    
    def __init__(self, config_dir: str = "./data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm_config_file = self.config_dir / "llm_profiles.json"
        self.user_config_file = self.config_dir / "user_settings.json"
        
        self._llm_config = self._load_llm_config()
        self._user_settings = self._load_user_settings()
    
    def _load_llm_config(self) -> LLMProfilesConfig:
        if self.llm_config_file.exists():
            with open(self.llm_config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return LLMProfilesConfig(**data)
        return LLMProfilesConfig()
    
    def _save_llm_config(self) -> None:
        with open(self.llm_config_file, "w", encoding="utf-8") as f:
            json.dump(self._llm_config.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def _load_user_settings(self) -> UserSettings:
        if self.user_config_file.exists():
            with open(self.user_config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return UserSettings(**data)
        return UserSettings()
    
    def _save_user_settings(self) -> None:
        with open(self.user_config_file, "w", encoding="utf-8") as f:
            json.dump(self._user_settings.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    # ========== LLM 配置 ==========
    
    def list_llm_profiles(self) -> List[LLMProfile]:
        return self._llm_config.profiles
    
    def get_llm_profile(self, profile_id: str) -> Optional[LLMProfile]:
        return self._llm_config.get_profile(profile_id)
    
    def get_default_llm_profile(self) -> Optional[LLMProfile]:
        return self._llm_config.get_default()
    
    def add_llm_profile(self, profile: LLMProfile) -> None:
        self._llm_config.add_profile(profile)
        self._save_llm_config()
    
    def update_llm_profile(self, profile: LLMProfile) -> bool:
        result = self._llm_config.update_profile(profile)
        if result:
            self._save_llm_config()
        return result
    
    def delete_llm_profile(self, profile_id: str) -> bool:
        result = self._llm_config.remove_profile(profile_id)
        if result:
            self._save_llm_config()
        return result
    
    def set_default_llm_profile(self, profile_id: str) -> bool:
        profile = self.get_llm_profile(profile_id)
        if not profile:
            return False
        
        for p in self._llm_config.profiles:
            p.is_default = False
        
        profile.is_default = True
        self._llm_config.default_profile_id = profile_id
        self._save_llm_config()
        return True
    
    def test_llm_profile(self, profile_id: str) -> dict:
        from ..llm import LLMFactory, Message, MessageRole
        
        profile = self.get_llm_profile(profile_id)
        if not profile:
            return {"success": False, "error": "配置不存在"}
        
        try:
            llm = LLMFactory.create_from_profile(profile)
            response = llm.chat([
                Message(role=MessageRole.USER, content="Hello, this is a test.")
            ])
            return {
                "success": True,
                "response_preview": response[:100] + "..." if len(response) > 100 else response
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== 用户设置 ==========
    
    def get_app_config(self) -> AppConfig:
        return self._user_settings.app_config
    
    def update_app_config(self, config: AppConfig) -> None:
        self._user_settings.app_config = config
        self._save_user_settings()
    
    def get_user_settings(self) -> UserSettings:
        return self._user_settings
    
    def update_user_settings(self, settings: UserSettings) -> None:
        self._user_settings = settings
        self._save_user_settings()


# 预设模板
LLM_PRESET_TEMPLATES = [
    {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434/v1",
        "model_name": "llama3",
        "protocol": "openai_compatible",
        "description": "Ollama 本地模型服务"
    },
    {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
        "protocol": "openai_compatible",
        "description": "DeepSeek API"
    },
    {
        "name": "Moonshot (月之暗面)",
        "base_url": "https://api.moonshot.cn/v1",
        "model_name": "moonshot-v1-8k",
        "protocol": "openai_compatible",
        "description": "Moonshot API"
    },
    {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model_name": "glm-4",
        "protocol": "glm",
        "description": "智谱 GLM API"
    },
    {
        "name": "本地 vLLM",
        "base_url": "http://localhost:8000/v1",
        "model_name": "model",
        "protocol": "openai_compatible",
        "description": "vLLM 本地模型服务"
    }
]
