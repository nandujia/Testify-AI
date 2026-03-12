# 智测AI (Testify AI)

<div align="center">

**基于多模态大模型的开源自动化测试工具**

**Open-Source Automated Testing Tool Based on Multimodal LLM**

[![Version](https://img.shields.io/badge/version-3.1.0--dev-orange.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[English](#english) | [中文](#中文)

</div>

---

<a name="中文"></a>
## 📖 产品简介

**智测AI（Testify AI）** 是一款基于多模态大模型、Agent 智能体与插件化架构构建的开源自动化测试工具，支持原型解析、需求结构化、自动用例生成、多格式导出等全流程能力，为测试工程师提供开箱即用的 AI 辅助工具。

### 🎯 核心能力

| 能力 | 说明 |
|------|------|
| **原型解析** | 自动解析墨刀、蓝湖、Figma等设计原型，提取页面结构和组件信息 |
| **需求结构化** | 将原始需求转换为结构化数据，支持智能分析和归类 |
| **自动用例生成** | 基于AI大模型自动生成测试用例，支持正向、逆向、边界等多种场景 |
| **多格式导出** | 支持Excel、JSON、Markdown等多种格式导出，对接主流测试管理平台 |

---

## ✨ 产品特性

### 🔍 协议级数据提取

```
传统方案 Traditional:
  DOM/OCR → 截图识别 → 易出错、Canvas无法解析

智测AI方案 Our Approach:
  Network Interception → 拦截数据包 → 完美DOM、隐藏字段、内部备注
```

**优势 Advantages:**
- ✅ 绕过Canvas渲染限制 | Bypass Canvas rendering limitations
- ✅ 获取隐藏字段和内部备注 | Extract hidden fields and internal notes
- ✅ 100%数据完整性 | 100% data integrity

### 🤖 结构化LLM输出

```python
# Pydantic保证100%可解析
class TestCase(BaseModel):
    title: str
    steps: List[TestCaseStep]
    expected_result: str
```

**优势 Advantages:**
- ✅ 类型安全 | Type safety
- ✅ 自动校验 | Automatic validation
- ✅ 无解析错误 | No parsing errors

### 🧠 影子运行自学习

```
用户修正 → 记录Prompt+Context → Few-Shot学习库 → 自动优化
```

**优势 Advantages:**
- ✅ 记录用户修正 | Record user corrections
- ✅ 自动检索相似案例 | Auto-retrieve similar cases
- ✅ 持续质量提升 | Continuous quality improvement

### ⚡ 全链路异步化

```
API立即响应 → 后台任务执行 → 实时进度跟踪
```

**优势 Advantages:**
- ✅ 非阻塞API | Non-blocking API
- ✅ 实时进度条 | Real-time progress bar
- ✅ 任务可取消 | Task cancellation

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                    │
│                   立即响应 + 后台任务                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Engine (编排引擎)                         │
│     Extractor → Generator (Few-Shot) → Exporter            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Platforms (平台插件)                        │
│   Modao | Lanhu | Figma | Axure | JSDesign | ...           │
│         策略模式 - 新增平台只需添加插件                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Interceptor (数据嗅探引擎)                     │
│   Network Interception → 原始JSON → 隐藏字段 + 内部备注      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
testify-ai/
├── app/
│   ├── core/                   # 核心模块
│   │   ├── schema.py          # 数据模型
│   │   └── engine.py          # 编排引擎
│   │
│   ├── platforms/              # 平台插件
│   │   ├── base.py            # 适配器基类
│   │   ├── registry.py        # 平台注册表
│   │   ├── modao/             # 墨刀
│   │   ├── lanhu/             # 蓝湖
│   │   └── figma/             # Figma
│   │
│   ├── adapters/               # 数据嗅探
│   │   └── sniffer.py         # 网络拦截引擎
│   │
│   ├── services/               # 服务层
│   │   ├── async_tasks.py     # 异步任务管理
│   │   └── shadow_learning.py # 自学习服务
│   │
│   ├── llm/                    # LLM适配层
│   ├── api/                    # API接口
│   └── main.py                 # 入口
│
├── data/                       # 数据存储
├── exports/                    # 导出文件
└── docs/                       # 文档
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+ (可选，用于前端)

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/nandujia/DemandTest.git
cd DemandTest

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 配置 LLM_API_KEY

# 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 访问 API 文档
# http://localhost:8000/docs
```

### Docker 部署

```bash
docker-compose up -d
# 访问 http://localhost:8000
```

---

## 📊 支持的平台

| 平台 Platform | 状态 Status | 说明 Description |
|---------------|-------------|------------------|
| 墨刀 Modao | ✅ 支持中 | 国产原型设计工具 |
| 蓝湖 Lanhu | 🚧 开发中 | 设计协作平台 |
| Figma | 🚧 开发中 | 在线设计工具 |
| Axure | 📋 计划中 | 专业原型工具 |
| 即时设计 JSDesign | 📋 计划中 | 国产设计工具 |

**新增平台**：只需实现 `BasePlatformAdapter`，无需修改核心代码！

---

## 🔌 插件开发

### 创建新平台插件

```python
# app/platforms/myplatform/adapter.py

from app.platforms.base import BasePlatformAdapter, PlatformInfo

class MyPlatformAdapter(BasePlatformAdapter):
    @property
    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="myplatform",
            display_name="我的平台",
            display_name_en="My Platform",
            url_patterns=["myplatform.com"]
        )
    
    def match(self, url: str) -> bool:
        return "myplatform.com" in url
    
    def get_sniff_patterns(self) -> dict:
        return {"api": ["/api/data"]}
    
    async def parse_sniffed_data(self, data):
        # 解析数据...
        return nodes

# 注册插件
from app.platforms.registry import PlatformRegistry
PlatformRegistry.register(MyPlatformAdapter)
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 协作模式

本项目采用 **Fork + Pull Request** 模式：

```
主仓库 (main) → 受保护，只接受PR
     ↑
  Pull Request (需要审核)
     ↑
贡献者的Fork → 开发 → 提交PR
```

### 如何贡献

```bash
# 1. Fork仓库到你的账户

# 2. 克隆你的Fork
git clone https://github.com/YOUR_USERNAME/DemandTest.git

# 3. 创建功能分支
git checkout -b feature/your-feature

# 4. 提交变更
git commit -m "feat: 添加XXX功能"

# 5. 推送并创建PR
git push origin feature/your-feature
```

详细指南请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🔐 数据隐私

### 数据安全原则

| 原则 | 说明 |
|------|------|
| **最小权限** | 仅请求必要的API权限 |
| **本地存储** | 所有数据存储在本地，不上传云端 |
| **敏感过滤** | 自动过滤敏感字段（密钥、密码等） |
| **审计日志** | 记录所有数据访问操作 |

### 数据存储位置

```
./data/
├── learning/     # 学习数据（本地）
├── tasks/        # 任务结果（本地）
└── sniffed/      # 嗅探数据（本地）

./exports/        # 导出文件（本地）
```

---

## 📝 许可证

[MIT License](LICENSE)

---

<a name="english"></a>
## 📖 English Documentation

### Product Overview

**Testify AI** is an open-source automated testing tool built on multimodal LLM, Agent intelligence, and plugin architecture. It supports prototype parsing, requirement structuring, automatic test case generation, and multi-format export, providing out-of-the-box AI assistance for QA engineers.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Prototype Parsing** | Automatically parse design prototypes from Modao, Lanhu, Figma, etc. |
| **Requirement Structuring** | Convert raw requirements into structured data |
| **Auto Test Case Generation** | AI-powered test case generation covering positive, negative, boundary scenarios |
| **Multi-format Export** | Export to Excel, JSON, Markdown and integrate with test management platforms |

### Quick Start

```bash
# Clone repository
git clone https://github.com/nandujia/DemandTest.git
cd DemandTest

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env to configure LLM_API_KEY

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Supported Platforms

| Platform | Status | Description |
|----------|--------|-------------|
| Modao | ✅ Supported | Chinese prototyping tool |
| Lanhu | 🚧 In Development | Design collaboration platform |
| Figma | 🚧 In Development | Online design tool |
| Axure | 📋 Planned | Professional prototyping tool |
| JSDesign | 📋 Planned | Chinese design tool |

### License

[MIT License](LICENSE)

---

<div align="center">

**Made with ❤️ by Testify AI Team**

**智测AI - 让测试更智能**

[GitHub](https://github.com/nandujia/DemandTest) | [Issues](https://github.com/nandujia/DemandTest/issues) | [Discussions](https://github.com/nandujia/DemandTest/discussions)

</div>
