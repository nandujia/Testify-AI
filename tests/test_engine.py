"""
Core Engine Tests
测试编排引擎的核心功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.engine import Engine, WorkflowState, WorkflowContext
from app.core.schema import ExtractionResult, RequirementNode, TestCase


class TestWorkflowState:
    """测试工作流状态"""
    
    def test_state_values(self):
        """测试状态枚举值"""
        assert WorkflowState.IDLE == "idle"
        assert WorkflowState.EXTRACTING == "extracting"
        assert WorkflowState.GENERATING == "generating"
        assert WorkflowState.EXPORTING == "exporting"
        assert WorkflowState.COMPLETED == "completed"
        assert WorkflowState.FAILED == "failed"


class TestWorkflowContext:
    """测试工作流上下文"""
    
    def test_context_creation(self):
        """测试上下文创建"""
        ctx = WorkflowContext(url="https://example.com")
        
        assert ctx.url == "https://example.com"
        assert ctx.state == WorkflowState.IDLE
        assert ctx.platform == ""
        assert ctx.extraction_result is None
        assert ctx.test_cases == []
        assert ctx.error is None
    
    def test_context_with_results(self):
        """测试上下文存储结果"""
        ctx = WorkflowContext(url="https://example.com")
        
        # 模拟存储结果
        ctx.extraction_result = ExtractionResult(
            platform="modao",
            url="https://example.com",
            success=True
        )
        ctx.test_cases = [
            TestCase(id="TC_001", title="测试用例1", expected_result="预期结果")
        ]
        
        assert ctx.extraction_result.success is True
        assert len(ctx.test_cases) == 1


class TestEngine:
    """测试编排引擎"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return Engine(llm=None, use_shadow_learning=False)
    
    def test_engine_creation(self, engine):
        """测试引擎创建"""
        assert engine.llm is None
        assert engine.use_shadow_learning is False
        assert engine.shadow_learning is None
    
    @pytest.mark.asyncio
    async def test_extract_unsupported_platform(self, engine):
        """测试不支持的平台"""
        result = await engine._extract("https://unknown.com/page")
        
        assert result.success is False
        assert "不支持的平台" in result.error or "Unsupported" in result.error
    
    def test_parse_test_cases(self, engine):
        """测试解析测试用例"""
        requirement = RequirementNode(
            id="test_001",
            name="登录功能",
            page_id="login"
        )
        
        cases = engine._parse_test_cases("LLM响应内容", requirement)
        
        assert len(cases) == 2  # 正向和逆向
        assert "登录功能" in cases[0].title
    
    def test_build_response(self, engine):
        """测试构建响应"""
        ctx = WorkflowContext(url="https://example.com")
        ctx.state = WorkflowState.COMPLETED
        ctx.platform = "modao"
        
        response = engine._build_response(ctx)
        
        assert response["state"] == "completed"
        assert response["url"] == "https://example.com"
        assert response["platform"] == "modao"


class TestExtractionResult:
    """测试提取结果"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = ExtractionResult(
            platform="modao",
            url="https://modao.cc/xxx",
            success=True
        )
        
        assert result.success is True
        assert result.platform == "modao"
        assert result.error is None
    
    def test_failure_result(self):
        """测试失败结果"""
        result = ExtractionResult(
            platform="unknown",
            url="https://unknown.com",
            success=False,
            error="不支持的平台"
        )
        
        assert result.success is False
        assert result.error == "不支持的平台"


class TestRequirementNode:
    """测试需求节点"""
    
    def test_node_creation(self):
        """测试节点创建"""
        node = RequirementNode(
            id="page_001",
            name="VIP页面",
            page_id="vip",
            description="VIP会员权益展示"
        )
        
        assert node.id == "page_001"
        assert node.name == "VIP页面"
        assert node.page_id == "vip"
    
    def test_to_prompt_text(self):
        """测试转换为Prompt文本"""
        node = RequirementNode(
            id="page_001",
            name="VIP页面",
            page_id="vip",
            description="展示VIP等级和权益"
        )
        
        text = node.to_prompt_text()
        
        assert "VIP页面" in text
        assert "展示VIP等级和权益" in text


class TestTestCase:
    """测试测试用例"""
    
    def test_case_creation(self):
        """测试用例创建"""
        case = TestCase(
            id="TC_VIP_001",
            title="VIP会员查看等级信息",
            module="VIP",
            expected_result="显示VIP等级和到期时间"
        )
        
        assert case.id == "TC_VIP_001"
        assert case.title == "VIP会员查看等级信息"
        assert case.priority == "P2"  # 默认优先级
