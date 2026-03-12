"""
FastAPI 主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import crawl, generate, export, agent, knowledge, chat, config, learning

app = FastAPI(
    title="DemandTest Platform",
    description="需求提取与测试用例生成平台 - 自然对话驱动",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(crawl.router, prefix="/api/v1", tags=["爬取"])
app.include_router(generate.router, prefix="/api/v1", tags=["生成"])
app.include_router(export.router, prefix="/api/v1", tags=["导出"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(config.router, prefix="/api/v1/config", tags=["配置"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["学习"])


@app.get("/")
async def root():
    return {
        "name": "DemandTest Platform",
        "version": "3.0.0",
        "status": "running",
        "features": [
            "自然对话交互",
            "多LLM适配（GLM/GPT/Qwen/ERNIE/自定义）",
            "Orchestrator智能调度",
            "Skill技能系统",
            "RAG知识库",
            "自我学习优化",
            "本地化配置"
        ]
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
