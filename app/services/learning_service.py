"""
自我学习服务
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class LearningType(str, Enum):
    ERROR = "error"           # 错误记录
    CORRECTION = "correction" # 用户纠正
    IMPROVEMENT = "improvement"  # 改进建议
    BEST_PRACTICE = "best_practice"  # 最佳实践


class LearningRecord(BaseModel):
    """学习记录"""
    id: str = Field(..., description="记录ID")
    type: LearningType
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 内容
    summary: str = Field(..., description="摘要")
    details: str = Field(..., description="详情")
    context: Dict[str, Any] = {}
    
    # 解决方案
    solution: Optional[str] = None
    applied: bool = False
    
    # 元数据
    tags: List[str] = []
    source: str = ""  # conversation/error/user_feedback
    session_id: Optional[str] = None


class LearningService:
    """自我学习服务"""
    
    def __init__(self, storage_dir: str = "./data/learning"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.records_file = self.storage_dir / "records.json"
        self.best_practices_file = self.storage_dir / "best_practices.json"
        
        self._records: List[LearningRecord] = self._load_records()
        self._best_practices: Dict[str, str] = self._load_best_practices()
    
    def _load_records(self) -> List[LearningRecord]:
        """加载记录"""
        if self.records_file.exists():
            with open(self.records_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [LearningRecord(**r) for r in data]
        return []
    
    def _save_records(self) -> None:
        """保存记录"""
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump(
                [r.model_dump() for r in self._records],
                f,
                ensure_ascii=False,
                indent=2,
                default=str
            )
    
    def _load_best_practices(self) -> Dict[str, str]:
        """加载最佳实践"""
        if self.best_practices_file.exists():
            with open(self.best_practices_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_best_practices(self) -> None:
        """保存最佳实践"""
        with open(self.best_practices_file, "w", encoding="utf-8") as f:
            json.dump(self._best_practices, f, ensure_ascii=False, indent=2)
    
    def record_error(
        self,
        error: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> LearningRecord:
        """记录错误"""
        import uuid
        
        record = LearningRecord(
            id=f"ERR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            type=LearningType.ERROR,
            summary=error[:100],
            details=error,
            context=context,
            source="error",
            session_id=session_id
        )
        
        self._records.append(record)
        self._save_records()
        
        return record
    
    def record_correction(
        self,
        original: str,
        corrected: str,
        context: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> LearningRecord:
        """记录用户纠正"""
        import uuid
        
        record = LearningRecord(
            id=f"COR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            type=LearningType.CORRECTION,
            summary=f"纠正: {original[:50]} → {corrected[:50]}",
            details=f"原始: {original}\n纠正: {corrected}",
            context=context,
            source="user_feedback",
            session_id=session_id
        )
        
        self._records.append(record)
        self._save_records()
        
        return record
    
    def record_best_practice(
        self,
        pattern: str,
        practice: str,
        tags: List[str] = []
    ) -> None:
        """记录最佳实践"""
        self._best_practices[pattern] = practice
        self._save_best_practices()
        
        import uuid
        record = LearningRecord(
            id=f"BP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            type=LearningType.BEST_PRACTICE,
            summary=f"最佳实践: {pattern}",
            details=practice,
            tags=tags,
            source="best_practice"
        )
        
        self._records.append(record)
        self._save_records()
    
    def find_similar_errors(self, error: str, limit: int = 5) -> List[LearningRecord]:
        """查找相似错误"""
        # 简单关键词匹配
        keywords = error.lower().split()[:5]
        
        similar = []
        for record in self._records:
            if record.type == LearningType.ERROR:
                if any(kw in record.details.lower() for kw in keywords):
                    similar.append(record)
        
        return similar[:limit]
    
    def get_solution(self, error: str) -> Optional[str]:
        """获取解决方案"""
        similar = self.find_similar_errors(error)
        
        for record in similar:
            if record.solution and record.applied:
                return record.solution
        
        return None
    
    def apply_solution(self, record_id: str, solution: str) -> None:
        """应用解决方案"""
        for record in self._records:
            if record.id == record_id:
                record.solution = solution
                record.applied = True
                break
        
        self._save_records()
    
    def get_best_practice(self, pattern: str) -> Optional[str]:
        """获取最佳实践"""
        # 精确匹配
        if pattern in self._best_practices:
            return self._best_practices[pattern]
        
        # 模糊匹配
        for key, value in self._best_practices.items():
            if key in pattern or pattern in key:
                return value
        
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计"""
        stats = {
            "total_records": len(self._records),
            "errors": 0,
            "corrections": 0,
            "best_practices": len(self._best_practices),
            "applied_solutions": 0
        }
        
        for record in self._records:
            if record.type == LearningType.ERROR:
                stats["errors"] += 1
            elif record.type == LearningType.CORRECTION:
                stats["corrections"] += 1
            
            if record.applied:
                stats["applied_solutions"] += 1
        
        return stats
    
    def promote_to_best_practice(self, record_id: str) -> bool:
        """将记录提升为最佳实践"""
        for record in self._records:
            if record.id == record_id and record.solution:
                # 从摘要中提取模式
                pattern = record.summary.split(":")[0] if ":" in record.summary else record.summary[:30]
                self._best_practices[pattern] = record.solution
                self._save_best_practices()
                return True
        return False
