"""Test case generation skill"""

from typing import Dict, Any, List, Optional
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class TestCaseSkill(BaseSkill):
    
    name = "gen_testcase"
    description = "根据需求生成测试用例"
    triggers = ["生成测试用例", "写测试用例", "生成用例"]
    
    parameters = {
        "pages": {"required": False, "description": "页面列表"},
        "types": {"required": False, "description": "测试类型"},
        "priority": {"required": False, "description": "优先级"}
    }
    
    def execute(
        self,
        params: Dict[str, Any],
        session: SessionState
    ) -> SkillResult:
        pages = params.get("pages")
        filter_keyword = params.get("filter")
        
        if not pages:
            pages = session.analyzed_pages
            if not pages:
                return SkillResult(
                    success=False,
                    error="没有可用的页面数据",
                    suggestion="请先分析一个原型链接"
                )
        
        # 标准化页面格式为名称列表
        page_names = []
        for p in pages:
            if isinstance(p, dict):
                page_names.append(p.get("name", ""))
            elif isinstance(p, str):
                page_names.append(p)
        
        # 筛选
        if filter_keyword:
            page_names = [name for name in page_names if filter_keyword in name]
            if not page_names:
                return SkillResult(
                    success=False,
                    error=f"没有找到包含「{filter_keyword}」的页面"
                )
        
        test_types = params.get("types", ["positive", "negative"])
        priority = params.get("priority", "P1")
        
        # 生成测试用例
        test_cases = self._generate(page_names, test_types, priority, session)
        
        # 更新会话
        session.test_cases = test_cases
        
        # 统计
        type_counts = {}
        for tc in test_cases:
            t = tc.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        type_summary = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
        
        return SkillResult(
            success=True,
            data={
                "test_cases": test_cases,
                "total": len(test_cases),
                "pages_count": len(page_names),
                "type_summary": type_summary
            },
            message=f"已生成 {len(test_cases)} 条测试用例（{type_summary}）"
        )
    
    def _generate(
        self,
        page_names: List[str],
        test_types: List[str],
        priority: str,
        session: SessionState
    ) -> List[Dict]:
        if self.llm:
            return self._llm_generate(page_names, test_types, priority, session)
        return self._template_generate(page_names, test_types, priority)
    
    def _template_generate(
        self,
        page_names: List[str],
        test_types: List[str],
        priority: str
    ) -> List[Dict]:
        from ..services.generator.test_case_generator import TestCaseGenerator
        
        generator = TestCaseGenerator()
        return generator.generate(page_names, test_types, priority)
    
    def _llm_generate(
        self,
        page_names: List[str],
        test_types: List[str],
        priority: str,
        session: SessionState
    ) -> List[Dict]:
        import json
        import re
        
        context = ""
        if self.knowledge_base:
            query = " ".join(page_names[:5])
            try:
                context = self.knowledge_base.get_context(query, top_k=3)
            except:
                pass
        
        prompt = f"""根据以下页面生成测试用例：

页面列表：{json.dumps(page_names, ensure_ascii=False, indent=2)}

测试类型：{', '.join(test_types)}
优先级：{priority}

{f'参考知识库内容：{context}' if context else ''}

请生成测试用例，以 JSON 数组格式输出：
[
  {{
    "id": "TC_模块_001",
    "title": "测试用例标题",
    "preconditions": "前置条件",
    "steps": "操作步骤",
    "expected_results": "预期结果",
    "priority": "{priority}",
    "type": "positive/negative/boundary"
  }}
]

只返回 JSON 数组。
"""
        
        try:
            from ..llm import Message, MessageRole
            response = self.llm.chat([
                Message(role=MessageRole.USER, content=prompt)
            ])
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return self._template_generate(page_names, test_types, priority)
