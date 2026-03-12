"""
分析API接口 | Analysis API Endpoints

提供异步分析接口，支持进度查询
Provides async analysis API with progress tracking.
"""

import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.engine import Engine
from app.platforms.registry import PlatformRegistry
from app.services.async_tasks import get_task_manager
from app.llm import LLMFactory
from app.utils.security import sanitize_url

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 请求模型 Request Models ============

class AnalyzeRequest(BaseModel):
    """分析请求 | Analyze Request"""
    url: str  # 使用str而非HttpUrl，以便自定义验证
    pages: Optional[List[str]] = None
    llm_type: Optional[str] = None  # glm, gpt, qwen, ernie, custom
    
    @validator('url')
    def validate_url(cls, v):
        """验证并清理URL"""
        try:
            return sanitize_url(v)
        except ValueError as e:
            raise ValueError(str(e))
    
    @validator('pages', each_item=True)
    def validate_pages(cls, v):
        """验证页面名称"""
        if len(v) > 100:
            raise ValueError('页面名称过长')
        return v


class AnalyzeResponse(BaseModel):
    """分析响应 | Analyze Response"""
    status: str
    message: str
    task_id: Optional[str] = None


# ============ API端点 API Endpoints ============

@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    启动分析任务 | Start analysis task
    
    异步执行，立即返回task_id
    Executes asynchronously, returns task_id immediately.
    
    **流程 Flow:**
    1. 验证平台支持 | Validate platform support
    2. 创建任务 | Create task
    3. 后台执行 | Execute in background
    4. 返回task_id | Return task_id
    
    **前端处理 Frontend:**
    - 立即显示进度条 | Show progress bar immediately
    - 轮询 `/analyze/{task_id}` 获取进度 | Poll `/analyze/{task_id}` for progress
    """
    url_str = str(request.url)
    
    # 检查平台支持
    if not PlatformRegistry.is_supported(url_str):
        supported = [p["display_name"] for p in PlatformRegistry.list_platforms()]
        raise HTTPException(
            status_code=400,
            detail=f"不支持的平台 | Unsupported platform. Supported: {supported}"
        )
    
    # 创建任务
    manager = get_task_manager()
    task_id = manager.create_task()
    
    # 获取平台信息
    adapter = PlatformRegistry.get_adapter(url_str)
    platform_name = adapter.info.display_name if adapter else "Unknown"
    
    # 定义后台任务
    async def run_analysis():
        engine = Engine()  # TODO: 传入LLM配置
        result = await engine.run(
            url=url_str,
            pages=request.pages,
            progress_callback=lambda p: manager.update_progress(
                task_id,
                p.get("step", p.get("state", "")),
                int(p.get("current", 0) * 10),
                int(p.get("total", 0) * 10),
                p.get("message", "")
            )
        )
        return result
    
    # 添加到后台任务
    from app.services.async_tasks import analyze_url_task
    background_tasks.add_task(
        manager.run_task,
        task_id,
        run_analysis
    )
    
    return AnalyzeResponse(
        status="processing",
        message=f"任务已启动，平台: {platform_name} | Task started, platform: {platform_name}",
        task_id=task_id
    )


@router.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str):
    """
    获取分析状态 | Get analysis status
    
    轮询此接口获取进度和结果
    Poll this endpoint for progress and results.
    
    **响应示例 Response Example:**
    ```json
    {
      "task_id": "abc123",
      "status": "running",
      "progress": {
        "step": "generating",
        "percentage": 60.0,
        "message": "正在生成测试用例..."
      },
      "result": null
    }
    ```
    """
    manager = get_task_manager()
    task = manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在 | Task not found")
    
    response = {
        "task_id": task.task_id,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
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
    
    if task.completed_at:
        response["completed_at"] = task.completed_at.isoformat()
    
    return response


@router.delete("/analyze/{task_id}")
async def cancel_analysis(task_id: str):
    """
    取消分析任务 | Cancel analysis task
    """
    manager = get_task_manager()
    
    if manager.cancel_task(task_id):
        return {"status": "cancelled", "task_id": task_id}
    else:
        raise HTTPException(
            status_code=400,
            detail="无法取消任务（已完成或不存在）| Cannot cancel task (completed or not found)"
        )


@router.get("/platforms")
async def list_platforms():
    """
    列出支持的平台 | List supported platforms
    
    返回所有已注册的平台信息
    Returns all registered platform information.
    """
    platforms = PlatformRegistry.list_platforms()
    
    return {
        "total": len(platforms),
        "platforms": platforms
    }


@router.get("/health")
async def health_check():
    """健康检查 | Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.1.0-dev"
    }