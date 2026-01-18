"""
基础爬虫抽象类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """基础爬虫类"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            api_url: API 基础URL
            api_key: API密钥 (可选)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.session = None
    
    @abstractmethod
    def fetch_games(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        抓取游戏数据
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            游戏数据列表
        """
        pass
    
    @abstractmethod
    def parse_game_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析游戏数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            解析后的游戏数据
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证数据
        
        Args:
            data: 数据字典
            
        Returns:
            是否有效
        """
        return True

