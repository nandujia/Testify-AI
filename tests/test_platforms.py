"""
Platform Adapters Tests
测试平台适配器功能
"""

import pytest
from app.platforms.base import BasePlatformAdapter, PlatformInfo
from app.platforms.registry import PlatformRegistry
from app.platforms.modao.adapter import ModaoAdapter


class TestPlatformInfo:
    """测试平台信息"""
    
    def test_modao_info(self):
        """测试墨刀平台信息"""
        adapter = ModaoAdapter()
        info = adapter.info
        
        assert info.name == "modao"
        assert info.display_name == "墨刀"
        assert info.display_name_en == "Modao"
        assert "modao.cc" in info.url_patterns


class TestModaoAdapter:
    """测试墨刀适配器"""
    
    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return ModaoAdapter()
    
    def test_match_modao_url(self, adapter):
        """测试匹配墨刀URL"""
        assert adapter.match("https://modao.cc/xxx") is True
        assert adapter.match("https://modao.com/xxx") is True
        assert adapter.match("https://figma.com/xxx") is False
    
    def test_get_sniff_patterns(self, adapter):
        """测试获取嗅探模式"""
        patterns = adapter.get_sniff_patterns()
        
        assert "document_js" in patterns
        assert "api" in patterns
        assert "sitemap" in patterns


class TestPlatformRegistry:
    """测试平台注册表"""
    
    def setup_method(self):
        """每个测试前清理注册表"""
        PlatformRegistry._platforms.clear()
        PlatformRegistry._initialized = False
    
    def test_register_platform(self):
        """测试注册平台"""
        PlatformRegistry.register(ModaoAdapter)
        
        assert "modao" in PlatformRegistry._platforms
    
    def test_get_adapter_by_url(self):
        """测试根据URL获取适配器"""
        PlatformRegistry.register(ModaoAdapter)
        
        adapter = PlatformRegistry.get_adapter("https://modao.cc/xxx")
        
        assert adapter is not None
        assert adapter.info.name == "modao"
    
    def test_get_adapter_by_name(self):
        """测试根据名称获取适配器"""
        PlatformRegistry.register(ModaoAdapter)
        
        adapter = PlatformRegistry.get_adapter_by_name("modao")
        
        assert adapter is not None
        assert isinstance(adapter, ModaoAdapter)
    
    def test_list_platforms(self):
        """测试列出所有平台"""
        PlatformRegistry.register(ModaoAdapter)
        
        platforms = PlatformRegistry.list_platforms()
        
        assert len(platforms) == 1
        assert platforms[0]["name"] == "modao"
    
    def test_is_supported(self):
        """测试检查URL是否支持"""
        PlatformRegistry.register(ModaoAdapter)
        
        assert PlatformRegistry.is_supported("https://modao.cc/xxx") is True
        assert PlatformRegistry.is_supported("https://figma.com/xxx") is False
    
    def test_unregister_platform(self):
        """测试注销平台"""
        PlatformRegistry.register(ModaoAdapter)
        assert "modao" in PlatformRegistry._platforms
        
        result = PlatformRegistry.unregister("modao")
        
        assert result is True
        assert "modao" not in PlatformRegistry._platforms
    
    def test_unregister_nonexistent(self):
        """测试注销不存在的平台"""
        result = PlatformRegistry.unregister("nonexistent")
        
        assert result is False
