"""
Configuration Tests
测试配置管理
"""

import pytest
from pathlib import Path
from app.core.config import Settings


class TestSettings:
    """测试应用配置"""
    
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        
        assert settings.APP_NAME == "智测AI (Testify AI)"
        assert settings.APP_VERSION == "3.1.0-dev"
        assert settings.DEBUG is False
        assert settings.PORT == 8000
    
    def test_log_settings(self):
        """测试日志配置"""
        settings = Settings()
        
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_DIR == "./logs"
    
    def test_storage_settings(self):
        """测试存储配置"""
        settings = Settings()
        
        assert settings.UPLOAD_DIR == "./uploads"
        assert settings.EXPORT_DIR == "./exports"
        assert settings.DATA_DIR == "./data"
    
    def test_crawler_settings(self):
        """测试爬虫配置"""
        settings = Settings()
        
        assert settings.CRAWLER_TIMEOUT == 60
        assert settings.CRAWLER_HEADLESS is True
        assert settings.PAGE_LOAD_TIMEOUT_MS == 3000
    
    def test_llm_settings(self):
        """测试LLM配置"""
        settings = Settings()
        
        assert settings.LLM_API_TYPE == "glm"
        assert settings.LLM_MODEL_NAME == "glm-4"
        assert settings.LLM_TEMPERATURE == 0.7
        assert settings.LLM_MAX_TOKENS == 4096
    
    def test_get_storage_path(self, tmp_path):
        """测试获取存储路径"""
        settings = Settings(DATA_DIR=str(tmp_path))
        
        path = settings.get_storage_path("data")
        
        assert path.exists()
        assert isinstance(path, Path)
    
    def test_cors_origins(self):
        """测试CORS配置"""
        settings = Settings()
        
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS