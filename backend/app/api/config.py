"""
配置 API
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from ..models.llm_config import LLMProfile, AppConfig, UserSettings
from ..services.config_service import ConfigService, LLM_PRESET_TEMPLATES

router = APIRouter()

_config_service = ConfigService()


# ========== LLM 配置 ==========

@router.get("/llm/profiles", response_model=List[LLMProfile])
async def list_llm_profiles():
    """列出所有 LLM 配置"""
    return _config_service.list_llm_profiles()


@router.post("/llm/profiles", response_model=LLMProfile)
async def create_llm_profile(profile: LLMProfile):
    """创建 LLM 配置"""
    _config_service.add_llm_profile(profile)
    return profile


@router.put("/llm/profiles/{profile_id}", response_model=LLMProfile)
async def update_llm_profile(profile_id: str, profile: LLMProfile):
    """更新 LLM 配置"""
    if not _config_service.update_llm_profile(profile):
        raise HTTPException(status_code=404, detail="配置不存在")
    return profile


@router.delete("/llm/profiles/{profile_id}")
async def delete_llm_profile(profile_id: str):
    """删除 LLM 配置"""
    if not _config_service.delete_llm_profile(profile_id):
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True}


@router.post("/llm/profiles/{profile_id}/default")
async def set_default_llm_profile(profile_id: str):
    """设置默认 LLM 配置"""
    if not _config_service.set_default_llm_profile(profile_id):
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True}


@router.post("/llm/profiles/{profile_id}/test")
async def test_llm_profile(profile_id: str):
    """测试 LLM 配置"""
    result = _config_service.test_llm_profile(profile_id)
    return result


@router.get("/llm/presets")
async def list_llm_presets():
    """列出预设模板"""
    return LLM_PRESET_TEMPLATES


# ========== 应用配置 ==========

@router.get("/app", response_model=AppConfig)
async def get_app_config():
    """获取应用配置"""
    return _config_service.get_app_config()


@router.put("/app", response_model=AppConfig)
async def update_app_config(config: AppConfig):
    """更新应用配置"""
    _config_service.update_app_config(config)
    return config


# ========== 用户设置 ==========

@router.get("/user", response_model=UserSettings)
async def get_user_settings():
    """获取用户设置"""
    return _config_service.get_user_settings()


@router.put("/user", response_model=UserSettings)
async def update_user_settings(settings: UserSettings):
    """更新用户设置"""
    _config_service.update_user_settings(settings)
    return settings
