"""Test case skill"""

from typing import Dict, Any, List
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class TestCaseSkill(BaseSkill):
    
    name = "gen_testcase"
    description = "根据选择的需求生成测试用例"
    
    parameters = {
        "selection": {"required": False, "description": "选择的页面名称或关键词"},
        "types": {"required": False, "description": "测试类型"},
        "priority": {"required": False, "description": "优先级"}
    }
    
    def execute(self, params: Dict[str, Any], session: SessionState) -> SkillResult:
        # Get analyzed pages
        all_pages = session.analyzed_pages
        
        if not all_pages:
            return SkillResult(
                success=False,
                error="没有可用的页面数据",
                suggestion="请先分析原型链接"
            )
        
        # Get user selection
        selection = params.get("selection", "")
        page_names = [p.get("name", "") for p in all_pages]
        
        # Filter pages by selection
        if selection:
            # Parse selection (comma/、/空格 separated keywords)
            import re
            keywords = re.split(r'[,，、\s]+', selection)
            keywords = [k.strip() for k in keywords if k.strip()]
            
            selected_pages = []
            for name in page_names:
                for keyword in keywords:
                    if keyword.lower() in name.lower():
                        if name not in selected_pages:
                            selected_pages.append(name)
                        break
        else:
            selected_pages = page_names
        
        if not selected_pages:
            return SkillResult(
                success=False,
                error=f"没有找到匹配「{selection}」的页面",
                suggestion=f"可用页面：{', '.join(page_names[:10])}..."
            )
        
        test_types = params.get("types", ["positive", "negative"])
        priority = params.get("priority", "P1")
        
        # Generate test cases
        test_cases = self._generate(selected_pages, test_types, priority)
        
        # Update session
        session.test_cases = test_cases
        
        # Count by type
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
                "selected_pages": selected_pages,
                "type_summary": type_summary
            },
            message=f"已为 {len(selected_pages)} 个页面生成 {len(test_cases)} 条测试用例（{type_summary}）"
        )
    
    def _generate(self, page_names: List[str], test_types: List[str], priority: str) -> List[Dict]:
        from ..services.generator.test_case_generator import TestCaseGenerator
        
        generator = TestCaseGenerator()
        return generator.generate(page_names, test_types, priority)
