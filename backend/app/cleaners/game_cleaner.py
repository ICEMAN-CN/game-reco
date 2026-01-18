"""
游戏数据清洗模块
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class GameCleaner:
    """游戏数据清洗器"""
    
    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗游戏数据
        
        Args:
            data: 原始数据
            
        Returns:
            清洗后的数据
        """
        cleaned = data.copy()
        
        # 字段标准化
        cleaned = self._normalize_fields(cleaned)
        
        # 数据验证
        cleaned = self._validate_data(cleaned)
        
        # 缺失值处理
        cleaned = self._handle_missing_values(cleaned)
        
        return cleaned
    
    def _normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """字段标准化"""
        # 确保 platforms 是列表
        if "platforms" in data and not isinstance(data["platforms"], list):
            data["platforms"] = []
        
        # 确保 tags 是列表
        if "tags" in data and not isinstance(data["tags"], list):
            data["tags"] = []
        
        # 标准化评分 (0-10 范围)
        if "user_score" in data and data["user_score"] is not None:
            score = float(data["user_score"])
            if score < 0:
                data["user_score"] = None
            elif score > 10:
                data["user_score"] = 10.0
        
        # 标准化价格
        if "price" in data and data["price"] is not None:
            price = float(data["price"])
            if price < 0:
                data["price"] = 0.0
        
        return data
    
    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据验证"""
        # 必须有 external_id 和 title
        if not data.get("external_id") or not data.get("title"):
            raise ValueError("external_id 和 title 是必填字段")
        
        return data
    
    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理缺失值"""
        # 设置默认值
        defaults = {
            "source": "external",
            "is_free": False,
            "platforms": [],
            "tags": []
        }
        
        for key, value in defaults.items():
            if key not in data or data[key] is None:
                data[key] = value
        
        return data
    
    def extract_embedding_fields(self, data: Dict[str, Any], max_reviews: int = 5) -> str:
        """
        提取用于embedding的字段组合
        
        Args:
            data: 游戏数据
            max_reviews: 最多使用的评论数量
            
        Returns:
            组合后的文本
        """
        parts = []
        
        # 游戏名称
        title = data.get("title", "")
        title_english = data.get("title_english", "")
        if title:
            parts.append(f"游戏名称: {title}")
        if title_english:
            parts.append(f"英文名称: {title_english}")
        
        # 平台
        platforms = data.get("platforms", [])
        if platforms:
            parts.append(f"支持平台: {', '.join(platforms)}")
        
        # 标签
        tags = data.get("tags", [])
        if tags:
            parts.append(f"标签: {', '.join(tags)}")
        
        # 价格信息
        price_infes = data.get("price_infes", [])
        if price_infes:
            price_parts = []
            for price_info in price_infes:
                platform = price_info.get("platformName", "")
                price = price_info.get("price", 0)
                price_lowest = price_info.get("priceLowest", 0)
                is_free = price_info.get("beFree", False)
                
                if is_free:
                    price_parts.append(f"{platform}平台: 免费")
                else:
                    price_str = f"{platform}平台: ¥{price}"
                    if price_lowest and price_lowest < price:
                        price_str += f", 史低¥{price_lowest}"
                    price_parts.append(price_str)
            
            if price_parts:
                parts.append(f"价格信息: {'; '.join(price_parts)}")
        
        # 描述
        description = data.get("description", "")
        if description:
            # 限制描述长度
            if len(description) > 500:
                description = description[:500] + "..."
            parts.append(f"游戏描述: {description}")
        
        # 媒体评分
        media_scores = data.get("media_scores", [])
        if media_scores:
            media_parts = []
            for media_score in media_scores:
                media_name = media_score.get("media_name", "")
                score = media_score.get("score")
                total_score = media_score.get("total_score")
                
                if media_name and score is not None:
                    if total_score:
                        # 格式化评分：9.2/10 或 92/100
                        if total_score == 10:
                            score_str = f"{float(score):.1f}/10"
                        elif total_score == 100:
                            score_str = f"{float(score):.0f}/100"
                        else:
                            score_str = f"{float(score):.1f}/{float(total_score):.0f}"
                    else:
                        score_str = f"{float(score):.1f}"
                    media_parts.append(f"{media_name} {score_str}")
            
            if media_parts:
                parts.append(f"媒体评分: {', '.join(media_parts)}")
        
        # 评论摘要
        reviews = data.get("reviews", [])
        if reviews:
            review_texts = []
            for review in reviews[:max_reviews]:
                content = review.get("content", "")
                if content:
                    # 限制每条评论长度
                    if len(content) > 200:
                        content = content[:200] + "..."
                    review_texts.append(content)
            
            if review_texts:
                parts.append(f"用户评论: {' | '.join(review_texts)}")
        
        return "\n".join(parts)

