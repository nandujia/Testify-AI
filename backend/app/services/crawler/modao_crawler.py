"""Modao crawler"""

import re
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright


class ModaoCrawler:
    
    def __init__(self, timeout: int = 60, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.document_content = None
        self.document_url = None
    
    def crawl(self, url: str) -> Dict:
        expected_count = 0
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            def handle_response(response):
                resp_url = response.url
                if 'axdata.modao.ink' in resp_url and 'document.js' in resp_url:
                    try:
                        self.document_url = resp_url
                        self.document_content = response.text()
                    except:
                        pass
            
            page.on('response', handle_response)
            
            page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            
            # Get expected page count
            page_text = page.evaluate("() => document.body.innerText")
            page_count_match = re.search(r'页面[（(](\d+)[）)]', page_text)
            if page_count_match:
                expected_count = int(page_count_match.group(1))
            
            browser.close()
        
        if not self.document_content:
            return {
                "success": False,
                "error": "未能获取数据",
                "expected": expected_count,
                "extracted": 0,
                "match_rate": "0%",
                "pages": []
            }
        
        # Parse pages using multiple methods
        pages = self._parse_document()
        
        match_rate = len(pages) / expected_count * 100 if expected_count > 0 else 0
        
        return {
            "success": True,
            "expected": expected_count,
            "extracted": len(pages),
            "match_rate": f"{match_rate:.1f}%",
            "pages": [{"id": str(i), "name": p, "status": self._get_status(p)} for i, p in enumerate(pages, 1)]
        }
    
    def _parse_document(self) -> List[str]:
        """Parse document.js using multiple methods"""
        all_pages = set()
        
        # Method 1: Extract from .html file references
        html_files = re.findall(r'"([^"]+\.html)"', self.document_content)
        for f in html_files:
            name = f.replace('.html', '')
            if 2 < len(name) < 50 and not name.startswith('_') and '号字' not in name:
                all_pages.add(name)
        
        # Method 2: Extract Chinese strings (page names)
        all_strings = re.findall(r'"([^"]+)"', self.document_content)
        for s in all_strings:
            if 2 < len(s) < 50:
                # Check if it contains Chinese characters
                has_chinese = bool(re.search(r'[\u4e00-\u9fff]', s))
                has_underscore = s.startswith('_')
                has_special = any(c in s for c in ['.js', '.css', 'http', 'data/', 'resources/', 'images/'])
                
                if has_chinese and not has_underscore and not has_special:
                    # Clean up - remove .html suffix if present
                    clean_name = s.replace('.html', '')
                    all_pages.add(clean_name)
        
        # Filter and sort
        pages = []
        for p in all_pages:
            # Skip pure technical strings
            if p in ['configuration', 'undefined', 'null']:
                continue
            pages.append(p)
        
        return sorted(pages)
    
    def _get_status(self, page_name: str) -> Optional[str]:
        if '（新增）' in page_name or '(新增)' in page_name:
            return "新增"
        elif '（修改）' in page_name or '(修改)' in page_name:
            return "修改"
        return None


PLATFORM_PATTERNS = {
    "modao": [r"modao\.cc"],
    "lanhu": [r"lanhuapp\.com"],
    "axure": [r"share\.axure\.com", r"axshare\.com"],
    "mokc": [r"mokc\.cn"],
    "figma": [r"figma\.com"],
    "jsdesign": [r"js\.design"],
}


def identify_platform(url: str) -> Optional[str]:
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url):
                return platform
    return None


def crawl_url(url: str) -> Dict:
    platform = identify_platform(url)
    
    if platform == "modao":
        crawler = ModaoCrawler()
        return crawler.crawl(url)
    else:
        return {
            "success": False,
            "error": f"平台 {platform} 暂不支持",
            "expected": 0,
            "extracted": 0,
            "match_rate": "0%",
            "pages": []
        }
