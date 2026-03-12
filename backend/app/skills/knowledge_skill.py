"""
知识库技能
"""

from typing import Dict, Any, Optional
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class KnowledgeSkill(BaseSkill):
    """知识库操作"""
    
    name = "knowledge"
    description = "知识库上传和检索"
    triggers = ["上传", "知识库", "检索"]
    
    parameters = {
        "action": {"required": True, "description": "操作类型 (upload/search)"},
        "content": {"required": False, "description": "文档内容（上传时）"},
        "query": {"required": False, "description": "检索查询（检索时）"}
    }
    
    def execute(
        self,
        params: Dict[str, Any],
        session: SessionState
    ) -> SkillResult:
        """执行操作"""
        action = params.get("action", "search")
        
        if not self.knowledge_base:
            return SkillResult(
                success=False,
                error="知识库未启用",
                suggestion="请在配置中启用知识库功能"
            )
        
        if action == "upload":
            return self._upload(params)
        elif action == "search":
            return self._search(params)
        else:
            return SkillResult(
                success=False,
                error=f"未知操作: {action}"
            )
    
    def _upload(self, params: Dict[str, Any]) -> SkillResult:
        """上传文档"""
        content = params.get("content")
        title = params.get("title")
        
        if not content:
            return SkillResult(
                success=False,
                error="缺少文档内容"
            )
        
        try:
            document = self.knowledge_base.upload_document(
                content=content,
                title=title
            )
            
            return SkillResult(
                success=True,
                data={
                    "document_id": document.id,
                    "title": document.title,
                    "chunk_count": len(document.chunks)
                },
                message=f"文档已上传，包含 {len(document.chunks)} 个片段"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"上传失败: {str(e)}"
            )
    
    def _search(self, params: Dict[str, Any]) -> SkillResult:
        """检索知识"""
        query = params.get("query")
        top_k = params.get("top_k", 5)
        
        if not query:
            return SkillResult(
                success=False,
                error="缺少检索查询"
            )
        
        try:
            results = self.knowledge_base.retrieve(query, top_k)
            context = self.knowledge_base.get_context(query, top_k)
            
            return SkillResult(
                success=True,
                data={
                    "results": [
                        {
                            "content": r.chunk.content[:200],
                            "score": r.score,
                            "document_title": r.document.title if r.document else None
                        }
                        for r in results
                    ],
                    "context": context
                },
                message=f"找到 {len(results)} 条相关内容"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"检索失败: {str(e)}"
            )
