-- 创建 game_embeddings 表 (用于 RAG 向量检索)
-- 需要先安装 pgvector 扩展

CREATE TABLE IF NOT EXISTS game_embeddings (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    embedding_vector vector(2560),  -- 根据模型调整维度 (Qwen3-Embedding-4B 是 2560 维)
    chunk_text TEXT,
    metadata JSONB,
    model_name VARCHAR(255) DEFAULT 'qwen3-embedding-4b',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_game_embeddings_game_id ON game_embeddings(game_id);
CREATE INDEX IF NOT EXISTS idx_game_embeddings_model ON game_embeddings(model_name);

-- 向量索引 (使用 ivfflat 加速相似度搜索)
-- 注意: 需要先有数据才能创建向量索引
-- CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings 
-- USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE game_embeddings IS '游戏 Embedding 向量表，用于 RAG 检索';
COMMENT ON COLUMN game_embeddings.embedding_vector IS '游戏文本的 embedding 向量';
COMMENT ON COLUMN game_embeddings.chunk_text IS '用于生成 embedding 的原始文本';

