"""
学习记录 API
"""

from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

from ..services.learning_service import LearningService, LearningType

router = APIRouter()

_learning_service = LearningService()


class ErrorRecordRequest(BaseModel):
    """错误记录请求"""
    error: str
    context: dict = {}


class CorrectionRequest(BaseModel):
    """纠正请求"""
    original: str
    corrected: str
    context: dict = {}


class BestPracticeRequest(BaseModel):
    """最佳实践请求"""
    pattern: str
    practice: str
    tags: List[str] = []


@router.get("/stats")
async def get_learning_stats():
    """获取学习统计"""
    return _learning_service.get_stats()


@router.get("/records")
async def list_records(
    type: Optional[LearningType] = None,
    limit: int = 50
):
    """列出学习记录"""
    records = _learning_service._records
    
    if type:
        records = [r for r in records if r.type == type]
    
    return {
        "records": [r.model_dump() for r in records[:limit]],
        "total": len(records)
    }


@router.post("/errors")
async def record_error(request: ErrorRecordRequest):
    """记录错误"""
    record = _learning_service.record_error(
        error=request.error,
        context=request.context
    )
    return {"success": True, "record_id": record.id}


@router.post("/corrections")
async def record_correction(request: CorrectionRequest):
    """记录纠正"""
    record = _learning_service.record_correction(
        original=request.original,
        corrected=request.corrected,
        context=request.context
    )
    return {"success": True, "record_id": record.id}


@router.post("/best-practices")
async def record_best_practice(request: BestPracticeRequest):
    """记录最佳实践"""
    _learning_service.record_best_practice(
        pattern=request.pattern,
        practice=request.practice,
        tags=request.tags
    )
    return {"success": True}


@router.get("/solutions/{error}")
async def find_solution(error: str):
    """查找解决方案"""
    solution = _learning_service.get_solution(error)
    similar = _learning_service.find_similar_errors(error)
    
    return {
        "solution": solution,
        "similar_errors": [
            {"id": r.id, "summary": r.summary, "solution": r.solution}
            for r in similar
        ]
    }


@router.get("/best-practices/{pattern}")
async def get_best_practice(pattern: str):
    """获取最佳实践"""
    practice = _learning_service.get_best_practice(pattern)
    return {
        "pattern": pattern,
        "practice": practice
    }


@router.post("/records/{record_id}/promote")
async def promote_record(record_id: str):
    """将记录提升为最佳实践"""
    success = _learning_service.promote_to_best_practice(record_id)
    return {"success": success}
