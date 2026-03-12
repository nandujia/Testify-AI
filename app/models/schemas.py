"""
数据模型
"""

from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class PlatformEnum(str, Enum):
    MODAO = "modao"
    LANHU = "lanhu"
    AXURE = "axure"
    MOKC = "mokc"
    FIGMA = "figma"
    JSDESIGN = "jsdesign"


class TestCaseType(str, Enum):
    POSITIVE = "positive"       # 正向测试
    NEGATIVE = "negative"       # 逆向测试
    BOUNDARY = "boundary"       # 边界测试
    EXCEPTION = "exception"     # 异常测试
    SECURITY = "security"       # 安全测试
    PERFORMANCE = "performance" # 性能测试


class PriorityEnum(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# ==================== 请求模型 ====================

class CrawlRequest(BaseModel):
    """爬取请求"""
    url: str


class GenerateRequest(BaseModel):
    """生成测试用例请求"""
    pages: List[str]
    types: Optional[List[TestCaseType]] = [TestCaseType.POSITIVE, TestCaseType.NEGATIVE]
    priority: Optional[PriorityEnum] = PriorityEnum.P1


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = "xlsx"  # xlsx, markdown, json
    test_cases: List[dict]


# ==================== 响应模型 ====================

class PageInfo(BaseModel):
    """页面信息"""
    id: str
    name: str
    status: Optional[str] = None  # 新增/修改


class CrawlResponse(BaseModel):
    """爬取响应"""
    success: bool
    platform: Optional[str] = None
    expected: int = 0
    extracted: int = 0
    match_rate: str = "0%"
    pages: List[PageInfo] = []
    error: Optional[str] = None


class TestCase(BaseModel):
    """测试用例"""
    id: str
    title: str
    preconditions: str
    steps: str
    expected_results: str
    priority: str
    type: str
    remarks: Optional[str] = None


class GenerateResponse(BaseModel):
    """生成响应"""
    success: bool
    total: int
    test_cases: List[TestCase]
    error: Optional[str] = None


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    error: Optional[str] = None
