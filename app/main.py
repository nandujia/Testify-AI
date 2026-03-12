"""
智测AI (Testify AI) - Main Entry
基于多模态大模型的开源自动化测试工具
Open-Source Automated Testing Tool Based on Multimodal LLM

版本 Version: 3.1.0-dev
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import analyze
from app.platforms.registry import PlatformRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 | Application lifecycle"""
    # 启动时 Startup
    print("\n" + "="*60)
    print("智测AI (Testify AI) v3.1.0-dev")
    print("基于多模态大模型的开源自动化测试工具")
    print("="*60)
    print(f"已注册平台 Registered platforms: {len(PlatformRegistry._platforms)}")
    for p in PlatformRegistry.list_platforms():
        print(f"  - {p['display_name']} ({p['display_name_en']})")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时 Shutdown
    print("\n" + "="*60)
    print("智测AI (Testify AI) shutting down...")
    print("="*60 + "\n")


app = FastAPI(
    title="智测AI (Testify AI)",
    description="""
## 基于多模态大模型的开源自动化测试工具

智测AI（Testify AI）支持原型解析、需求结构化、自动用例生成、多格式导出等全流程能力。

### 核心能力 Core Capabilities:
- 🔍 原型解析（墨刀、蓝湖、Figma）
- 📋 需求结构化
- 🤖 自动用例生成
- 📊 多格式导出（Excel、JSON、Markdown）

### 特性 Features:
- 🔍 协议级数据提取（Network Interception）
- 🤖 结构化LLM输出（Pydantic）
- 🧠 影子运行自学习（Few-Shot）
- ⚡ 全链路异步化（BackgroundTasks）

### 支持平台 Supported Platforms:
- 墨刀 Modao
- 蓝湖 Lanhu (开发中)
- Figma (开发中)
""",
    version="3.1.0-dev",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS 配置
# 生产环境请修改为具体的域名
# For production, change to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        # 生产环境添加你的域名
        # Add your domains for production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# 注册路由 Register routes
app.include_router(analyze.router, prefix="/api/v1", tags=["分析 Analysis"])


@app.get("/")
async def root():
    """根路径 | Root endpoint"""
    return {
        "name": "智测AI (Testify AI)",
        "version": "3.1.0-dev",
        "description": "基于多模态大模型的开源自动化测试工具 | Open-Source Automated Testing Tool Based on Multimodal LLM",
        "docs": "/docs",
        "capabilities": [
            "原型解析 | Prototype Parsing",
            "需求结构化 | Requirement Structuring",
            "自动用例生成 | Auto Test Case Generation",
            "多格式导出 | Multi-format Export"
        ],
        "platforms": PlatformRegistry.list_platforms()
    }


@app.get("/health")
async def health():
    """健康检查 | Health check"""
    return {
        "status": "healthy",
        "version": "3.1.0-dev",
        "platforms_registered": len(PlatformRegistry._platforms)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
