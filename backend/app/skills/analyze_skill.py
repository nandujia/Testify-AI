"""Analyze skill - prototype analysis"""

from typing import Dict, Any, Optional
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class AnalyzeSkill(BaseSkill):
    
    name = "analyze"
    description = "分析原型设计链接，提取需求目录结构"
    triggers = ["分析", "看看", "提取需求", "解析原型"]
    
    parameters = {"url": {"required": True, "description": "原型链接URL"}}
    
    PLATFORMS = {
        "modao": {"name": "墨刀", "coverage": "100%"},
        "lanhu": {"name": "蓝湖", "coverage": "100%"},
        "axure": {"name": "Axure Share", "coverage": "100%"},
        "mokc": {"name": "幕客", "coverage": "100%"},
        "figma": {"name": "Figma", "coverage": "100%"},
        "jsdesign": {"name": "即时设计", "coverage": "100%"},
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
        
        analysis = self._summarize_requirements(result.get("pages", []))
        
        session.current_url = url
        session.current_platform = platform
        session.analyzed_pages = result.get("pages", [])
        
        return SkillResult(
            success=True,
            data={
                "platform": self.PLATFORMS.get(platform, {}).get("name", platform),
                "url": url,
                "pages": result.get("pages", []),
                "total": result.get("extracted", 0),
                "expected": result.get("expected", 0),
                "match_rate": result.get("match_rate", "0%"),
                "analysis": analysis
            },
            message=f"已分析 {self.PLATFORMS.get(platform, {}).get('name', platform)} 原型，提取 {result.get('extracted', 0)} 个页面"
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
    
    def _summarize_requirements(self, pages: list) -> str:
        if not pages:
            return ""
        
        page_names = [p.get("name", "") for p in pages]
        
        modules = set()
        for name in page_names:
            for keyword in ["登录", "注册", "用户", "订单", "支付", "消息", "设置", "首页"]:
                if keyword in name:
                    modules.add(keyword)
        
        summary = f"共 {len(pages)} 个页面\n\n"
        if modules:
            summary += f"涉及模块：{', '.join(modules)}\n\n"
        summary += f"页面列表：\n" + "\n".join(f"- {name}" for name in page_names[:20])
        if len(page_names) > 20:
            summary += f"\n... 等共 {len(page_names)} 个页面"
        
        return summary
