"""
测试用例生成 API 路由
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse, TestCase
from app.services.generator.test_case_generator import generate_test_cases

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    生成测试用例
    
    - **pages**: 页面名称列表
    - **types**: 测试类型（positive/negative/boundary/security）
    - **priority**: 优先级（P0/P1/P2/P3）
    """
    try:
        test_cases = generate_test_cases(
            page_names=request.pages,
            test_types=[t.value for t in request.types] if request.types else None,
            priority=request.priority.value
        )
        
        return GenerateResponse(
            success=True,
            total=len(test_cases),
            test_cases=[TestCase(**tc) for tc in test_cases]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
