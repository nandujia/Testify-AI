"""
爬取 API 路由
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import CrawlRequest, CrawlResponse
from app.services.crawler.modao_crawler import crawl_url

router = APIRouter()


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest):
    """
    爬取原型设计平台
    
    - **url**: 原型分享链接（支持墨刀、蓝湖、Axure等）
    """
    try:
        result = crawl_url(request.url)
        return CrawlResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
