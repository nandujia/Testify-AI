"""
平台适配器基类
低侵入式设计：每个平台一个适配器，互不干扰
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from app.adapters.sniffer import DataSniffer, SniffedData
from app.core.schema import RequirementNode, ExtractionResult


@dataclass
class AdapterConfig:
    """适配器配置"""
    name: str
    display_name: str
    url_patterns: List[str]
    api_patterns: List[str]
    document_js_patterns: List[str]


class BaseAdapter(ABC):
    """
    平台适配器基类
    
    设计原则：
    1. 低侵入：不依赖DOM/OCR，只做数据嗅探
    2. 可插拔：新平台只需实现parse_data方法
    3. 标准化输出：统一转换为RequirementNode
    """
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config
        self.sniffer = DataSniffer()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """显示名称"""
        pass
    
    @abstractmethod
    def match(self, url: str) -> bool:
        """判断URL是否匹配此平台"""
        pass
    
    @abstractmethod
    def get_sniff_patterns(self) -> Dict[str, List[str]]:
        """
        获取嗅探模式
        返回: {"api": [...], "document_js": [...], "sitemap": [...]}
        """
        pass
    
    @abstractmethod
    async def parse_sniffed_data(
        self, 
        sniffed_data: List[SniffedData]
    ) -> List[RequirementNode]:
        """
        解析嗅探到的数据
        这是最关键的方法：将原始JSON转换为标准需求节点
        """
        pass
    
    async def extract(self, url: str) -> ExtractionResult:
        """
        执行提取流程
        
        标准流程：
        1. 设置嗅探模式
        2. 执行嗅探
        3. 解析数据
        4. 返回结果
        """
        print(f"\n[{self.display_name}] 开始提取")
        print(f"URL: {url}")
        
        # 设置嗅探模式
        patterns = self.get_sniff_patterns()
        self.sniffer.patterns = {}
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                self.sniffer.register_pattern(category, pattern)
        
        # 执行嗅探
        sniff_result = await self.sniffer.sniff(url, platform=self.name)
        
        # 解析数据
        if sniff_result.get("sniffed_count", 0) > 0:
            # 重建SniffedData对象
            sniffed_data = []
            for source, items in sniff_result.get("data_sources", {}).items():
                for item in items:
                    sniffed_data.append(SniffedData(
                        url=item["url"],
                        method="GET",
                        status=item["status"],
                        headers={},
                        body=item.get("body"),
                        source=source,
                        parsed=item.get("parsed")
                    ))
            
            nodes = await self.parse_sniffed_data(sniffed_data)
        else:
            nodes = []
        
        return ExtractionResult(
            platform=self.name,
            url=url,
            pages=nodes,
            total_elements=sum(len(n.elements) for n in nodes),
            success=len(nodes) > 0,
            error=None if nodes else "未能提取到数据"
        )
