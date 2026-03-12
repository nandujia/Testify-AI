# DemandTest Platform - 需求提取与测试用例生成平台

<div align="center">

**一款智能测试用例生成平台 - 自然对话驱动**

分析原型链接 → 生成测试用例 → 导出文件

[![Version](https://img.shields.io/badge/version-3.0.0--dev-orange.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)]()

</div>

---

## ⚠️ 开发状态说明

**当前版本：v3.0.0-dev**

### 已完成功能 ✅

| 功能 | 状态 | 说明 |
|------|------|------|
| 原型目录提取 | ✅ 完成 | 支持97个页面的目录结构提取 |
| 页面导航 | ✅ 完成 | 点击目录切换页面 |
| 截图保存 | ✅ 完成 | 页面截图功能 |
| 多LLM适配 | ✅ 完成 | GLM/GPT/Qwen/ERNIE/自定义模型 |
| 意图识别 | ✅ 完成 | 规则匹配 + LLM分析 |
| 技能系统 | ✅ 完成 | 基础技能框架 |
| 自学习机制 | ✅ 完成 | 错误记录和优化机制 |
| 会话管理 | ✅ 完成 | 多会话支持 |

### 待解决问题 ❌

| 问题 | 状态 | 说明 |
|------|------|------|
| 需求内容提取 | ❌ 未完成 | 墨刀页面使用图片/Canvas渲染，无法直接提取文字内容 |
| OCR识别 | ❌ 待集成 | 本地OCR工具(PaddleOCR)存在兼容性问题，需要配置API Key |

### 解决方案

**方式1：配置视觉模型API Key**
```bash
# 智谱AI (推荐，有免费额度)
export ZHIPU_API_KEY="your-api-key"

# 或 OpenAI
export OPENAI_API_KEY="your-api-key"
```

**方式2：手动提供需求内容**
用户可直接提供需求文字，系统基于内容生成测试用例。

---

## ✨ v3.0 设计目标

### 🗣️ 自然对话交互

像聊天一样使用，无需记忆命令：

```
用户: 分析这个墨刀链接 https://modao.cc/xxx
AI: 已分析墨刀原型，提取 97 个页面...

用户: 生成VIP模块的测试用例
AI: 已为「VIP模块」生成 15 条测试用例...

用户: 导出Excel
AI: 已导出到 test_cases_20260312.xlsx
```

### 🤖 智能调度系统

| 模块 | 说明 | 状态 |
|------|------|------|
| **Intent Agent** | 意图识别，理解用户想做什么 | ✅ |
| **Orchestrator** | 调度中心，协调各技能执行 | ✅ |
| **Skills** | 技能系统，按需调用爬虫/生成/导出 | ✅ |

### 🧠 自我学习优化

- **错误记录**：自动记录执行失败 ✅
- **用户纠正**：学习用户反馈 ✅
- **最佳实践**：积累可复用经验 ✅
- **自动优化**：重复问题自动提示解决方案 ✅

### 🔧 本地化配置

前端可视化配置：

| 配置项 | 说明 |
|--------|------|
| 导出路径 | 自定义文件导出目录 |
| LLM 模型 | 多模型配置、自定义模型 |
| 知识库 | 启用/禁用、存储路径 |
| 主题/语言 | 界面个性化 |

### 🌐 多 LLM 支持

| 类型 | 模型 | 状态 |
|------|------|------|
| 内置 | GLM / GPT / Qwen / ERNIE | ✅ |
| 自定义 | Ollama / vLLM / DeepSeek / Moonshot | ✅ |
| 完全自定义 | 任意 OpenAI 兼容 API | ✅ |

---

## 🚀 快速开始

### Docker 部署

```bash
git clone https://github.com/nandujia/DemandTest.git
cd DemandTest
docker-compose up -d
# 访问 http://localhost:8080
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置 LLM_API_KEY
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

---

## 📁 项目结构

```
backend/app/
├── core/                    # 核心模块 (v3.0)
│   ├── intent_agent.py     # 意图识别
│   ├── orchestrator.py     # 调度中心
│   └── session.py          # 会话管理
│
├── skills/                  # 技能系统 (v3.0)
│   ├── base.py             # 技能基类
│   ├── registry.py         # 技能注册表
│   ├── analyze_skill.py    # 分析技能
│   ├── demand_extractor_skill.py # 需求提取技能
│   ├── testcase_skill.py   # 测试用例技能
│   ├── export_skill.py     # 导出技能
│   ├── qa_skill.py         # 问答技能
│   └── knowledge_skill.py  # 知识库技能
│
├── llm/                     # LLM 适配层
│   ├── base.py             # 抽象基类
│   ├── factory.py          # 工厂模式
│   ├── glm.py              # 智谱 GLM
│   ├── gpt.py              # OpenAI
│   ├── qwen.py             # 通义千问
│   ├── ernie.py            # 文心一言
│   └── custom.py           # 自定义模型
│
├── knowledge/               # 知识库模块
│   ├── rag.py              # RAG 知识库
│   ├── embeddings.py       # 嵌入引擎
│   └── vector_store.py     # 向量存储
│
├── services/
│   ├── config_service.py   # 配置服务 (v3.0)
│   ├── learning_service.py # 学习服务 (v3.0)
│   ├── bug_fix_service.py  # 自动修复服务
│   ├── crawler/            # 爬虫服务
│   │   └── modao_crawler.py # 墨刀爬虫
│   ├── extractor/          # 导出服务
│   └── generator/          # 用例生成
│
├── api/
│   ├── chat.py             # 对话 API (v3.0)
│   ├── config.py           # 配置 API (v3.0)
│   ├── learning.py         # 学习 API (v3.0)
│   └── ...
│
└── models/
    ├── llm_config.py       # LLM 配置模型 (v3.0)
    └── schemas.py
```

---

## 📖 使用指南

### 分析原型

```
用户: 分析这个墨刀链接 https://modao.cc/community/xxx
```

支持平台：墨刀、蓝湖、Axure、幕客、Figma、即时设计

**当前状态**：
- ✅ 目录提取：成功提取97个页面名称
- ❌ 内容提取：待完成（需要OCR支持）

### 生成测试用例

```
用户: 生成测试用例
用户: 生成登录模块的测试用例
用户: 只生成正向和逆向用例
```

### 导出文件

```
用户: 导出Excel
用户: 导出Markdown格式
```

### 知识库增强

```
用户: 上传这份需求文档 [文件]
用户: 根据文档生成登录测试用例
```

---

## 🛠️ API 文档

### 对话接口

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "分析 https://modao.cc/xxx",
  "session_id": "可选"
}
```

### LLM 配置

```http
GET  /api/v1/config/llm/profiles
POST /api/v1/config/llm/profiles
PUT  /api/v1/config/llm/profiles/{id}
DELETE /api/v1/config/llm/profiles/{id}
POST /api/v1/config/llm/profiles/{id}/test
```

---

## ⚙️ 配置说明

### 环境变量

```bash
# LLM 配置
LLM_API_TYPE=glm              # glm/gpt/qwen/ernie/custom
LLM_MODEL_NAME=glm-4
LLM_API_KEY=your-api-key
LLM_BASE_URL=                 # 自定义 API 地址

# 视觉模型 (用于OCR)
ZHIPU_API_KEY=                # 智谱AI (GLM-4V)
OPENAI_API_KEY=               # OpenAI (GPT-4V)

# 知识库
KB_ENABLED=true
KB_STORAGE_DIR=./data/knowledge

# 学习系统
LEARNING_ENABLED=true
LEARNING_STORAGE_DIR=./data/learning

# 会话
SESSION_TIMEOUT=3600
```

### 自定义 LLM 配置

通过 API 或前端添加自定义模型：

```json
{
  "name": "Ollama-Llama3",
  "base_url": "http://localhost:11434/v1",
  "model_name": "llama3",
  "protocol": "openai_compatible",
  "api_key": ""
}
```

---

## 🔧 核心技术

### 意图识别流程

```
用户消息 → 规则匹配（快速）→ LLM 分析（精准）→ 意图结果
```

### 技能调度流程

```
意图 → 路由到技能 → 参数验证 → 执行 → 响应生成
```

### 需求提取流程

```
原型页面 → Playwright加载 → 目录提取 ✅
                         → 页面导航 ✅
                         → 截图保存 ✅
                         → OCR识别 ❌ (待完成)
                         → 需求分析 → 用例生成
```

### 自我学习机制

```
错误/纠正 → 记录 → 分析 → 最佳实践 → 自动优化
```

---

## 📊 当前性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 目录提取准确率 | 100% | 97个页面全部识别 |
| 页面导航成功率 | 100% | 点击切换正常 |
| 截图成功率 | 100% | 全页面截图正常 |
| 需求内容提取 | 0% | 待OCR支持 |

---

## 🗓️ 开发计划

### v3.0.1 (计划中)

- [ ] 集成视觉模型API进行OCR识别
- [ ] 支持GLM-4V / GPT-4V视觉模型
- [ ] 完善需求内容提取流程
- [ ] 优化测试用例生成质量

### v3.0.2 (计划中)

- [ ] 前端界面开发
- [ ] 可视化配置面板
- [ ] 导出路径配置
- [ ] 多模型切换UI

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

**v3.0.0-dev** | Made with ❤️ by nandujia

需求提取功能开发中，欢迎贡献代码或提供建议！

</div>
