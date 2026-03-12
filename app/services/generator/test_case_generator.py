"""
测试用例生成服务

根据需求页面名称和功能描述，自动生成标准格式的测试用例
"""

from typing import List, Dict, Optional
from enum import Enum


class TestCaseType(Enum):
    POSITIVE = "positive"       # 正向测试
    NEGATIVE = "negative"       # 逆向测试
    BOUNDARY = "boundary"       # 边界测试
    EXCEPTION = "exception"     # 异常测试
    SECURITY = "security"       # 安全测试
    PERFORMANCE = "performance" # 性能测试


class TestCaseGenerator:
    """测试用例生成器"""
    
    # 功能关键词映射
    FUNCTION_KEYWORDS = {
        "登录": ["用户名", "密码", "验证码", "手机号"],
        "注册": ["手机号", "验证码", "密码", "用户协议"],
        "充值": ["金额", "支付方式", "银行卡"],
        "提现": ["金额", "银行卡", "手续费"],
        "修改": ["原", "新", "确认"],
        "编辑": ["修改", "保存", "取消"],
        "新增": ["创建", "添加", "保存"],
        "删除": ["确认", "取消"],
        "搜索": ["关键词", "筛选", "结果"],
        "列表": ["排序", "筛选", "分页"],
        "详情": ["查看", "返回"],
        "评论": ["内容", "提交"],
        "分享": ["方式", "链接"],
    }
    
    # 测试用例模板
    TEMPLATES = {
        TestCaseType.POSITIVE: {
            "title_template": "正向-{page_name}成功",
            "steps_template": "1. 进入{page_name}页面\n2. 填写有效信息\n3. 点击提交",
            "expected_template": "1. 页面正常加载\n2. 信息填写成功\n3. 操作成功"
        },
        TestCaseType.NEGATIVE: {
            "title_template": "逆向-{page_name}失败-{reason}",
            "steps_template": "1. 进入{page_name}页面\n2. {invalid_action}\n3. 点击提交",
            "expected_template": "1. 页面正常加载\n2. 输入框显示错误\n3. Toast提示错误信息"
        },
        TestCaseType.BOUNDARY: {
            "title_template": "边界-{page_name}边界值测试",
            "steps_template": "1. 进入{page_name}页面\n2. 输入边界值\n3. 点击提交",
            "expected_template": "1. 页面正常加载\n2. 边界值验证通过\n3. 操作结果符合预期"
        }
    }
    
    def generate(
        self,
        page_names: List[str],
        test_types: Optional[List[str]] = None,
        priority: str = "P1"
    ) -> List[Dict]:
        """
        生成测试用例
        
        Args:
            page_names: 页面名称列表
            test_types: 测试类型列表
            priority: 优先级
            
        Returns:
            测试用例列表
        """
        if test_types is None:
            test_types = ["positive", "negative"]
        
        test_cases = []
        case_id = 1
        
        for page_name in page_names:
            # 清理页面名称
            clean_name = self._clean_page_name(page_name)
            module = self._extract_module(clean_name)
            
            for test_type in test_types:
                cases = self._generate_for_type(
                    clean_name=clean_name,
                    module=module,
                    test_type=test_type,
                    priority=priority,
                    start_id=case_id
                )
                test_cases.extend(cases)
                case_id += len(cases)
        
        return test_cases
    
    def _clean_page_name(self, name: str) -> str:
        """清理页面名称"""
        # 移除状态标记
        name = name.replace("（新增）", "").replace("(新增)", "")
        name = name.replace("（修改）", "").replace("(修改)", "")
        name = name.replace("_1", "").replace("_2", "")
        return name.strip()
    
    def _extract_module(self, page_name: str) -> str:
        """提取模块名"""
        # 从页面名称提取模块
        for keyword in ["登录", "注册", "充值", "提现", "用户", "订单", "消息", "活动", "游戏", "VIP"]:
            if keyword in page_name:
                return keyword.upper()[:5]
        return "COMMON"
    
    def _generate_for_type(
        self,
        clean_name: str,
        module: str,
        test_type: str,
        priority: str,
        start_id: int
    ) -> List[Dict]:
        """根据类型生成测试用例"""
        test_cases = []
        
        if test_type == "positive":
            test_cases.append(self._create_positive_case(clean_name, module, start_id, priority))
        elif test_type == "negative":
            # 生成多个逆向用例
            negative_cases = self._create_negative_cases(clean_name, module, start_id, priority)
            test_cases.extend(negative_cases)
        elif test_type == "boundary":
            test_cases.append(self._create_boundary_case(clean_name, module, start_id, priority))
        elif test_type == "security":
            test_cases.append(self._create_security_case(clean_name, module, start_id, priority))
        
        return test_cases
    
    def _create_positive_case(self, name: str, module: str, case_id: int, priority: str) -> Dict:
        """创建正向测试用例"""
        return {
            "id": f"TC_{module}_{case_id:03d}",
            "title": f"正向-{name}成功",
            "preconditions": "1. 用户已登录\n2. 系统正常运行",
            "steps": f"1. 进入{name}页面\n2. 填写有效信息\n3. 点击提交",
            "expected_results": f"1. 页面正常加载\n2. 信息填写成功\n3. 操作成功",
            "priority": priority,
            "type": "positive",
            "remarks": None
        }
    
    def _create_negative_cases(self, name: str, module: str, start_id: int, priority: str) -> List[Dict]:
        """创建逆向测试用例"""
        cases = []
        
        # 空值测试
        cases.append({
            "id": f"TC_{module}_{start_id:03d}",
            "title": f"逆向-{name}-必填项为空",
            "preconditions": "1. 用户已登录",
            "steps": f"1. 进入{name}页面\n2. 不填写必填项\n3. 点击提交",
            "expected_results": f"1. 页面正常加载\n2. 必填项标红\n3. Toast提示'请填写必填项'",
            "priority": priority,
            "type": "negative",
            "remarks": None
        })
        
        # 格式错误测试
        cases.append({
            "id": f"TC_{module}_{start_id + 1:03d}",
            "title": f"逆向-{name}-格式错误",
            "preconditions": "1. 用户已登录",
            "steps": f"1. 进入{name}页面\n2. 输入错误格式\n3. 点击提交",
            "expected_results": f"1. 页面正常加载\n2. 格式校验失败\n3. Toast提示'格式错误'",
            "priority": priority,
            "type": "negative",
            "remarks": None
        })
        
        return cases
    
    def _create_boundary_case(self, name: str, module: str, case_id: int, priority: str) -> Dict:
        """创建边界测试用例"""
        return {
            "id": f"TC_{module}_{case_id:03d}",
            "title": f"边界-{name}-边界值测试",
            "preconditions": "1. 用户已登录\n2. 已了解字段限制",
            "steps": f"1. 进入{name}页面\n2. 输入最小值\n3. 输入最大值\n4. 验证边界",
            "expected_results": f"1. 页面正常加载\n2. 最小值验证通过\n3. 最大值验证通过\n4. 边界验证正确",
            "priority": priority,
            "type": "boundary",
            "remarks": None
        }
    
    def _create_security_case(self, name: str, module: str, case_id: int, priority: str) -> Dict:
        """创建安全测试用例"""
        return {
            "id": f"TC_{module}_{case_id:03d}",
            "title": f"安全-{name}-SQL注入测试",
            "preconditions": "1. 用户已登录",
            "steps": f"1. 进入{name}页面\n2. 输入SQL注入语句\n3. 点击提交",
            "expected_results": f"1. 页面正常加载\n2. 注入语句被过滤\n3. 系统安全",
            "priority": "P0",
            "type": "security",
            "remarks": "安全测试"
        }


# ==================== 统一入口 ====================

def generate_test_cases(
    page_names: List[str],
    test_types: Optional[List[str]] = None,
    priority: str = "P1"
) -> List[Dict]:
    """
    生成测试用例（统一入口）
    
    Args:
        page_names: 页面名称列表
        test_types: 测试类型列表
        priority: 优先级
        
    Returns:
        测试用例列表
    """
    generator = TestCaseGenerator()
    return generator.generate(page_names, test_types, priority)
