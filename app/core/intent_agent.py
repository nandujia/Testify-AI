"""Intent agent"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import re


class Intent(str, Enum):
    ANALYZE_URL = "analyze_url"
    GENERATE_TESTCASE = "gen_testcase"
    EXTRACT_DEMAND = "extract_demand"  # New
    EXPORT = "export"
    SELECT = "select"
    QA = "qa"
    HELP = "help"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    intent: Intent
    entities: Dict[str, Any] = {}
    confidence: float = 0.0
    missing_params: List[str] = []


class IntentAgent:
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def analyze(self, user_message: str, session=None) -> IntentResult:
        message_lower = user_message.lower()
        
        # URL analysis
        if self._contains_url(user_message):
            url = self._extract_url(user_message)
            return IntentResult(intent=Intent.ANALYZE_URL, entities={"url": url}, confidence=0.95)
        
        # Extract demand (new)
        extract_patterns = [
            r'提取\s*(.+?)\s*的需求',
            r'解析\s*(.+?)\s*的需求',
            r'提取需求.*选择\s+(.+)',
            r'从\s*(.+?)\s*提取需求',
        ]
        
        for pattern in extract_patterns:
            match = re.search(pattern, user_message)
            if match:
                selection = match.group(1).strip()
                return IntentResult(intent=Intent.EXTRACT_DEMAND, entities={"selection": selection}, confidence=0.9)
        
        # Simple extract demand
        if any(kw in message_lower for kw in ["提取需求", "解析需求", "提取页面需求"]):
            return IntentResult(intent=Intent.EXTRACT_DEMAND, confidence=0.85)
        
        # Selection for test cases
        select_patterns = [
            r'选择\s+(.+)',
            r'生成\s+(.+?)\s*(?:的)?测试用例',
            r'为\s*(.+?)\s*生成',
            r'只生成\s+(.+)',
        ]
        
        for pattern in select_patterns:
            match = re.search(pattern, user_message)
            if match:
                selection = match.group(1).strip()
                return IntentResult(intent=Intent.GENERATE_TESTCASE, entities={"selection": selection}, confidence=0.9)
        
        # Generate all test cases
        if any(kw in message_lower for kw in ["生成测试用例", "写测试用例", "生成用例"]):
            return IntentResult(intent=Intent.GENERATE_TESTCASE, confidence=0.85)
        
        # Export
        if any(kw in message_lower for kw in ["导出", "下载", "保存excel"]):
            return IntentResult(intent=Intent.EXPORT, confidence=0.85)
        
        # Help
        if any(kw in message_lower for kw in ["帮助", "怎么用", "使用说明"]):
            return IntentResult(intent=Intent.HELP, confidence=0.9)
        
        return IntentResult(intent=Intent.UNKNOWN, confidence=0.0)
    
    def _contains_url(self, message: str) -> bool:
        return bool(re.search(r'https?://[^\s]+', message))
    
    def _extract_url(self, message: str) -> Optional[str]:
        match = re.search(r'https?://[^\s]+', message)
        return match.group(0) if match else None
