"""
异步任务管理器
核心思想：使用FastAPI BackgroundTasks，确保API立即响应，后台处理任务
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import traceback


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """任务进度"""
    step: str = ""
    current: int = 0
    total: int = 0
    percentage: float = 0.0
    message: str = ""


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    progress: TaskProgress = field(default_factory=TaskProgress)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    traceback: Optional[str] = None


class AsyncTaskManager:
    """
    异步任务管理器
    
    核心能力：
    1. 立即返回task_id，后台执行
    2. 实时进度跟踪
    3. 任务结果存储
    4. 支持任务取消
    """
    
    def __init__(self, storage_dir: str = "./data/tasks"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的任务存储（生产环境应使用Redis）
        self.tasks: Dict[str, TaskResult] = {}
        
        # 进度回调
        self.progress_callbacks: Dict[str, List[Callable]] = {}
    
    def create_task(self) -> str:
        """创建新任务，返回task_id"""
        task_id = str(uuid.uuid4())
        
        task = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        self.progress_callbacks[task_id] = []
        
        print(f"[任务管理] 创建任务: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def update_progress(
        self,
        task_id: str,
        step: str,
        current: int,
        total: int,
        message: str = ""
    ):
        """更新任务进度"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.progress = TaskProgress(
            step=step,
            current=current,
            total=total,
            percentage=round(current / total * 100, 1) if total > 0 else 0,
            message=message
        )
        
        # 触发回调
        for callback in self.progress_callbacks.get(task_id, []):
            try:
                callback(task.progress)
            except:
                pass
        
        print(f"[任务进度] {task_id[:8]}... | {step}: {current}/{total} ({task.progress.percentage}%)")
    
    async def run_task(
        self,
        task_id: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> TaskResult:
        """
        执行异步任务
        
        Args:
            task_id: 任务ID
            task_func: 异步任务函数
            *args, **kwargs: 任务参数
        
        Returns:
            TaskResult
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 更新状态为运行中
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # 执行任务
            result = await task_func(task_id, *args, **kwargs)
            
            # 更新为完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            print(f"[任务管理] 任务完成: {task_id}")
            
        except Exception as e:
            # 更新为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            task.traceback = traceback.format_exc()
            
            print(f"[任务管理] 任务失败: {task_id}")
            print(f"           错误: {e}")
        
        # 保存结果
        self._save_task_result(task)
        
        return task
    
    def _save_task_result(self, task: TaskResult):
        """保存任务结果到文件"""
        result_file = self.storage_dir / f"{task.task_id}.json"
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task.task_id,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "progress": {
                    "step": task.progress.step,
                    "current": task.progress.current,
                    "total": task.progress.total,
                    "percentage": task.progress.percentage,
                    "message": task.progress.message
                },
                "result": task.result,
                "error": task.error
            }, f, ensure_ascii=False, indent=2, default=str)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.error = "用户取消"
        
        return True
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理过期任务"""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.completed_at:
                age = (now - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            del self.progress_callbacks[task_id]
        
        if to_remove:
            print(f"[任务管理] 清理 {len(to_remove)} 个过期任务")


# 全局实例
_task_manager: Optional[AsyncTaskManager] = None


def get_task_manager() -> AsyncTaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager


# ============ 具体任务实现 ============

async def analyze_url_task(task_id: str, url: str, pages: Optional[List[str]] = None):
    """
    分析URL的异步任务
    
    这是一个完整的任务示例，展示如何在后台执行多步骤任务
    """
    manager = get_task_manager()
    
    # Step 1: 数据嗅探 (30%)
    manager.update_progress(task_id, "数据嗅探", 0, 3, "正在拦截网络请求...")
    
    from app.adapters.sniffer import DataSniffer
    sniffer = DataSniffer()
    sniff_result = await sniffer.sniff(url)
    
    manager.update_progress(task_id, "数据嗅探", 1, 3, f"已拦截 {sniff_result['sniffed_count']} 个数据包")
    
    # Step 2: 数据转换 (60%)
    manager.update_progress(task_id, "数据转换", 1, 3, "正在解析数据结构...")
    
    # 这里应该有实际的数据转换逻辑
    # transformed_data = await transform_data(sniff_result)
    
    manager.update_progress(task_id, "数据转换", 2, 3, "数据解析完成")
    
    # Step 3: 生成测试用例 (100%)
    manager.update_progress(task_id, "生成用例", 2, 3, "正在生成测试用例...")
    
    # 使用影子学习服务构建增强Prompt
    from app.services.shadow_learning import get_shadow_learning
    learning = get_shadow_learning()
    
    enhanced_prompt = learning.build_few_shot_prompt(
        f"分析URL: {url}",
        json.dumps(sniff_result, ensure_ascii=False, default=str)[:1000]
    )
    
    # 这里应该调用LLM生成
    # test_cases = await generate_test_cases(enhanced_prompt, sniff_result)
    
    manager.update_progress(task_id, "生成用例", 3, 3, "测试用例生成完成")
    
    return {
        "url": url,
        "sniff_result": sniff_result,
        "enhanced_prompt": enhanced_prompt[:500],
        "test_cases": []  # 实际结果
    }


# ============ API集成示例 ============

"""
# 在 api/analyze.py 中使用:

from fastapi import BackgroundTasks
from app.services.async_tasks import get_task_manager, analyze_url_task

@router.post("/analyze")
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    manager = get_task_manager()
    task_id = manager.create_task()
    
    # 添加后台任务
    background_tasks.add_task(
        manager.run_task,
        task_id,
        analyze_url_task,
        str(request.url),
        request.pages
    )
    
    return {"task_id": task_id, "status": "processing"}


@router.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str):
    manager = get_task_manager()
    task = manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": {
            "step": task.progress.step,
            "current": task.progress.current,
            "total": task.progress.total,
            "percentage": task.progress.percentage,
            "message": task.progress.message
        },
        "result": task.result,
        "error": task.error
    }
"""