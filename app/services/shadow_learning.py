"""
影子运行自学习服务
核心思想：记录用户修正 + Prompt + Context，构建Few-Shot学习库
"""

import json
import os
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import pickle


@dataclass
class CorrectionCase:
    """修正案例"""
    id: str
    timestamp: datetime
    
    # 原始生成
    original_prompt: str
    original_context: str
    original_output: Dict[str, Any]
    
    # 用户修正
    corrected_output: Dict[str, Any]
    correction_type: str  # "modify", "add", "delete", "reorder"
    correction_reason: Optional[str] = None
    
    # 相似度向量（用于检索）
    prompt_embedding: Optional[List[float]] = None
    
    # 元数据
    page_name: str = ""
    platform: str = ""
    user_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "original_prompt": self.original_prompt,
            "original_context": self.original_context,
            "original_output": self.original_output,
            "corrected_output": self.corrected_output,
            "correction_type": self.correction_type,
            "correction_reason": self.correction_reason,
            "page_name": self.page_name,
            "platform": self.platform,
        }


@dataclass 
class FewShotExample:
    """Few-Shot示例"""
    prompt: str
    context: str
    expected_output: str
    source_case_id: str
    relevance_score: float = 1.0


class ShadowLearningService:
    """
    影子运行自学习服务
    
    核心能力：
    1. 记录用户对生成内容的修正
    2. 构建向量索引（支持BM25或简单的关键词匹配）
    3. 自动检索相似案例作为Few-Shot示例
    4. 持续优化生成质量
    """
    
    def __init__(self, storage_dir: str = "./data/learning"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.cases_file = self.storage_dir / "correction_cases.json"
        self.index_file = self.storage_dir / "search_index.pkl"
        
        self.cases: List[CorrectionCase] = []
        self.keyword_index: Dict[str, List[str]] = {}  # keyword -> case_ids
        
        self._load_cases()
        self._build_index()
    
    def _load_cases(self):
        """加载历史修正案例"""
        if self.cases_file.exists():
            try:
                with open(self.cases_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("cases", []):
                        case = CorrectionCase(
                            id=item["id"],
                            timestamp=datetime.fromisoformat(item["timestamp"]),
                            original_prompt=item["original_prompt"],
                            original_context=item["original_context"],
                            original_output=item["original_output"],
                            corrected_output=item["corrected_output"],
                            correction_type=item["correction_type"],
                            correction_reason=item.get("correction_reason"),
                            page_name=item.get("page_name", ""),
                            platform=item.get("platform", ""),
                        )
                        self.cases.append(case)
                print(f"[学习服务] 已加载 {len(self.cases)} 个修正案例")
            except Exception as e:
                print(f"[学习服务] 加载失败: {e}")
    
    def _save_cases(self):
        """保存修正案例"""
        with open(self.cases_file, "w", encoding="utf-8") as f:
            json.dump({
                "cases": [case.to_dict() for case in self.cases],
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _build_index(self):
        """构建搜索索引（简单的关键词倒排索引）"""
        self.keyword_index = {}
        
        for case in self.cases:
            # 提取关键词
            keywords = self._extract_keywords(case.original_prompt + " " + case.original_context)
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(case.id)
        
        print(f"[学习服务] 索引构建完成，关键词数: {len(self.keyword_index)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现：分词 + 过滤停用词）"""
        # 停用词
        stopwords = {"的", "是", "在", "和", "了", "有", "我", "你", "他", "她", "它",
                     "这", "那", "就", "也", "都", "为", "能", "会", "要", "不", "上", "下"}
        
        # 简单分词（按空格和标点）
        import re
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text.lower())
        
        # 过滤
        keywords = []
        for word in words:
            if len(word) >= 2 and word not in stopwords:
                keywords.append(word)
        
        return list(set(keywords))[:20]  # 最多20个关键词
    
    def record_correction(
        self,
        original_prompt: str,
        original_context: str,
        original_output: Dict[str, Any],
        corrected_output: Dict[str, Any],
        correction_type: str = "modify",
        correction_reason: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> CorrectionCase:
        """
        记录用户修正
        
        这是核心方法：每当用户修改生成结果时调用
        """
        # 生成唯一ID
        content_hash = hashlib.md5(
            f"{original_prompt}{original_context}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        case = CorrectionCase(
            id=f"case_{content_hash}",
            timestamp=datetime.now(),
            original_prompt=original_prompt,
            original_context=original_context,
            original_output=original_output,
            corrected_output=corrected_output,
            correction_type=correction_type,
            correction_reason=correction_reason,
            page_name=metadata.get("page_name", "") if metadata else "",
            platform=metadata.get("platform", "") if metadata else "",
            user_id=metadata.get("user_id", "") if metadata else "",
        )
        
        self.cases.append(case)
        self._save_cases()
        
        # 更新索引
        keywords = self._extract_keywords(original_prompt + " " + original_context)
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            self.keyword_index[keyword].append(case.id)
        
        print(f"[学习服务] 记录修正案例: {case.id}")
        print(f"           类型: {correction_type}, 关键词: {keywords[:5]}")
        
        return case
    
    def search_similar_cases(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.1
    ) -> List[FewShotExample]:
        """
        检索相似案例
        
        用于Few-Shot学习：在生成新内容前，检索相似的历史修正案例
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        
        # 计算每个案例的相关性分数
        case_scores: Dict[str, float] = {}
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for case_id in self.keyword_index[keyword]:
                    if case_id not in case_scores:
                        case_scores[case_id] = 0
                    case_scores[case_id] += 1
        
        # 归一化分数
        if case_scores:
            max_score = max(case_scores.values())
            for case_id in case_scores:
                case_scores[case_id] /= max_score
        
        # 排序并返回top_k
        sorted_cases = sorted(case_scores.items(), key=lambda x: x[1], reverse=True)
        
        examples = []
        for case_id, score in sorted_cases[:top_k]:
            if score < min_score:
                continue
            
            # 查找案例
            case = next((c for c in self.cases if c.id == case_id), None)
            if case:
                examples.append(FewShotExample(
                    prompt=case.original_prompt,
                    context=case.original_context,
                    expected_output=json.dumps(case.corrected_output, ensure_ascii=False),
                    source_case_id=case_id,
                    relevance_score=score
                ))
        
        print(f"[学习服务] 检索到 {len(examples)} 个相似案例")
        return examples
    
    def build_few_shot_prompt(
        self,
        current_prompt: str,
        current_context: str,
        max_examples: int = 3
    ) -> str:
        """
        构建带Few-Shot示例的Prompt
        
        在生成测试用例时，自动加入相似的历史修正案例
        """
        examples = self.search_similar_cases(current_prompt, top_k=max_examples)
        
        if not examples:
            return current_prompt
        
        # 构建Few-Shot部分
        few_shot_section = "\n\n## 参考示例（来自历史修正）\n\n"
        
        for i, example in enumerate(examples, 1):
            few_shot_section += f"""### 示例 {i} (相关性: {example.relevance_score:.2f})

**需求上下文:**
{example.context[:200]}...

**期望输出:**
{example.expected_output[:500]}...

---
"""
        
        enhanced_prompt = current_prompt + few_shot_section
        enhanced_prompt += "\n\n请参考上述示例，生成符合要求的测试用例。"
        
        return enhanced_prompt
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        type_counts = {}
        for case in self.cases:
            t = case.correction_type
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_cases": len(self.cases),
            "correction_types": type_counts,
            "keywords_count": len(self.keyword_index),
            "recent_cases": len([c for c in self.cases if (datetime.now() - c.timestamp).days <= 7])
        }


# 全局实例
_shadow_learning: Optional[ShadowLearningService] = None


def get_shadow_learning() -> ShadowLearningService:
    """获取学习服务单例"""
    global _shadow_learning
    if _shadow_learning is None:
        _shadow_learning = ShadowLearningService()
    return _shadow_learning


# 使用示例
if __name__ == "__main__":
    service = ShadowLearningService()
    
    # 模拟记录一个修正
    service.record_correction(
        original_prompt="生成登录页面的测试用例",
        original_context="页面包含用户名、密码输入框和登录按钮",
        original_output={"test_cases": [{"title": "登录测试"}]},
        corrected_output={"test_cases": [
            {"title": "正向-正确登录", "steps": ["输入正确用户名", "输入正确密码", "点击登录"]},
            {"title": "逆向-密码错误", "steps": ["输入正确用户名", "输入错误密码", "点击登录"]}
        ]},
        correction_type="add",
        correction_reason="需要覆盖更多场景",
        metadata={"page_name": "登录", "platform": "modao"}
    )
    
    # 检索相似案例
    examples = service.search_similar_cases("生成登录测试用例")
    print(f"\n检索结果:")
    for ex in examples:
        print(f"  - {ex.source_case_id}: {ex.relevance_score:.2f}")
    
    # 统计
    print(f"\n统计: {service.get_statistics()}")
