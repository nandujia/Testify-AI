"""
适配器模块
低侵入式产研数据转换器

核心思想：
- Canvas是根据数据绘图，截获数据包即拥有完美DOM
- 每个平台一个适配器，互不干扰
- 新增平台只需实现parse_data方法
"""

from .base import BaseAdapter, AdapterConfig
from .sniffer import DataSniffer, SniffedData, sniff_url

__all__ = [
    "BaseAdapter",
    "AdapterConfig",
    "DataSniffer",
    "SniffedData",
    "sniff_url",
]