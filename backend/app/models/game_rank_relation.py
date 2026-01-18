"""
游戏-榜单关联模型 (SQLAlchemy)
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class GameRankRelation(Base):
    """游戏-榜单关联模型"""
    __tablename__ = "game_rank_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    rank_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('game_id', 'rank_id', name='uq_game_rank'),
        {"schema": None},
    )

