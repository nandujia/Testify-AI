"""Intent recognition agent"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import re


class Intent(str, Enum):
    ANALYZE_URL = "analyze_url"
    GENERATE_TESTCASE = "gen_testcase"
    EXPORT = "export"
    UPLOAD_DOC = "upload_doc"
    SEARCH_KB = "search_kb"
    QA = "qa"
    REPORT = "report"
    CONFIG = "config"
    HELP = "help"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    intent: Intent
    entities: Dict[str, Any] = {}
    confidence: float = 0.0
    missing_params: List[str] = []
    sub_intents: List[Intent] = []
    raw_response: Optional[str] = None


class IntentAgent:
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def analyze(self, user_message: str, session=None) -> IntentResult:
        rule_result = self._rule_based_match(user_message, session)
        if rule_result and rule_result.confidence > 0.9:
            return rule_result
        
        if self.llm:
            return self._llm_analyze(user_message, session)
        
        return rule_result or IntentResult(intent=Intent.UNKNOWN, confidence=0.0)
    
    def _rule_based_match(self, message: str, session=None) -> Optional[IntentResult]:
        message_lower = message.lower()
        
        if self._contains_url(message):
            url = self._extract_url(message)
            return IntentResult(
                intent=Intent.ANALYZE_URL,
                entities={"url": url},
                confidence=0.95
            )
        
        patterns = [
            (["分析", "看看", "提取需求", "解析原型"], Intent.ANALYZE_URL),
            (["生成测试用例", "写测试用例", "生成用例"], Intent.GENERATE_TESTCASE),
            (["导出", "下载", "保存excel", "导出excel"], Intent.EXPORT),
            (["上传", "添加文档"], Intent.UPLOAD_DOC),
            (["查询", "搜索知识"], Intent.SEARCH_KB),
            (["生成报告", "分析报告"], Intent.REPORT),
            (["设置", "配置"], Intent.CONFIG),
            (["帮助", "怎么用", "使用说明"], Intent.HELP),
        ]
        
        for keywords, intent in patterns:
            for keyword in keywords:
                if keyword in message_lower:
                    entities = {}
                    if intent == Intent.GENERATE_TESTCASE and session:
                        if session.analyzed_pages:
                            entities["pages"] = [p["name"] for p in session.analyzed_pages]
                    elif intent == Intent.EXPORT and session:
                        if session.test_cases:
                            entities["has_testcases"] = True
                    return IntentResult(intent=intent, entities=entities, confidence=0.85)
        
        return None
    
    def _llm_analyze(self, message: str, session=None) -> IntentResult:
        from ..llm import Message, MessageRole
        
        prompt = f"""分析用户意图，返回JSON格式。

支持意图: analyze_url, gen_testcase, export, upload_doc, search_kb, qa, report, config, help

用户消息: {message}

返回格式:
{{"intent": "意图", "entities": {{}}, "confidence": 0.95, "missing_params": []}}
"""
        try:
            response = self.llm.chat([Message(role=MessageRole.USER, content=prompt)])
            import json
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return IntentResult(
                    intent=Intent(data.get("intent", "unknown")),
                    entities=data.get("entities", {}),
                    confidence=data.get("confidence", 0.8),
                    missing_params=data.get("missing_params", [])
                )
        except:
            pass
        
        return IntentResult(intent=Intent.UNKNOWN, confidence=0.0)
    
    def _contains_url(self, message: str) -> bool:
        return bool(re.search(r'https?://[^\s]+', message))
    
    def _extract_url(self, message: str) -> Optional[str]:
        match = re.search(r'https?://[^\s]+', message)
        return match.group(0) if match else None
