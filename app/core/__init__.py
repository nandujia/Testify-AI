"""
核心模块 | Core Module

提供核心功能组件
Provides core functionality components.
"""

from .schema import (
    ElementType,
    TestCasePriority,
    TestCaseType,
    UIElement,
    RequirementNode,
    TestCaseStep,
    TestCase,
    ExtractionResult,
    GenerationResult,
    ExportResult,
)

# Engine 需要单独导入，避免循环依赖
# from .engine import Engine, WorkflowState, WorkflowContext

__all__ = [
    # Schema
    "ElementType",
    "TestCasePriority",
    "TestCaseType",
    "UIElement",
    "RequirementNode",
    "TestCaseStep",
    "TestCase",
    "ExtractionResult",
    "GenerationResult",
    "ExportResult",
]