"""
本地模型提供者 (Ollama, vLLM 等)
"""
import httpx
import logging
import json
from typing import List, Dict, Optional, AsyncIterator
from app.model_providers.base_provider import BaseModelProvider

logger = logging.getLogger(__name__)

class LocalModelProvider(BaseModelProvider):
    """本地模型提供者"""
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", api_key: Optional[str] = None):
        super().__init__(model_name, base_url, api_key)
        self.client = httpx.AsyncClient(base_url=base_url, timeout=300.0)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成 embedding (MLX本地API)"""
        embeddings = []
        # 逐个处理，避免OOM
        for text in texts:
            try:
                logger.debug(f"请求 embedding，文本长度: {len(text)}")
                
                # 使用 /embed 端点，格式: {"texts": [text]}
                response = await self.client.post(
                    "/embed",
                    json={
                        "texts": [text]  # 单个文本，但API期望列表格式
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # 调试：记录响应结构
                debug_info = json.dumps(data, ensure_ascii=False)[:500]
                logger.debug(f"API 响应: {debug_info}")
                
                # 响应格式: {"embeddings": [[...]], "dimension": 2560}
                result_embeddings = data.get("embeddings", [])
                expected_dim = data.get("dimension", 2560)
                
                if not result_embeddings:
                    raise Exception(f"API 返回的 embeddings 为空。响应: {debug_info}")
                
                # 确保 result_embeddings 是列表
                if not isinstance(result_embeddings, list):
                    raise Exception(
                        f"API 返回的 embeddings 格式错误，期望列表，得到: {type(result_embeddings)}。"
                        f"响应: {debug_info}"
                    )
                
                if len(result_embeddings) == 0:
                    raise Exception(f"API 返回的 embeddings 列表为空。响应: {debug_info}")
                
                # 获取第一个 embedding（因为只传了一个文本）
                embedding = result_embeddings[0]
                
                # 详细日志
                logger.debug(f"embedding type: {type(embedding)}, len: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
                
                # 验证 embedding 是列表
                if not isinstance(embedding, list):
                    raise Exception(
                        f"Embedding 不是列表格式，得到: {type(embedding).__name__}。"
                        f"响应预览: {debug_info}"
                    )
                
                # 检查是否是嵌套列表
                if len(embedding) > 0 and isinstance(embedding[0], list):
                    raise Exception(
                        f"Embedding 是嵌套列表结构，API 返回格式错误。"
                        f"第一层长度: {len(embedding)}, 第二层长度: {len(embedding[0])}。"
                        f"期望: 单层数字列表，维度 {expected_dim}。"
                    )
                
                # 验证维度
                embedding_len = len(embedding)
                
                if embedding_len != expected_dim:
                    # 详细错误信息，帮助诊断问题
                    error_msg = (
                        f"Embedding 维度不匹配: 期望 {expected_dim}，实际 {embedding_len}。\n"
                        f"可能原因：\n"
                        f"1. API 返回了所有 token 的 embedding（如果是 {expected_dim} 的倍数: {embedding_len // expected_dim if embedding_len % expected_dim == 0 else '否'}）\n"
                        f"2. 模型输出格式错误\n"
                        f"3. 文本长度: {len(text)} 字符\n"
                        f"响应预览: {debug_info}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # 验证所有元素都是数字
                if not all(isinstance(x, (int, float)) for x in embedding[:100]):  # 只检查前100个，提高性能
                    non_numeric = [type(x).__name__ for x in embedding[:10] if not isinstance(x, (int, float))]
                    raise Exception(f"Embedding 包含非数字元素。前10个非数字类型: {non_numeric[:5]}")
                
                logger.debug(f"成功获取 embedding，维度: {embedding_len}")
                embeddings.append(embedding)
                
            except httpx.ConnectError as e:
                error_msg = (
                    f"无法连接到 Embedding 服务 ({self.base_url})。"
                    f"请确保 Embedding 服务正在运行。"
                    f"错误详情: {str(e)}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP 错误 {e.response.status_code}: {e.response.text[:200]}")
            except Exception as e:
                raise Exception(f"Embedding 生成失败: {str(e)}")
        return embeddings
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> AsyncIterator[str] | str:
        """聊天对话 (Ollama)"""
        if stream:
            async def stream_response():
                # Ollama 流式 API
                async with self.client.stream(
                    "POST",
                    "/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                                elif "content" in data:
                                    yield data["content"]
                            except json.JSONDecodeError:
                                continue
            return stream_response()
        else:
            # Ollama 非流式 API
            try:
                response = await self.client.post(
                    "/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            except httpx.ConnectError as e:
                error_msg = (
                    f"无法连接到 Ollama 服务 ({self.base_url})。"
                    f"请确保 Ollama 服务正在运行。"
                    f"错误详情: {str(e)}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            except httpx.HTTPStatusError as e:
                error_msg = f"Ollama API 错误 {e.response.status_code}: {e.response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Ollama 聊天请求失败: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
