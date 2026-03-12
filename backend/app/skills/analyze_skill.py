"""Analyze skill"""

from typing import Dict, Any, Optional, List
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class AnalyzeSkill(BaseSkill):
    
    name = "analyze"
    description = "分析原型设计链接，提取需求目录"
    
    parameters = {"url": {"required": True, "description": "原型链接URL"}}
    
    PLATFORMS = {
        "modao": "墨刀",
        "lanhu": "蓝湖",
        "axure": "Axure Share",
        "mokc": "幕客",
        "figma": "Figma",
        "jsdesign": "即时设计",
    }
    
    def execute(self, params: Dict[str, Any], session: SessionState) -> SkillResult:
        url = params.get("url")
        
        if not url:
            return SkillResult(
                success=False,
                error="缺少URL参数",
                suggestion="请提供原型链接"
            )
        
        platform = self._identify_platform(url)
        
        if not platform:
            return SkillResult(
                success=False,
                error="无法识别平台",
                suggestion="支持：墨刀、蓝湖、Axure、幕客、Figma、即时设计"
            )
        
        try:
            result = self._crawl(url, platform)
        except Exception as e:
            return SkillResult(success=False, error=f"分析失败: {str(e)}")
        
        # Update session
        session.current_url = url
        session.current_platform = platform
        session.analyzed_pages = result.get("pages", [])
        
        pages = result.get("pages", [])
        platform_name = self.PLATFORMS.get(platform, platform)
        
        # Build response
        return SkillResult(
            success=True,
            data={
                "platform": platform_name,
                "url": url,
                "pages": pages,
                "total": result.get("extracted", 0),
                "expected": result.get("expected", 0),
                "match_rate": result.get("match_rate", "0%"),
            },
            message=f"已分析 {platform_name} 原型，提取 {len(pages)} 个页面。\n\n请选择需要生成测试用例的页面，例如：选择 VIP、VIP等级说明"
        )
    
    def _identify_platform(self, url: str) -> Optional[str]:
        import re
        patterns = {
            "modao": [r"modao\.cc"],
            "lanhu": [r"lanhuapp\.com"],
            "axure": [r"share\.axure\.com", r"axshare\.com"],
            "mokc": [r"mokc\.cn"],
            "figma": [r"figma\.com"],
            "jsdesign": [r"js\.design"],
        }
        for platform, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, url):
                    return platform
        return None
    
    def _crawl(self, url: str, platform: str) -> Dict[str, Any]:
        from ..services.crawler.modao_crawler import ModaoCrawler, crawl_url
        if platform == "modao":
            crawler = ModaoCrawler()
            return crawler.crawl(url)
        return crawl_url(url)
