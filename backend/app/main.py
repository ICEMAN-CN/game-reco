"""
FastAPI 应用入口
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import games, recommendations, chat, images

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Game Odyssey API",
    description="游戏推荐系统 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(games.router, prefix="/api/v1", tags=["games"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(images.router, prefix="/api/v1", tags=["images"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Game Odyssey API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

