"""
Embedding 服务
"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.model_providers import LocalModelProvider, OpenAIProvider
from app.models.game import Game
from app.cleaners.game_cleaner import GameCleaner
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding 服务"""
    
    def __init__(self):
        # 根据配置创建模型提供者
        provider_type = settings.embedding_model_provider
        if provider_type == "local":
            self.provider = LocalModelProvider(
                model_name=settings.embedding_model_name,
                base_url=settings.embedding_base_url,
                api_key=settings.embedding_api_key
            )
        elif provider_type == "openai":
            self.provider = OpenAIProvider(
                model_name=settings.embedding_model_name,
                base_url=settings.embedding_base_url,
                api_key=settings.embedding_api_key
            )
        else:
            raise ValueError(f"不支持的 embedding 提供者: {provider_type}")
    
    async def embed_game(self, game: Game, db: Session) -> Tuple[List[float], str]:
        """
        为游戏生成 embedding（包含价格、评论、媒体评分）
        
        Args:
            game: 游戏对象
            db: 数据库会话
            
        Returns:
            (embedding_vector, chunk_text) 元组
        """
        from app.models.game_price import GamePrice
        from app.models.review import Review
        from app.models.game_media_score import GameMediaScore
        
        # 构建游戏基础数据
        game_data = {
            "title": game.title,
            "title_english": game.title_english,
            "description": game.description,
            "platforms": game.platforms or [],
            "tags": game.tags or [],
        }
        
        # 获取价格信息
        prices = db.query(GamePrice).filter(GamePrice.game_id == game.id).all()
        if prices:
            price_infes = []
            for price in prices:
                price_info = {
                    "platformName": price.platform_name,
                    "price": float(price.price) if price.price else 0,
                    "priceLowest": float(price.price_lowest) if price.price_lowest else None,
                    "beFree": price.is_free or False,
                }
                price_infes.append(price_info)
            game_data["price_infes"] = price_infes
        
        # 获取媒体评分
        media_scores = db.query(GameMediaScore).filter(GameMediaScore.game_id == game.id).all()
        if media_scores:
            media_score_list = []
            for media_score in media_scores:
                media_score_dict = {
                    "media_name": media_score.media_name,
                    "score": float(media_score.score) if media_score.score else None,
                    "total_score": float(media_score.total_score) if media_score.total_score else None,
                }
                media_score_list.append(media_score_dict)
            game_data["media_scores"] = media_score_list
        
        # 获取评论（最多5条，按原顺序 ordernum ASC）
        reviews = db.query(Review).filter(
            Review.game_id == game.id,
            Review.content.isnot(None),
            Review.content != ""
        ).order_by(Review.ordernum.asc()).limit(5).all()
        
        if reviews:
            review_list = []
            for review in reviews:
                review_list.append({
                    "content": review.content[:200] if review.content and len(review.content) > 200 else (review.content or "")
                })
            game_data["reviews"] = review_list
        
        # 使用 GameCleaner 提取 embedding 字段
        cleaner = GameCleaner()
        chunk_text = cleaner.extract_embedding_fields(game_data, max_reviews=5)
        
        # 生成 embedding
        embeddings = await self.provider.embed_texts([chunk_text])
        embedding_vector = embeddings[0] if embeddings else []
        
        return embedding_vector, chunk_text
    
    async def embed_games_batch(self, games: List[Game]) -> List[List[float]]:
        """批量生成 embedding（已废弃，使用 embed_game 逐个处理）"""
        texts = []
        for game in games:
            text_parts = []
            if game.title:
                text_parts.append(f"游戏名称: {game.title}")
            if game.description:
                text_parts.append(f"描述: {game.description}")
            if game.tags:
                text_parts.append(f"标签: {', '.join(game.tags)}")
            texts.append("\n".join(text_parts))
        
        return await self.provider.embed_texts(texts)

