"""
导出 API 路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.schemas import ExportRequest, ExportResponse
from app.services.extractor.excel_exporter import export_to_excel

router = APIRouter()


@router.post("/export", response_model=ExportResponse)
async def export(request: ExportRequest):
    """
    导出测试用例
    
    - **format**: 导出格式（xlsx/markdown/json）
    - **test_cases**: 测试用例列表
    """
    try:
        if request.format == "xlsx":
            filepath = export_to_excel(request.test_cases)
            filename = filepath.split("/")[-1]
            
            return ExportResponse(
                success=True,
                file_url=f"/api/v1/download/{filename}",
                file_name=filename
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {request.format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download(filename: str):
    """下载导出的文件"""
    filepath = f"./exports/{filename}"
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
