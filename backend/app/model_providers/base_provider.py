"""
基础模型提供者接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator

class BaseModelProvider(ABC):
    """基础模型提供者"""
    
    def __init__(self, model_name: str, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本 embedding
        
        Args:
            texts: 文本列表
            
        Returns:
            embedding 向量列表
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """
        聊天对话
        
        Args:
            messages: 消息列表
            stream: 是否流式返回
            
        Returns:
            响应文本或流式迭代器
        """
        pass

