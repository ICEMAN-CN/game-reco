"""
游戏评论模型 (SQLAlchemy)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ARRAY, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    """游戏评论模型"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    external_comment_id = Column(Integer, unique=True, index=True)
    user_id = Column(Integer)
    user_name = Column(String(255))
    author_user_id = Column(Integer)
    author_name = Column(String(255))
    author_head_image_url = Column(Text)
    content = Column(Text, nullable=False)
    content_html = Column(Text)
    rating = Column(Numeric(3, 1), index=True)
    sentiment = Column(String(50))
    praises_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    treads_count = Column(Integer, default=0)
    publish_time = Column(DateTime)
    ordernum = Column(Integer, index=True)
    game_label_platform_names = Column(ARRAY(String))
    content_user_label_type_names = Column(ARRAY(String))
    source = Column(String(50), default="external")
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
