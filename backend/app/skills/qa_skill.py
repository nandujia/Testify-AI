"""QA skill"""

from typing import Dict, Any
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class QASkill(BaseSkill):
    
    name = "qa"
    description = "回答用户问题"
    triggers = ["是什么", "怎么做", "有什么", "能不能"]
    
    parameters = {"question": {"required": True, "description": "用户问题"}}
    
    def execute(self, params: Dict[str, Any], session: SessionState) -> SkillResult:
        question = params.get("question", "")
        
        if not question:
            return SkillResult(success=False, error="请提供问题")
        
        context = self._build_context(session)
        
        if self.llm:
            answer = self._llm_answer(question, context, session)
        else:
            answer = self._rule_answer(question, session)
        
        return SkillResult(success=True, data={"answer": answer}, message=answer)
    
    def _build_context(self, session: SessionState) -> str:
        parts = []
        if session.current_url:
            parts.append(f"当前分析的原型：{session.current_platform} - {session.current_url}")
        if session.analyzed_pages:
            page_names = [p.get("name", "") for p in session.analyzed_pages[:10]]
            parts.append(f"已分析的页面：{', '.join(page_names)}")
        if session.test_cases:
            parts.append(f"已生成 {len(session.test_cases)} 条测试用例")
        return "\n".join(parts)
    
    def _llm_answer(self, question: str, context: str, session: SessionState) -> str:
        from ..llm import Message, MessageRole
        
        prompt = f"""你是一个测试用例生成助手。

上下文：
{context}

用户问题：
{question}

请简洁友好地回答。"""
        
        try:
            return self.llm.chat([Message(role=MessageRole.USER, content=prompt)])
        except:
            return self._rule_answer(question, session)
    
    def _rule_answer(self, question: str, session: SessionState) -> str:
        question_lower = question.lower()
        
        if "功能" in question or "能做什么" in question:
            return """我可以帮你：

1. **分析原型链接** - 发送原型链接，提取页面目录
2. **生成测试用例** - 根据需求自动生成测试用例
3. **导出文件** - 导出 Excel/Markdown/JSON 格式
4. **上传知识库** - 上传需求文档增强用例质量

有什么我可以帮你的？"""
        
        if "怎么用" in question or "如何" in question:
            return """使用方法：

1. 发送原型链接让我分析
2. 说「生成测试用例」
3. 说「导出Excel」

试试发送一个墨刀或蓝湖链接吧。"""
        
        if "当前" in question or "状态" in question:
            if session.current_url:
                return f"当前：{session.current_platform} 原型，{len(session.analyzed_pages)} 个页面，{len(session.test_cases)} 条用例"
            return "还没有分析任何原型。发送一个链接开始吧！"
        
        return "抱歉，我暂时无法回答这个问题。试试问我「有什么功能」或「怎么用」。"
