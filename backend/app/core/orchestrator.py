"""Orchestrator - dispatch center"""

from typing import Dict, Any, Optional
from ..llm import BaseLLM, Message, MessageRole, LLMFactory
from ..knowledge import KnowledgeBase
from ..services.config_service import ConfigService
from .session import SessionManager, SessionState
from .intent_agent import IntentAgent, Intent
from ..skills.base import SkillResult
from ..skills.registry import SkillRegistry
from ..skills.analyze_skill import AnalyzeSkill
from ..skills.testcase_skill import TestCaseSkill
from ..skills.export_skill import ExportSkill
from ..skills.qa_skill import QASkill
from ..skills.demand_extractor_skill import DemandExtractorSkill


class Orchestrator:
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        config_service: Optional[ConfigService] = None
    ):
        self.llm = llm
        self.knowledge_base = knowledge_base
        self.config_service = config_service or ConfigService()
        
        self.session_manager = SessionManager()
        self.intent_agent = IntentAgent(llm=llm)
        
        self._register_skills()
    
    def _register_skills(self):
        SkillRegistry.register(AnalyzeSkill)
        SkillRegistry.register(TestCaseSkill)
        SkillRegistry.register(ExportSkill)
        SkillRegistry.register(QASkill)
        SkillRegistry.register(DemandExtractorSkill)
    
    def process(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        session = self.session_manager.get_or_create(session_id)
        self.session_manager.add_message(session.session_id, "user", user_message)
        
        intent_result = self.intent_agent.analyze(user_message, session)
        result = self._route_to_skill(intent_result, session)
        response = self._generate_response(result, session)
        
        self.session_manager.add_message(session.session_id, "assistant", response["message"])
        
        return {
            "session_id": session.session_id,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "success": result.success,
            "message": response["message"],
            "data": result.data,
            "suggestion": result.suggestion
        }
    
    def _route_to_skill(self, intent_result, session: SessionState) -> SkillResult:
        intent_map = {
            Intent.ANALYZE_URL: "analyze",
            Intent.GENERATE_TESTCASE: "gen_testcase",
            Intent.EXTRACT_DEMAND: "extract_demand",
            Intent.EXPORT: "export",
            Intent.QA: "qa",
            Intent.HELP: "qa",
        }
        
        skill_name = intent_map.get(intent_result.intent)
        
        if not skill_name:
            return SkillResult(
                success=False,
                error="抱歉，我没有理解你的意思",
                suggestion="你可以试试：「分析 https://xxx」或「提取VIP的需求」"
            )
        
        skill = SkillRegistry.get_or_create(
            skill_name,
            llm=self.llm,
            knowledge_base=self.knowledge_base
        )
        
        if not skill:
            return SkillResult(success=False, error=f"技能 {skill_name} 不可用")
        
        params = intent_result.entities.copy()
        missing = skill.validate_params(params)
        if missing:
            return SkillResult(
                success=False,
                error="缺少必要参数",
                suggestion=skill.ask_clarification(missing)
            )
        
        return skill.execute(params, session)
    
    def _generate_response(self, result: SkillResult, session: SessionState) -> Dict[str, str]:
        if result.success:
            if self.llm and result.data and len(result.message) > 50:
                return self._enhance_response(result, session)
            return {"message": result.message}
        else:
            message = result.error or "操作失败"
            if result.suggestion:
                message += f"\n\n{result.suggestion}"
            return {"message": message}
    
    def _enhance_response(self, result: SkillResult, session: SessionState) -> Dict[str, str]:
        if len(result.message) < 50:
            return {"message": result.message}
        
        prompt = f"""将以下信息转换为更友好的回复：

{result.message}

要求简洁友好。只返回回复内容。"""
        
        try:
            enhanced = self.llm.chat([Message(role=MessageRole.USER, content=prompt)])
            return {"message": enhanced}
        except:
            return {"message": result.message}
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        return self.session_manager.get_context_summary(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        return self.session_manager.delete(session_id)
