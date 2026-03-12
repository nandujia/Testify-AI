# DemandTest Platform 项目结构说明

## 目录结构

```
demand-test-platform/
├── README.md                    # 项目说明文档
├── LICENSE                      # 许可证
├── Makefile                     # 常用命令
├── docker-compose.yml           # Docker编排配置
├── .gitignore                   # Git忽略配置
│
├── backend/                     # 后端代码目录
│   ├── Dockerfile              # 后端Docker构建文件
│   ├── requirements.txt        # Python依赖
│   ├── .env.example            # 环境变量示例
│   │
│   ├── app/                    # 主应用代码
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── main.py             # 应用入口
│   │   │
│   │   ├── api/                # API接口层
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 对话接口 (v3.0)
│   │   │   ├── config.py       # 配置接口 (v3.0)
│   │   │   └── learning.py     # 学习接口 (v3.0)
│   │   │
│   │   ├── core/               # 核心模块 (v3.0)
│   │   │   ├── __init__.py
│   │   │   ├── intent_agent.py # 意图识别
│   │   │   ├── orchestrator.py # 调度中心
│   │   │   └── session.py      # 会话管理
│   │   │
│   │   ├── llm/                # LLM适配层 (v3.0)
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 抽象基类
│   │   │   ├── factory.py      # 工厂模式
│   │   │   └── custom.py       # 自定义模型
│   │   │
│   │   ├── skills/             # 技能系统 (v3.0)
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 技能基类
│   │   │   ├── registry.py     # 技能注册
│   │   │   ├── analyze_skill.py         # 分析技能
│   │   │   ├── demand_extractor_skill.py # 需求提取
│   │   │   ├── full_extractor.py         # 完整提取器
│   │   │   ├── testcase_skill.py         # 用例生成
│   │   │   ├── export_skill.py           # 导出技能
│   │   │   ├── qa_skill.py               # 问答技能
│   │   │   └── knowledge_skill.py        # 知识库技能
│   │   │
│   │   ├── knowledge/          # 知识库模块 (v3.0)
│   │   │   ├── __init__.py
│   │   │   ├── rag.py          # RAG知识库
│   │   │   ├── embeddings.py   # 嵌入引擎
│   │   │   ├── vector_store.py # 向量存储
│   │   │   └── document.py     # 文档处理
│   │   │
│   │   ├── services/           # 服务层
│   │   │   ├── __init__.py
│   │   │   ├── config_service.py   # 配置服务 (v3.0)
│   │   │   ├── learning_service.py # 学习服务 (v3.0)
│   │   │   ├── crawler/            # 爬虫服务
│   │   │   │   └── modao_crawler.py
│   │   │   ├── extractor/      # 导出服务
│   │   │   └── generator/      # 生成服务
│   │   │
│   │   ├── models/             # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── llm_config.py   # LLM配置模型 (v3.0)
│   │   │   └── schemas.py      # Pydantic模型
│   │   │
│   │   └── utils/              # 工具函数
│   │       └── helpers.py
│   │
│   ├── data/                   # 数据存储
│   │   ├── config/             # 配置数据
│   │   ├── sessions/           # 会话数据
│   │   ├── knowledge/          # 知识库数据
│   │   └── learning/           # 学习数据
│   │
│   └── exports/                # 导出文件目录
│
├── frontend/                   # 前端代码目录
│   ├── package.json
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── ...
│   └── dist/                   # 构建输出
│
└── docs/                       # 文档目录
    ├── ARCHITECTURE.md         # 架构说明
    └── API.md                  # API文档
```

## 模块说明

### 核心模块 (backend/app/core/)

| 文件 | 说明 |
|------|------|
| `intent_agent.py` | 意图识别，理解用户消息目的 |
| `orchestrator.py` | 调度中心，协调技能执行 |
| `session.py` | 会话管理，维护对话状态 |

### 技能系统 (backend/app/skills/)

| 文件 | 说明 |
|------|------|
| `base.py` | 技能基类，定义标准接口 |
| `registry.py` | 技能注册表，管理技能实例 |
| `analyze_skill.py` | 分析原型链接 |
| `demand_extractor_skill.py` | 需求提取 |
| `testcase_skill.py` | 测试用例生成 |
| `export_skill.py` | 文件导出 |

### LLM适配层 (backend/app/llm/)

| 文件 | 说明 |
|------|------|
| `base.py` | LLM抽象基类 |
| `factory.py` | 工厂模式创建LLM实例 |
| `custom.py` | 自定义模型支持 |

### API接口 (backend/app/api/)

| 文件 | 说明 |
|------|------|
| `chat.py` | 对话接口，处理用户消息 |
| `config.py` | 配置接口，管理应用配置 |
| `learning.py` | 学习接口，记录反馈 |

## 运行方式

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑.env配置
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### Docker部署

```bash
docker-compose up -d
# 访问 http://localhost:8080
```

## 环境变量

详见 `backend/.env.example`
