# DemandTest Platform v3.1 重构方案

## 🎯 重构目标

| 痛点 | 当前问题 | 重构方案 |
|------|----------|----------|
| 提取层脆弱 | 依赖DOM/OCR，Canvas无法解析 | 协议级拦截（Network Interception） |
| 逻辑层混乱 | Agent意图与执行耦合 | 原子化Skill + 编排器 |
| 扩展性不足 | 新增平台需改核心代码 | 平台插件化（策略模式） |

---

## 📐 新架构设计

```
app/
├── core/                      # 核心层
│   ├── engine.py             # Agent编排引擎（状态机）
│   ├── interceptor.py        # 网络拦截器基类
│   ├── schema.py             # 全局Pydantic模型
│   └── registry.py           # 平台注册表
│
├── platforms/                 # 平台插件（策略模式）
│   ├── __init__.py
│   ├── base.py               # 平台适配器抽象基类
│   ├── modao/                # 墨刀插件
│   │   ├── __init__.py
│   │   ├── adapter.py        # 适配器实现
│   │   ├── interceptor.py    # 网络拦截逻辑
│   │   └── parser.py         # JSON解析器
│   ├── lanhu/                # 蓝湖插件
│   │   └── ...
│   └── figma/                # Figma插件
│       └── ...
│
├── skills/                    # 原子化技能
│   ├── __init__.py
│   ├── base.py               # 技能基类
│   ├── extractor.py          # 数据提取技能
│   ├── transformer.py        # 数据转换技能
│   ├── generator.py          # 用例生成技能
│   └── exporter.py           # 导出技能
│
├── llm/                       # LLM层（保持）
│   └── ...
│
├── api/                       # API层
│   ├── __init__.py
│   ├── analyze.py            # 分析接口
│   ├── generate.py           # 生成接口
│   └── export.py             # 导出接口
│
├── models/                    # 数据模型
│   └── ...
│
└── main.py                    # 入口
```

---

## 🔧 核心代码实现

### 1. Schema层 - 标准化数据模型

```python
# app/core/schema.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ElementType(str, Enum):
    """元素类型"""
    BUTTON = "button"
    INPUT = "input"
    TEXT = "text"
    IMAGE = "image"
    LINK = "link"
    CONTAINER = "container"
    UNKNOWN = "unknown"


class UIElement(BaseModel):
    """UI元素"""
    id: str
    type: ElementType
    name: Optional[str] = None
    text: Optional[str] = None
    selector: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    children: List["UIElement"] = Field(default_factory=list)


class RequirementNode(BaseModel):
    """需求节点 - 标准格式，解耦平台差异"""
    id: str
    name: str
    page_id: str
    url: Optional[str] = None
    description: Optional[str] = None
    elements: List[UIElement] = Field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None  # 保留原始数据
    screenshot_path: Optional[str] = None


class TestCaseStep(BaseModel):
    """测试步骤"""
    order: int
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    expected: Optional[str] = None


class TestCase(BaseModel):
    """测试用例"""
    id: str
    title: str = Field(..., description="用例标题")
    module: Optional[str] = None
    priority: str = Field(default="P2", description="P0/P1/P2/P3")
    type: str = Field(default="positive", description="positive/negative/boundary/exception")
    preconditions: List[str] = Field(default_factory=list, description="前置条件")
    steps: List[TestCaseStep] = Field(default_factory=list, description="操作步骤")
    expected_result: str = Field(..., description="预期结果")
    tags: List[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """提取结果"""
    platform: str
    url: str
    pages: List[RequirementNode]
    total_elements: int = 0
    success: bool = True
    error: Optional[str] = None


class GenerationResult(BaseModel):
    """生成结果"""
    page_name: str
    test_cases: List[TestCase]
    total: int
    success: bool = True
    error: Optional[str] = None
```

---

### 2. 拦截器基类 - 协议级提取

```python
# app/core/interceptor.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import asyncio
import json

from playwright.async_api import async_playwright, Page, Response

from .schema import RequirementNode, ExtractionResult


@dataclass
class InterceptedData:
    """拦截到的数据"""
    url: str
    method: str
    status: int
    headers: Dict[str, str]
    body: Any


class BaseInterceptor(ABC):
    """
    网络拦截器基类
    通过拦截网络请求获取原始JSON数据，绕过Canvas/DOM限制
    """

    def __init__(self):
        self.intercepted_data: List[InterceptedData] = []
        self.target_patterns: List[str] = []

    @abstractmethod
    def get_target_patterns(self) -> List[str]:
        """
        返回需要拦截的URL模式列表
        例如: ["api/pages", "api/workspace", "document.js"]
        """
        pass

    @abstractmethod
    async def parse_response(self, data: InterceptedData) -> List[RequirementNode]:
        """
        解析拦截到的响应数据
        返回标准化的需求节点列表
        """
        pass

    def should_intercept(self, url: str) -> bool:
        """判断是否需要拦截此URL"""
        return any(pattern in url for pattern in self.target_patterns)

    async def handle_response(self, response: Response):
        """响应处理器"""
        url = response.url
        method = response.request.method

        if not self.should_intercept(url):
            return

        try:
            # 尝试解析为JSON
            body = await response.json()
        except:
            try:
                body = await response.text()
            except:
                body = None

        self.intercepted_data.append(InterceptedData(
            url=url,
            method=method,
            status=response.status,
            headers=dict(response.headers),
            body=body
        ))

        print(f"[拦截] {method} {url} -> {response.status}")

    async def extract(self, url: str) -> ExtractionResult:
        """
        执行提取流程
        1. 启动浏览器
        2. 注册拦截器
        3. 导航到页面
        4. 解析数据
        """
        self.target_patterns = self.get_target_patterns()
        self.intercepted_data = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            # 注册响应拦截器
            page.on("response", self.handle_response)

            try:
                # 导航到页面
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)

                # 触发额外的数据加载（滚动、点击等）
                await self.trigger_data_loading(page)

            except Exception as e:
                return ExtractionResult(
                    platform=self.platform_name,
                    url=url,
                    pages=[],
                    success=False,
                    error=str(e)
                )
            finally:
                await browser.close()

        # 解析拦截到的数据
        all_nodes = []
        for data in self.intercepted_data:
            if data.body:
                nodes = await self.parse_response(data)
                all_nodes.extend(nodes)

        return ExtractionResult(
            platform=self.platform_name,
            url=url,
            pages=all_nodes,
            total_elements=sum(len(p.elements) for p in all_nodes)
        )

    async def trigger_data_loading(self, page: Page):
        """
        触发页面数据加载
        子类可覆盖以实现特定交互
        """
        # 默认：滚动页面
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(500)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass
```

---

### 3. 平台适配器基类

```python
# app/platforms/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

from app.core.interceptor import BaseInterceptor
from app.core.schema import RequirementNode, ExtractionResult


class PlatformAdapter(ABC):
    """
    平台适配器基类
    每个平台实现自己的适配器，包含拦截器和解析器
    """

    def __init__(self):
        self.interceptor: Optional[BaseInterceptor] = None

    @abstractmethod
    def get_interceptor(self) -> BaseInterceptor:
        """获取平台对应的拦截器"""
        pass

    @abstractmethod
    def match(self, url: str) -> bool:
        """判断URL是否匹配此平台"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """平台显示名称"""
        pass

    async def extract(self, url: str) -> ExtractionResult:
        """执行提取"""
        if not self.interceptor:
            self.interceptor = self.get_interceptor()
        return await self.interceptor.extract(url)
```

---

### 4. 墨刀平台实现

```python
# app/platforms/modao/adapter.py
import re
from typing import List

from app.platforms.base import PlatformAdapter
from app.core.interceptor import BaseInterceptor, InterceptedData
from app.core.schema import RequirementNode, UIElement, ElementType


class ModaoInterceptor(BaseInterceptor):
    """墨刀网络拦截器"""

    def get_target_patterns(self) -> List[str]:
        """墨刀的关键API模式"""
        return [
            "document.js",      # 页面结构数据
            "/api/pages",       # 页面列表
            "/api/workspace",   # 工作空间
            "sitemap",          # 站点地图
        ]

    async def parse_response(self, data: InterceptedData) -> List[RequirementNode]:
        """解析墨刀数据"""
        nodes = []

        if "document.js" in data.url:
            # 解析document.js中的页面结构
            nodes = await self._parse_document_js(data.body)
        elif "/api/pages" in data.url:
            # 解析API返回的JSON
            nodes = await self._parse_pages_api(data.body)

        return nodes

    async def _parse_document_js(self, content: str) -> List[RequirementNode]:
        """解析document.js文件"""
        if not isinstance(content, str):
            return []

        nodes = []

        # 提取变量定义
        variables = {}
        for match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', content):
            variables[match.group(1)] = match.group(2)

        # 解析sitemap树结构
        # 格式: _(s, id_var, u, name_var, ...)
        # 这里需要根据实际格式解析

        return nodes

    async def _parse_pages_api(self, data: dict) -> List[RequirementNode]:
        """解析页面API返回"""
        if not isinstance(data, dict):
            return []

        nodes = []
        pages = data.get("pages", [])

        for page in pages:
            node = RequirementNode(
                id=page.get("id", ""),
                name=page.get("name", ""),
                page_id=page.get("pageId", ""),
                url=page.get("url"),
                description=page.get("description"),
            )
            nodes.append(node)

        return nodes

    @property
    def platform_name(self) -> str:
        return "modao"


class ModaoAdapter(PlatformAdapter):
    """墨刀平台适配器"""

    def get_interceptor(self) -> BaseInterceptor:
        return ModaoInterceptor()

    def match(self, url: str) -> bool:
        return "modao.cc" in url or "modao.com" in url

    @property
    def name(self) -> str:
        return "modao"

    @property
    def display_name(self) -> str:
        return "墨刀"
```

---

### 5. 平台注册表

```python
# app/core/registry.py
from typing import Dict, List, Optional, Type

from app.platforms.base import PlatformAdapter


class PlatformRegistry:
    """
    平台注册表
    支持动态注册新平台，无需修改核心代码
    """

    _adapters: Dict[str, Type[PlatformAdapter]] = {}

    @classmethod
    def register(cls, adapter_class: Type[PlatformAdapter]):
        """注册平台适配器"""
        instance = adapter_class()
        cls._adapters[instance.name] = adapter_class
        print(f"[注册] 平台: {instance.display_name} ({instance.name})")

    @classmethod
    def get_adapter(cls, url: str) -> Optional[PlatformAdapter]:
        """根据URL获取适配器"""
        for adapter_class in cls._adapters.values():
            instance = adapter_class()
            if instance.match(url):
                return instance
        return None

    @classmethod
    def list_platforms(cls) -> List[dict]:
        """列出所有支持的平台"""
        platforms = []
        for adapter_class in cls._adapters.values():
            instance = adapter_class()
            platforms.append({
                "name": instance.name,
                "display_name": instance.display_name,
            })
        return platforms


# 自动注册内置平台
def auto_register():
    from app.platforms.modao.adapter import ModaoAdapter
    # from app.platforms.lanhu.adapter import LanhuAdapter
    # from app.platforms.figma.adapter import FigmaAdapter

    PlatformRegistry.register(ModaoAdapter)
    # PlatformRegistry.register(LanhuAdapter)
    # PlatformRegistry.register(FigmaAdapter)


auto_register()
```

---

### 6. 原子化技能

```python
# app/skills/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.core.schema import ExtractionResult, GenerationResult


class SkillResult(BaseModel):
    """技能执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseSkill(ABC):
    """技能基类 - 每个技能只做一件事"""

    def __init__(self, **kwargs):
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass

    @abstractmethod
    async def execute(self, input_data: Any) -> SkillResult:
        """执行技能"""
        pass

    def validate_input(self, input_data: Any) -> Optional[str]:
        """验证输入，返回错误信息或None"""
        return None
```

```python
# app/skills/extractor.py
from typing import List
from app.skills.base import BaseSkill, SkillResult
from app.core.schema import RequirementNode, ExtractionResult
from app.core.registry import PlatformRegistry


class ExtractorSkill(BaseSkill):
    """
    提取技能
    只负责从URL提取原始数据
    """

    @property
    def name(self) -> str:
        return "extractor"

    async def execute(self, url: str) -> SkillResult:
        # 获取平台适配器
        adapter = PlatformRegistry.get_adapter(url)

        if not adapter:
            return SkillResult(
                success=False,
                error=f"不支持的平台: {url}"
            )

        # 执行提取
        result: ExtractionResult = await adapter.extract(url)

        return SkillResult(
            success=result.success,
            data=result,
            error=result.error,
            metadata={
                "platform": result.platform,
                "pages_count": len(result.pages),
                "elements_count": result.total_elements
            }
        )

    def validate_input(self, url: str) -> Optional[str]:
        if not url:
            return "URL不能为空"
        if not url.startswith("http"):
            return "URL格式错误"
        return None
```

```python
# app/skills/generator.py
from typing import List
from app.skills.base import BaseSkill, SkillResult
from app.core.schema import RequirementNode, TestCase
from app.llm import BaseLLM


class GeneratorSkill(BaseSkill):
    """
    生成技能
    只负责根据需求生成测试用例
    使用结构化输出保证100%可解析
    """

    def __init__(self, llm: BaseLLM, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm

    @property
    def name(self) -> str:
        return "generator"

    async def execute(self, requirement: RequirementNode) -> SkillResult:
        prompt = f"""分析以下需求并生成测试用例：

页面名称: {requirement.name}
页面描述: {requirement.description or '无'}
元素数量: {len(requirement.elements)}

请生成测试用例，覆盖正向、逆向、边界场景。
"""

        # 使用结构化输出（需要LLM支持）
        # 例如使用 instructor 库
        try:
            # response = await self.llm.chat(
            #     prompt=prompt,
            #     response_model=List[TestCase]
            # )
            # 临时模拟
            response = self._mock_generate(requirement)

            return SkillResult(
                success=True,
                data=response,
                metadata={"count": len(response)}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )

    def _mock_generate(self, requirement: RequirementNode) -> List[TestCase]:
        """临时模拟生成"""
        return [
            TestCase(
                id=f"TC_{requirement.id}_001",
                title=f"正向-{requirement.name}功能验证",
                expected_result="功能正常工作"
            )
        ]
```

---

### 7. 编排引擎

```python
# app/core/engine.py
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from app.skills.base import BaseSkill, SkillResult
from app.skills.extractor import ExtractorSkill
from app.skills.generator import GeneratorSkill
from app.skills.exporter import ExporterSkill
from app.core.schema import ExtractionResult, TestCase
from app.llm import BaseLLM


class WorkflowState(str, Enum):
    """工作流状态"""
    IDLE = "idle"
    EXTRACTING = "extracting"
    TRANSFORMING = "transforming"
    GENERATING = "generating"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowContext:
    """工作流上下文"""
    url: str
    state: WorkflowState = WorkflowState.IDLE
    extraction_result: Optional[ExtractionResult] = None
    test_cases: List[TestCase] = None
    export_path: Optional[str] = None
    error: Optional[str] = None


class Engine:
    """
    编排引擎
    协调各技能执行，管理状态流转
    """

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm
        self.skills: Dict[str, BaseSkill] = {}

        self._register_skills()

    def _register_skills(self):
        """注册技能"""
        self.skills["extractor"] = ExtractorSkill()
        if self.llm:
            self.skills["generator"] = GeneratorSkill(llm=self.llm)
        self.skills["exporter"] = ExporterSkill()

    async def run(self, url: str, pages: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行完整工作流
        """
        ctx = WorkflowContext(url=url)

        try:
            # Step 1: 提取
            ctx.state = WorkflowState.EXTRACTING
            extract_result = await self.skills["extractor"].execute(url)

            if not extract_result.success:
                ctx.state = WorkflowState.FAILED
                ctx.error = extract_result.error
                return self._build_response(ctx)

            ctx.extraction_result = extract_result.data

            # Step 2: 生成（可选，如果有LLM）
            if "generator" in self.skills and ctx.extraction_result.pages:
                ctx.state = WorkflowState.GENERATING

                all_cases = []
                for page in ctx.extraction_result.pages:
                    # 过滤指定页面
                    if pages and page.name not in pages:
                        continue

                    gen_result = await self.skills["generator"].execute(page)
                    if gen_result.success:
                        all_cases.extend(gen_result.data)

                ctx.test_cases = all_cases

            # Step 3: 导出（可选）
            if ctx.test_cases:
                ctx.state = WorkflowState.EXPORTING
                export_result = await self.skills["exporter"].execute(ctx.test_cases)
                if export_result.success:
                    ctx.export_path = export_result.data

            ctx.state = WorkflowState.COMPLETED

        except Exception as e:
            ctx.state = WorkflowState.FAILED
            ctx.error = str(e)

        return self._build_response(ctx)

    def _build_response(self, ctx: WorkflowContext) -> Dict[str, Any]:
        """构建响应"""
        return {
            "state": ctx.state.value,
            "url": ctx.url,
            "extraction": {
                "success": ctx.extraction_result.success if ctx.extraction_result else False,
                "platform": ctx.extraction_result.platform if ctx.extraction_result else None,
                "pages_count": len(ctx.extraction_result.pages) if ctx.extraction_result else 0,
            },
            "test_cases": {
                "count": len(ctx.test_cases) if ctx.test_cases else 0,
                "items": [tc.model_dump() for tc in ctx.test_cases] if ctx.test_cases else []
            },
            "export_path": ctx.export_path,
            "error": ctx.error
        }
```

---

### 8. API层

```python
# app/api/analyze.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, List

from app.core.engine import Engine
from app.core.registry import PlatformRegistry


router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    pages: Optional[List[str]] = None


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None


# 存储任务结果（生产环境应使用Redis）
_tasks: dict = {}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    启动分析任务（异步）
    """
    import uuid
    task_id = str(uuid.uuid4())

    # 检查平台支持
    adapter = PlatformRegistry.get_adapter(str(request.url))
    if not adapter:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的平台。支持的平台: {[p['display_name'] for p in PlatformRegistry.list_platforms()]}"
        )

    # 后台执行
    async def run_task():
        engine = Engine()
        result = await engine.run(str(request.url), request.pages)
        _tasks[task_id] = result

    background_tasks.add_task(run_task)

    return AnalyzeResponse(
        status="processing",
        message=f"任务已启动，平台: {adapter.display_name}",
        task_id=task_id
    )


@router.get("/analyze/{task_id}")
async def get_result(task_id: str):
    """
    获取任务结果
    """
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    return _tasks[task_id]


@router.get("/platforms")
async def list_platforms():
    """
    列出所有支持的平台
    """
    return PlatformRegistry.list_platforms()
```

---

## 📊 重构对比

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| **提取方式** | DOM/OCR | 网络拦截 |
| **可靠性** | 低（Canvas无法解析） | 高（直接获取JSON） |
| **扩展性** | 改核心代码 | 只需新增平台插件 |
| **代码耦合** | 高 | 低（原子化技能） |
| **LLM输出** | 自由文本 | 结构化Pydantic |
| **测试难度** | 困难 | 简单（每个技能独立测试） |

---

## 🚀 实施步骤

### Phase 1: 核心层 (1-2天)
- [x] schema.py - 数据模型
- [x] interceptor.py - 拦截器基类
- [x] registry.py - 平台注册表

### Phase 2: 平台插件 (2-3天)
- [ ] modao适配器完整实现
- [ ] lanhu适配器
- [ ] figma适配器

### Phase 3: 技能层 (1-2天)
- [ ] extractor技能
- [ ] generator技能
- [ ] exporter技能

### Phase 4: 编排层 (1天)
- [ ] engine.py
- [ ] 状态管理

### Phase 5: API层 (1天)
- [ ] analyze接口
- [ ] 任务管理

---

## 📝 后续优化

1. **添加缓存层** - 缓存拦截结果
2. **添加重试机制** - 网络请求失败重试
3. **添加进度推送** - WebSocket实时进度
4. **添加批量处理** - 支持批量URL分析
5. **添加插件热加载** - 动态加载平台插件

---

这个架构解决了你提到的三个核心痛点，且易于扩展。需要我开始实现吗？
