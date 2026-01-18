"""
游戏媒体评分模型 (SQLAlchemy)
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class GameMediaScore(Base):
    """游戏媒体评分模型"""
    __tablename__ = "game_media_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    media_name = Column(String(255), nullable=False)
    score = Column(Numeric(5, 2))
    total_score = Column(Numeric(5, 2))
    content_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('game_id', 'media_name', name='uq_game_media'),
        {"schema": None},
    )

