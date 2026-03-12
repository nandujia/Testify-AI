"""
DemandTest Platform - Main Entry
低侵入式产研数据转换器 | Non-Intrusive Product-Research Data Transformer

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
    print("DemandTest Platform v3.1.0-dev")
    print("低侵入式产研数据转换器")
    print("="*60)
    print(f"已注册平台 Registered platforms: {len(PlatformRegistry._platforms)}")
    for p in PlatformRegistry.list_platforms():
        print(f"  - {p['display_name']} ({p['display_name_en']})")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时 Shutdown
    print("\n" + "="*60)
    print("DemandTest Platform shutting down...")
    print("="*60 + "\n")


app = FastAPI(
    title="DemandTest Platform",
    description="""
## 低侵入式产研数据转换器 | Non-Intrusive Product-Research Data Transformer

智能测试用例生成平台，支持墨刀、蓝湖、Figma等原型设计工具。

### 核心特性 Core Features:
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
        "name": "DemandTest Platform",
        "version": "3.1.0-dev",
        "description": "低侵入式产研数据转换器 | Non-Intrusive Product-Research Data Transformer",
        "docs": "/docs",
        "features": [
            "协议级数据提取 | Protocol-level data extraction",
            "结构化LLM输出 | Structured LLM output",
            "影子运行自学习 | Shadow learning",
            "全链路异步化 | Full async pipeline"
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
