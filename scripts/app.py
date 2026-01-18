# 依赖：pip install mlx mlx-lm fastapi uvicorn pydantic langchain-core
import mlx.core as mx
from mlx_lm import load
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from langchain_core.embeddings import Embeddings
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 自定义 Embeddings 类（兼容 LangChain）
class QwenMLXEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "mlx-community/Qwen3-Embedding-4B-4bit-DWQ",
        instruct_prefix: str = "Instruct: Represent this sentence for searching relevant passages.\nQuery: ",
        batch_size: int = 16
    ):
        self.model, self.tokenizer = load(model_name)
        self.instruct_prefix = instruct_prefix
        self.batch_size = batch_size
        self.dimension = 2560  # Qwen3-Embedding-4B 默认维度
        
        # 检查模型结构
        logger.info(f"模型类型: {type(self.model)}")
        logger.info(f"模型属性: {dir(self.model)}")
        
        # 尝试获取内部模型（用于获取 hidden states 而非 logits）
        if hasattr(self.model, 'model'):
            logger.info(f"内部模型类型: {type(self.model.model)}")
            self.inner_model = self.model.model
        else:
            logger.warning("模型没有 'model' 属性，将尝试其他方式")
            self.inner_model = None
        
        logger.info(f"模型加载完成，预期维度: {self.dimension}")

    def _normalize(self, x: mx.array) -> mx.array:
        """手动实现 L2 归一化"""
        norm = mx.linalg.norm(x, axis=-1, keepdims=True)
        # 避免除零，添加小的 epsilon
        norm = mx.maximum(norm, 1e-8)
        return x / norm

    def _get_embedding(self, text: str) -> List[float]:
        full_text = self.instruct_prefix + text
        
        # 正确 tokenization：用 tokenizer.encode (返回 list[int])
        input_ids = self.tokenizer.encode(full_text)
        logger.debug(f"输入文本长度: {len(text)}, token 数量: {len(input_ids)}")
        
        input_ids_mx = mx.array([input_ids])  # shape (1, seq_len)
        logger.debug(f"input_ids shape: {input_ids_mx.shape}")

        # 获取 hidden states 而非 logits
        # mlx_lm 的模型结构: model(input_ids) 返回 logits
        # 需要使用 model.model(input_ids) 获取 hidden states
        if self.inner_model is not None:
            # 使用内部模型获取 hidden states
            hidden_states = self.inner_model(input_ids_mx)
            logger.debug(f"hidden_states type: {type(hidden_states)}")
            logger.debug(f"hidden_states shape: {hidden_states.shape}")
        else:
            # 如果没有内部模型，尝试其他方式
            # 某些模型可能有 embed 或 get_input_embeddings 方法
            if hasattr(self.model, 'embed_tokens'):
                # 尝试使用 embed_tokens（这是 token embedding 层）
                logger.info("使用 embed_tokens 方法")
                hidden_states = self.model.embed_tokens(input_ids_mx)
            else:
                # 最后尝试：直接使用模型输出（可能是 logits）
                logger.warning("无法获取 hidden states，使用模型输出")
                outputs = self.model(input_ids_mx)
                logger.debug(f"outputs shape: {outputs.shape}")
                
                # 检查输出维度，如果是 vocab_size，则无法使用
                if outputs.shape[-1] > 10000:  # vocab_size 通常很大
                    raise ValueError(
                        f"模型输出是 logits (shape: {outputs.shape})，无法用于 embedding。"
                        f"请检查模型结构或使用专门的 embedding 模型。"
                    )
                hidden_states = outputs
        
        # hidden_states shape: (batch_size, seq_len, hidden_dim)
        # 取最后一个 token 的 hidden state (last token pooling)
        if hidden_states.ndim == 3:
            last_hidden = hidden_states[:, -1, :]  # shape: (1, hidden_dim)
        elif hidden_states.ndim == 2:
            last_hidden = hidden_states[-1:, :]  # shape: (1, hidden_dim)
        else:
            raise ValueError(f"Unexpected hidden_states ndim: {hidden_states.ndim}")
        
        logger.debug(f"last_hidden shape: {last_hidden.shape}")
        
        # 验证 hidden_dim
        if last_hidden.shape[-1] != self.dimension:
            logger.error(
                f"hidden_dim 不匹配: 期望 {self.dimension}, 实际 {last_hidden.shape[-1]}. "
                f"hidden_states shape: {hidden_states.shape}"
            )
            # 更新实际维度
            actual_dim = last_hidden.shape[-1]
            logger.warning(f"将使用实际维度 {actual_dim} 替代预期维度 {self.dimension}")
            self.dimension = actual_dim
        
        # 手动归一化
        normalized = self._normalize(last_hidden)
        logger.debug(f"normalized shape: {normalized.shape}")
        
        # 转换为 Python list
        # normalized shape: (1, hidden_dim)
        # tolist() 返回 [[...]]，需要取 [0]
        embedding_nested = normalized.tolist()
        
        if isinstance(embedding_nested, list) and len(embedding_nested) > 0:
            if isinstance(embedding_nested[0], list):
                # 正常情况：[[...]]
                embedding = embedding_nested[0]
            else:
                # 已经是 1D list
                embedding = embedding_nested
        else:
            raise ValueError(f"Unexpected embedding format: {type(embedding_nested)}")
        
        logger.debug(f"成功生成 embedding，维度: {len(embedding)}")
        return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            for j, text in enumerate(batch):
                logger.info(f"处理文本 {i+j+1}/{len(texts)}，长度: {len(text)}")
                embeddings.append(self._get_embedding(text))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._get_embedding(text)

# FastAPI app
app = FastAPI(title="Qwen3 Embedding API", description="Local API for Qwen3-Embedding-4B on Mac")

# 全局初始化（加载一次模型）
embeddings = QwenMLXEmbeddings()

class EmbedRequest(BaseModel):
    texts: List[str]

@app.post("/embed")
async def embed(request: EmbedRequest):
    logger.info(f"收到请求，文本数量: {len(request.texts)}")
    for i, text in enumerate(request.texts):
        logger.debug(f"  文本 {i+1} 长度: {len(text)}, 前100字符: {text[:100]}")
    
    try:
        embs = embeddings.embed_documents(request.texts)
        
        # 验证返回的 embeddings
        for i, emb in enumerate(embs):
            if isinstance(emb, list) and len(emb) != embeddings.dimension:
                logger.error(f"  结果 {i+1} 维度错误: {len(emb)} != {embeddings.dimension}")
        
        return {"embeddings": embs, "dimension": embeddings.dimension}
    except Exception as e:
        logger.exception(f"生成 embedding 失败")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
