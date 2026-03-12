"""
Pytest Configuration
测试配置和fixtures
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_url():
    """示例URL"""
    return "https://modao.cc/axbox/share/abc123"


@pytest.fixture
def sample_requirement():
    """示例需求节点"""
    from app.core.schema import RequirementNode
    return RequirementNode(
        id="test_001",
        name="登录页面",
        page_id="login",
        description="用户登录功能"
    )


@pytest.fixture
def sample_test_case():
    """示例测试用例"""
    from app.core.schema import TestCase
    return TestCase(
        id="TC_001",
        title="用户登录成功",
        module="登录",
        expected_result="登录成功，跳转到首页"
    )