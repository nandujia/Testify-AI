"""
对话 API
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..core.orchestrator import Orchestrator
from ..core.session import SessionManager
from ..llm import LLMFactory
from ..knowledge import KnowledgeBase
from ..services.config_service import ConfigService

router = APIRouter()

# 全局实例
_config_service: Optional[ConfigService] = None
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """获取 Orchestrator 实例"""
    global _orchestrator, _config_service
    
    if _orchestrator is None:
        _config_service = ConfigService()
        
        # 获取 LLM
        llm = None
        profile = _config_service.get_default_llm_profile()
        if profile:
            try:
                llm = LLMFactory.create_from_profile(profile)
            except:
                pass
        
        # 获取知识库
        kb = None
        app_config = _config_service.get_app_config()
        if app_config.kb_enabled:
            try:
                kb = KnowledgeBase(storage_dir=app_config.kb_storage_dir)
            except:
                pass
        
        _orchestrator = Orchestrator(
            llm=llm,
            knowledge_base=kb,
            config_service=_config_service
        )
    
    return _orchestrator


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""
    success: bool
    session_id: str
    intent: str
    message: str
    data: Dict[str, Any] = {}
    suggestion: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口
    
    支持自然语言交互：
    - "分析 https://modao.cc/xxx"
    - "生成测试用例"
    - "导出Excel"
    - "有什么功能"
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.process(request.message, request.session_id)
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话状态"""
    orchestrator = get_orchestrator()
    context = orchestrator.get_session_context(session_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "context": context
    }


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    orchestrator = get_orchestrator()
    success = orchestrator.clear_session(session_id)
    
    return {
        "success": success,
        "message": "会话已清除" if success else "会话不存在"
    }


@router.get("/skills")
async def list_skills():
    """列出所有可用技能"""
    from ..skills.registry import SkillRegistry
    
    return {
        "skills": SkillRegistry.list_all()
    }
