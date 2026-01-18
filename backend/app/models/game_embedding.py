"""
游戏 Embedding 模型
"""
from sqlalchemy import Column, Integer, Text, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base

# 注意: 需要安装 pgvector 扩展
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    # 如果 pgvector 未安装，使用 Text 类型作为后备
    # 注意: 这种情况下向量检索功能将不可用
    Vector = Text
    VECTOR_AVAILABLE = False


class GameEmbedding(Base):
    """游戏 Embedding 模型"""
    __tablename__ = "game_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, index=True)
    embedding_vector = Column(Vector(2560))  # Qwen3-Embedding-4B 是 2560 维
    chunk_text = Column(Text)
    metadata_json = Column(JSON)  # 重命名：metadata 是 SQLAlchemy 保留字
    model_name = Column(String(255), default="qwen3-embedding-4b")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

