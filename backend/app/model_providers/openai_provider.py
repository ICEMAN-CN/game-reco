"""
OpenAI API 提供者
"""
import httpx
from typing import List, Dict, Optional, AsyncIterator
from app.model_providers.base_provider import BaseModelProvider

class OpenAIProvider(BaseModelProvider):
    """OpenAI API 提供者"""
    
    def __init__(self, model_name: str, base_url: str = "https://api.openai.com/v1", api_key: Optional[str] = None):
        super().__init__(model_name, base_url, api_key)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=300.0
        )
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成 embedding"""
        response = await self.client.post(
            "/embeddings",
            json={
                "model": self.model_name,
                "input": texts
            }
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """聊天对话"""
        if stream:
            async def stream_response():
                async with self.client.stream(
                    "POST",
                    "/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            import json
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
            return stream_response()
        else:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": messages
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

