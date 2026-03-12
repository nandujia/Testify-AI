"""Export skill"""

from typing import Dict, Any
from .base import BaseSkill, SkillResult
from ..core.session import SessionState


class ExportSkill(BaseSkill):
    
    name = "export"
    description = "导出测试用例到文件"
    triggers = ["导出", "下载", "保存"]
    
    parameters = {"format": {"required": False, "description": "导出格式"}}
    
    def execute(self, params: Dict[str, Any], session: SessionState) -> SkillResult:
        test_cases = session.test_cases
        
        if not test_cases:
            return SkillResult(
                success=False,
                error="没有可导出的测试用例",
                suggestion="请先生成测试用例"
            )
        
        export_format = params.get("format", "xlsx")
        
        try:
            file_path = self._export(test_cases, export_format)
        except Exception as e:
            return SkillResult(success=False, error=f"导出失败: {str(e)}")
        
        session.exported_files.append(file_path)
        
        import os
        file_name = os.path.basename(file_path)
        
        return SkillResult(
            success=True,
            data={
                "file_path": file_path,
                "file_name": file_name,
                "format": export_format,
                "count": len(test_cases)
            },
            message=f"已导出 {len(test_cases)} 条测试用例到 {file_name}"
        )
    
    def _export(self, test_cases: list, export_format: str) -> str:
        from ..services.extractor.excel_exporter import ExcelExporter
        from datetime import datetime
        from pathlib import Path
        import json
        
        if export_format == "xlsx":
            exporter = ExcelExporter()
            return exporter.export(test_cases)
        
        elif export_format == "markdown":
            export_dir = Path("./exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = export_dir / f"test_cases_{timestamp}.md"
            content = self._generate_markdown(test_cases)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return str(file_path)
        
        elif export_format == "json":
            export_dir = Path("./exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = export_dir / f"test_cases_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(test_cases, f, ensure_ascii=False, indent=2)
            return str(file_path)
        
        else:
            exporter = ExcelExporter()
            return exporter.export(test_cases)
    
    def _generate_markdown(self, test_cases: list) -> str:
        from datetime import datetime
        
        lines = [
            "# 测试用例文档",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总数: {len(test_cases)}",
            "",
            "---",
            ""
        ]
        
        for tc in test_cases:
            lines.extend([
                f"## {tc.get('id', 'N/A')} - {tc.get('title', 'N/A')}",
                "",
                f"- **优先级**: {tc.get('priority', 'N/A')}",
                f"- **类型**: {tc.get('type', 'N/A')}",
                "",
                "### 前置条件",
                tc.get("preconditions", "无"),
                "",
                "### 操作步骤",
                tc.get("steps", "无"),
                "",
                "### 预期结果",
                tc.get("expected_results", "无"),
                "",
                "---",
                ""
            ])
        
        return "\n".join(lines)
