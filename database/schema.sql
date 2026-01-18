-- Game Odyssey 数据库完整 Schema
-- 包含所有表的创建语句

-- 扩展
\i database/init/001_init_extensions.sql

-- 游戏表
\i database/init/002_create_games_table.sql

-- 索引
\i database/init/003_create_indexes.sql

-- Embedding 表
\i database/init/004_create_game_embeddings_table.sql

-- Reviews 表
\i database/init/006_create_reviews_table.sql
\i database/init/009_add_reviews_ordernum.sql

-- 关联表
\i database/init/005_create_game_relations_tables.sql

-- 迁移脚本：修改已有表结构
\i database/init/007_alter_game_embeddings_metadata.sql

-- 后续阶段表 (Phase 2 & 3)
-- reviews 表 - 游戏评论数据 (Phase 3)
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    external_comment_id INTEGER UNIQUE,
    user_id INTEGER,
    user_name VARCHAR(255),
    content TEXT NOT NULL,
    content_html TEXT,
    rating DECIMAL(3,1),
    sentiment VARCHAR(50),
    praises_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,
    publish_time TIMESTAMP,
    source VARCHAR(50) DEFAULT 'external',
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_game_id ON reviews(game_id);
CREATE INDEX IF NOT EXISTS idx_reviews_external_comment_id ON reviews(external_comment_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);

-- game_embeddings 表 - Embedding 向量 (Phase 2)
CREATE TABLE IF NOT EXISTS game_embeddings (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    embedding_vector vector(768),  -- 根据模型调整维度 (nomic-embed-text 是 768 维)
    chunk_text TEXT,
    metadata_json JSONB,  -- 重命名：避免与 SQLAlchemy 保留字冲突
    model_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_embeddings_game_id ON game_embeddings(game_id);
CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings USING ivfflat (embedding_vector vector_cosine_ops);

-- embedding_history 表 - Embedding 历史记录 (Phase 2)
CREATE TABLE IF NOT EXISTS embedding_history (
    record_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
    records_count INTEGER DEFAULT 0,
    batches_count INTEGER DEFAULT 0,
    successful_batches INTEGER DEFAULT 0,
    failed_batches INTEGER DEFAULT 0,
    batch_size INTEGER DEFAULT 10,
    model_name VARCHAR(255),
    error_messages TEXT,
    processing_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embedding_history_game_id ON embedding_history(game_id);
CREATE INDEX IF NOT EXISTS idx_embedding_history_timestamp ON embedding_history(processing_timestamp);

-- model_configs 表 - 模型配置 (Phase 2)
CREATE TABLE IF NOT EXISTS model_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL,  -- 'local' | 'openai' | 'anthropic' | 'custom'
    model_name VARCHAR(255) NOT NULL,
    base_url VARCHAR(500),
    api_key VARCHAR(500),  -- 加密存储
    config JSONB,
    is_embedding BOOLEAN DEFAULT FALSE,
    is_chat BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_configs_provider ON model_configs(provider_type);
CREATE INDEX IF NOT EXISTS idx_model_configs_active ON model_configs(is_active);

-- user_behaviors 表 - 用户行为数据 (Phase 3)
CREATE TABLE IF NOT EXISTS user_behaviors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    behavior_type VARCHAR(50) NOT NULL,  -- 'view' | 'like' | 'favorite' | 'share'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_behaviors_user_id ON user_behaviors(user_id);
CREATE INDEX IF NOT EXISTS idx_user_behaviors_game_id ON user_behaviors(game_id);
CREATE INDEX IF NOT EXISTS idx_user_behaviors_type ON user_behaviors(behavior_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_behaviors_unique ON user_behaviors(user_id, game_id, behavior_type);

