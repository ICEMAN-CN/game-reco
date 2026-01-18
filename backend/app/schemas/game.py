"""
游戏数据 Schema (Pydantic)
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class GameBase(BaseModel):
    """游戏基础 Schema"""
    external_id: int = Field(..., description="外部数据源游戏ID")
    title: str = Field(..., description="游戏名称")
    title_english: Optional[str] = Field(None, description="英文名称")
    developer_name: Optional[str] = Field(None, description="开发商")
    publisher_name: Optional[str] = Field(None, description="发行商")
    description: Optional[str] = Field(None, description="游戏描述")
    description_html: Optional[str] = Field(None, description="HTML 描述")
    cover_image_url: Optional[str] = Field(None, description="封面图URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    horizontal_image_url: Optional[str] = Field(None, description="横版图URL")
    platforms: Optional[List[str]] = Field(None, description="平台列表")
    platform_ids: Optional[List[int]] = Field(None, description="平台ID列表")
    publish_date: Optional[date] = Field(None, description="发布日期")
    publish_timestamp: Optional[int] = Field(None, description="发布时间戳")
    user_score: Optional[Decimal] = Field(None, description="用户评分")
    score_users_count: Optional[int] = Field(None, description="评分用户数")
    playeds_count: Optional[int] = Field(None, description="玩过人数")
    want_plays_count: Optional[int] = Field(None, description="想玩人数")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    steam_game_id: Optional[str] = Field(None, description="Steam 游戏ID")
    steam_praise_rate: Optional[Decimal] = Field(None, description="Steam 好评率")
    steam_header_image: Optional[str] = Field(None, description="Steam 头图")
    is_free: bool = Field(False, description="是否免费")
    price: Optional[Decimal] = Field(None, description="价格")
    price_original: Optional[Decimal] = Field(None, description="原价")
    device_requirement_html: Optional[str] = Field(None, description="配置要求HTML")
    source: str = Field("external", description="数据来源")


class GameCreate(GameBase):
    """创建游戏 Schema"""
    raw_data: Optional[dict] = Field(None, description="原始JSON数据")


class GameUpdate(BaseModel):
    """更新游戏 Schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    user_score: Optional[Decimal] = None
    # ... 其他可更新字段


class GameResponse(GameBase):
    """游戏响应 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    """游戏列表响应"""
    items: List[GameResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
