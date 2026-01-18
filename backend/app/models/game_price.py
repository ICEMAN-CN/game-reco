"""
游戏价格模型 (SQLAlchemy)
多平台价格信息
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class GamePrice(Base):
    """游戏价格模型"""
    __tablename__ = "game_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_name = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2))
    price_lowest = Column(Numeric(10, 2))
    price_original = Column(Numeric(10, 2))
    sale_price_rate = Column(Numeric(5, 2))
    is_free = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        {"schema": None},
    )

