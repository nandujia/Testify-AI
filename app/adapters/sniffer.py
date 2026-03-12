"""
数据嗅探引擎 - Network Interception
核心思想：Canvas是根据数据绘图，截获数据包即拥有完美DOM
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Response, Route, Request


@dataclass
class SniffedData:
    """嗅探到的数据包"""
    url: str
    method: str
    status: int
    headers: Dict[str, str]
    body: Any
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 解析后的结构化数据
    parsed: Optional[Dict[str, Any]] = None
    source: str = "unknown"  # api, document_js, sitemap, etc.


@dataclass
class PageStructure:
    """页面结构数据"""
    page_id: str
    page_name: str
    elements: List[Dict[str, Any]]
    raw_data: Dict[str, Any]
    hidden_fields: List[Dict[str, Any]] = field(default_factory=list)
    internal_notes: List[str] = field(default_factory=list)


class DataSniffer:
    """
    数据嗅探器
    
    核心能力：
    1. 拦截所有网络请求
    2. 识别关键数据包（API、document.js等）
    3. 解析Canvas背后的原始数据
    4. 提取隐藏字段和内部备注
    """
    
    def __init__(self, output_dir: str = "./data/sniffed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.sniffed_data: List[SniffedData] = []
        self.page_structures: List[PageStructure] = []
        
        # 数据包匹配规则
        self.patterns: Dict[str, re.Pattern] = {}
        
    def register_pattern(self, name: str, pattern: str):
        """注册数据包匹配规则"""
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)
        
    def _match_patterns(self, url: str) -> List[str]:
        """匹配URL的所有规则"""
        matches = []
        for name, pattern in self.patterns.items():
            if pattern.search(url):
                matches.append(name)
        return matches
    
    async def create_interceptor(self) -> Callable:
        """创建拦截器回调函数"""
        
        async def intercept(route: Route, request: Request):
            url = request.url
            method = request.method
            
            # 检查是否需要拦截
            matches = self._match_patterns(url)
            
            if matches:
                print(f"[嗅探] 拦截请求: {method} {url[:80]}...")
                print(f"       匹配规则: {matches}")
                
                # 继续请求
                response = await route.fetch()
                body = await response.text()
                
                # 尝试解析JSON
                try:
                    parsed_body = json.loads(body)
                except:
                    parsed_body = body
                
                # 记录嗅探数据
                sniffed = SniffedData(
                    url=url,
                    method=method,
                    status=response.status,
                    headers=dict(response.headers),
                    body=parsed_body,
                    source=matches[0] if matches else "unknown"
                )
                
                # 如果是JSON，尝试解析
                if isinstance(parsed_body, dict):
                    sniffed.parsed = await self._parse_data(sniffed)
                
                self.sniffed_data.append(sniffed)
                
                # 完成请求
                await route.fulfill(response=response, body=body)
            else:
                # 不拦截，直接继续
                await route.continue_()
        
        return intercept
    
    async def _parse_data(self, sniffed: SniffedData) -> Dict[str, Any]:
        """
        解析嗅探到的数据
        提取隐藏字段、组件ID、内部备注等
        """
        parsed = {
            "raw_keys": [],
            "hidden_fields": [],
            "internal_notes": [],
            "component_ids": [],
        }
        
        body = sniffed.body
        if not isinstance(body, dict):
            return parsed
        
        # 递归提取所有键名
        def extract_keys(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    parsed["raw_keys"].append(full_key)
                    
                    # 检测隐藏字段
                    if any(h in key.lower() for h in ["hidden", "private", "internal", "secret"]):
                        parsed["hidden_fields"].append({
                            "key": full_key,
                            "value": str(value)[:100]  # 只保留前100字符
                        })
                    
                    # 检测内部备注
                    if any(n in key.lower() for n in ["note", "comment", "remark", "description"]):
                        if isinstance(value, str) and value:
                            parsed["internal_notes"].append(value)
                    
                    # 检测组件ID
                    if any(i in key.lower() for i in ["id", "componentid", "widgetid"]):
                        parsed["component_ids"].append(str(value))
                    
                    extract_keys(value, full_key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_keys(item, f"{prefix}[{i}]")
        
        extract_keys(body)
        return parsed
    
    async def sniff(self, url: str, platform: str = "auto") -> Dict[str, Any]:
        """
        执行嗅探
        
        Args:
            url: 目标URL
            platform: 平台类型 (modao, lanhu, figma, auto)
        
        Returns:
            嗅探结果
        """
        print(f"\n{'='*60}")
        print(f"开始数据嗅探")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        # 根据平台设置匹配规则
        if platform == "auto":
            platform = self._detect_platform(url)
        
        self._setup_platform_patterns(platform)
        
        # 创建拦截器
        interceptor = await self.create_interceptor()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            
            # 注册路由拦截
            await context.route("**/*", interceptor)
            
            page = await context.new_page()
            
            try:
                print("1. 导航到页面...")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
                
                print("2. 触发数据加载...")
                await self._trigger_data_loading(page)
                
                print("3. 等待所有请求完成...")
                await page.wait_for_timeout(5000)
                
            except Exception as e:
                print(f"错误: {e}")
            finally:
                await browser.close()
        
        # 整理结果
        result = {
            "platform": platform,
            "url": url,
            "sniffed_count": len(self.sniffed_data),
            "data_sources": {},
            "page_structures": [],
            "hidden_fields": [],
            "internal_notes": [],
        }
        
        # 按来源分类
        for data in self.sniffed_data:
            source = data.source
            if source not in result["data_sources"]:
                result["data_sources"][source] = []
            result["data_sources"][source].append({
                "url": data.url[:100],
                "status": data.status,
                "has_body": data.body is not None,
                "parsed": data.parsed
            })
            
            # 收集隐藏字段和内部备注
            if data.parsed:
                result["hidden_fields"].extend(data.parsed.get("hidden_fields", []))
                result["internal_notes"].extend(data.parsed.get("internal_notes", []))
        
        # 保存原始数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"sniffed_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "sniffed_data": [
                    {
                        "url": d.url,
                        "method": d.method,
                        "status": d.status,
                        "body": d.body if not isinstance(d.body, (dict, list)) else d.body
                    }
                    for d in self.sniffed_data
                ]
            }, f, ensure_ascii=False, indent=2, default=str)
        
        result["output_file"] = str(output_file)
        
        print(f"\n{'='*60}")
        print(f"嗅探完成!")
        print(f"  拦截数据包: {result['sniffed_count']} 个")
        print(f"  数据来源: {list(result['data_sources'].keys())}")
        print(f"  隐藏字段: {len(result['hidden_fields'])} 个")
        print(f"  内部备注: {len(result['internal_notes'])} 条")
        print(f"  输出文件: {output_file}")
        print(f"{'='*60}\n")
        
        return result
    
    def _detect_platform(self, url: str) -> str:
        """自动检测平台"""
        if "modao" in url:
            return "modao"
        elif "lanhu" in url:
            return "lanhu"
        elif "figma" in url:
            return "figma"
        elif "axure" in url:
            return "axure"
        return "unknown"
    
    def _setup_platform_patterns(self, platform: str):
        """设置平台特定的匹配规则"""
        self.patterns = {}
        
        if platform == "modao":
            # 墨刀的关键数据接口
            self.register_pattern("document_js", r"document\.js")
            self.register_pattern("sitemap", r"sitemap|treelist")
            self.register_pattern("api_pages", r"/api/.*/pages")
            self.register_pattern("workspace", r"workspace|project")
            self.register_pattern("axdata", r"axdata\.modao")
            
        elif platform == "lanhu":
            # 蓝湖的关键数据接口
            self.register_pattern("api_design", r"/api/design")
            self.register_pattern("boards", r"boards|artboards")
            
        elif platform == "figma":
            # Figma的关键数据接口
            self.register_pattern("api_nodes", r"/api/nodes")
            self.register_pattern("file_data", r"/file/\w+")
        
        # 通用规则
        self.register_pattern("json_api", r"\.json$|/api/")
        self.register_pattern("data_endpoint", r"data|content|page")
    
    async def _trigger_data_loading(self, page: Page):
        """触发数据加载"""
        # 滚动页面
        for i in range(5):
            await page.evaluate(f"window.scrollBy(0, {800 * (i+1)})")
            await page.wait_for_timeout(300)
        
        # 点击可能的展开按钮
        try:
            expand_buttons = await page.query_selector_all('[class*="expand"], [class*="more"]')
            for btn in expand_buttons[:3]:
                await btn.click()
                await page.wait_for_timeout(200)
        except:
            pass


# 便捷函数
async def sniff_url(url: str, platform: str = "auto") -> Dict[str, Any]:
    """嗅探URL的快捷函数"""
    sniffer = DataSniffer()
    return await sniffer.sniff(url, platform)


# 命令行入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sniffer.py <url> [platform]")
        sys.exit(1)
    
    url = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    result = asyncio.run(sniff_url(url, platform))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
