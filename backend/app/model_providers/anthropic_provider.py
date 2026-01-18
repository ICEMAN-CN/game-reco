"""
Anthropic API 提供者
"""
import httpx
from typing import List, Dict, Optional, AsyncIterator
from app.model_providers.base_provider import BaseModelProvider

class AnthropicProvider(BaseModelProvider):
    """Anthropic API 提供者"""
    
    def __init__(self, model_name: str, base_url: str = "https://api.anthropic.com/v1", api_key: Optional[str] = None):
        super().__init__(model_name, base_url, api_key)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=300.0
        )
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Anthropic 不支持 embedding，抛出异常"""
        raise NotImplementedError("Anthropic API 不支持 embedding")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """聊天对话"""
        # 转换消息格式
        system_message = None
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation.append(msg)
        
        payload = {
            "model": self.model_name,
            "messages": conversation,
            "max_tokens": 4096
        }
        if system_message:
            payload["system"] = system_message
        
        if stream:
            async def stream_response():
                async with self.client.stream(
                    "POST",
                    "/messages",
                    json={**payload, "stream": True}
                ) as response:
                    async for event in response.aiter_lines():
                        if event.startswith("data: "):
                            import json
                            data = json.loads(event[6:])
                            if data["type"] == "content_block_delta":
                                yield data["delta"]["text"]
            return stream_response()
        else:
            response = await self.client.post("/messages", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

