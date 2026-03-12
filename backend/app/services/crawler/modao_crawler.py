"""Modao crawler with hierarchy support"""

import re
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright


class ModaoCrawler:
    
    def __init__(self, timeout: int = 60, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.document_content = None
        self.variables = {}
    
    def crawl(self, url: str) -> Dict:
        expected_count = 0
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            
            def handle_response(response):
                if 'axdata.modao.ink' in response.url and 'document.js' in response.url:
                    try:
                        self.document_content = response.text()
                    except:
                        pass
            
            page.on('response', handle_response)
            page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            
            page_text = page.evaluate("() => document.body.innerText")
            page_count_match = re.search(r'页面[（(](\d+)[）)]', page_text)
            if page_count_match:
                expected_count = int(page_count_match.group(1))
            
            browser.close()
        
        if not self.document_content:
            return {"success": False, "error": "未能获取数据", "expected": expected_count, "extracted": 0, "match_rate": "0%", "pages": []}
        
        # Extract variables
        self._extract_variables()
        
        # Parse sitemap tree
        pages = self._parse_sitemap()
        
        total = self._count_pages(pages)
        match_rate = total / expected_count * 100 if expected_count > 0 else 0
        
        return {
            "success": True,
            "expected": expected_count,
            "extracted": total,
            "match_rate": f"{match_rate:.1f}%",
            "pages": pages
        }
    
    def _extract_variables(self):
        """Extract variable definitions"""
        for match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', self.document_content):
            self.variables[match.group(1)] = match.group(2)
    
    def _parse_sitemap(self) -> List[Dict]:
        """Parse sitemap tree"""
        # Find sitemap array: r,[...]
        idx = self.document_content.find('r,[')
        if idx == -1:
            return []
        
        # Find matching ]
        bracket_count = 0
        j = idx + 2
        start = j
        
        while j < len(self.document_content):
            c = self.document_content[j]
            if c == '[':
                bracket_count += 1
            elif c == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    break
            j += 1
        
        sitemap_str = self.document_content[start:j+1]
        
        # Parse nodes
        return self._parse_node_array(sitemap_str)
    
    def _parse_node_array(self, s: str) -> List[Dict]:
        """Parse array of nodes"""
        nodes = []
        i = 0
        
        while i < len(s):
            # Find _(s,
            if s[i:i+4] != '_(s,':
                i += 1
                continue
            
            # Find matching )
            bracket_count = 0
            j = i
            while j < len(s):
                c = s[j]
                if c == '(':
                    bracket_count += 1
                elif c == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                j += 1
            
            node_str = s[i+2:j]  # Skip _(
            node = self._parse_node(node_str)
            if node:
                nodes.append(node)
            
            i = j + 1
        
        return nodes
    
    def _parse_node(self, node_str: str) -> Optional[Dict]:
        """Parse single node: s,id,u,name,w,type,x,y,url,A,[children]"""
        # Extract id and pageName variables
        match = re.match(r's,([^,]+),u,([^,]+)', node_str)
        if not match:
            return None
        
        id_var = match.group(1)
        name_var = match.group(2)
        
        # Get actual values
        page_name = self.variables.get(name_var, "")
        
        if not page_name:
            return None
        
        # Check if has children: A,[...]
        children = []
        children_match = re.search(r'A,\[(.+)\]$', node_str)
        if children_match:
            children = self._parse_node_array(children_match.group(1))
        
        # Check if folder (type = cW = "Folder")
        is_folder = ',cW,' in node_str
        
        return {
            "id": id_var,
            "name": page_name,
            "is_folder": is_folder,
            "status": self._get_status(page_name),
            "children": children
        }
    
    def _count_pages(self, pages: List[Dict]) -> int:
        """Count all pages"""
        count = 0
        for p in pages:
            if not p.get("is_folder"):
                count += 1
            if p.get("children"):
                count += self._count_pages(p["children"])
        return count
    
    def _get_status(self, name: str) -> Optional[str]:
        if '（新增）' in name or '(新增)' in name:
            return "新增"
        elif '（修改）' in name or '(修改)' in name:
            return "修改"
        return None


def identify_platform(url: str) -> Optional[str]:
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


def crawl_url(url: str) -> Dict:
    platform = identify_platform(url)
    if platform == "modao":
        return ModaoCrawler().crawl(url)
    return {"success": False, "error": f"平台 {platform} 暂不支持", "expected": 0, "extracted": 0, "match_rate": "0%", "pages": []}
