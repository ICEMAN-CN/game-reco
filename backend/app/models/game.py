"""
游戏数据模型 (SQLAlchemy)
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, Boolean, ARRAY, BigInteger, JSON
from sqlalchemy.sql import func
from app.database import Base


class Game(Base):
    """游戏模型"""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    title_english = Column(String(255))
    developer_name = Column(String(255))
    publisher_name = Column(String(255))
    description = Column(Text)
    description_html = Column(Text)
    cover_image_url = Column(Text)
    thumbnail_url = Column(Text)
    horizontal_image_url = Column(Text)
    platforms = Column(ARRAY(String))
    platform_ids = Column(ARRAY(Integer))
    publish_date = Column(Date, index=True)
    publish_timestamp = Column(BigInteger)
    user_score = Column(Numeric(3, 1), index=True)
    score_users_count = Column(Integer)
    playeds_count = Column(Integer)
    want_plays_count = Column(Integer)
    tags = Column(ARRAY(String))
    steam_game_id = Column(String(50))
    steam_praise_rate = Column(Numeric(3, 2))
    steam_header_image = Column(Text)
    is_free = Column(Boolean, default=False)
    price = Column(Numeric(10, 2))
    price_original = Column(Numeric(10, 2))
    device_requirement_html = Column(Text)
    theme_color = Column(String(50))
    hot_value = Column(String(50))
    be_official_chinese_enable = Column(Boolean)
    play_hours_caption = Column(String(50))
    real_players_score = Column(Numeric(3, 1))
    real_players_count = Column(Integer)
    source = Column(String(50), default="external")
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
