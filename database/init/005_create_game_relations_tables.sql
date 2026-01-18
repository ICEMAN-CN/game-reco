-- 创建游戏关联表
-- 用于存储游戏的多平台价格、媒体评分、榜单关联等信息

-- 游戏-榜单关联表
CREATE TABLE IF NOT EXISTS game_rank_relations (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    rank_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, rank_id)
);

CREATE INDEX IF NOT EXISTS idx_game_rank_relations_game_id ON game_rank_relations(game_id);
CREATE INDEX IF NOT EXISTS idx_game_rank_relations_rank_id ON game_rank_relations(rank_id);

-- 游戏多平台价格表
CREATE TABLE IF NOT EXISTS game_prices (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    platform_name VARCHAR(50) NOT NULL,
    price DECIMAL(10,2),
    price_lowest DECIMAL(10,2),
    price_original DECIMAL(10,2),
    sale_price_rate DECIMAL(5,2),
    is_free BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, platform_name)
);

CREATE INDEX IF NOT EXISTS idx_game_prices_game_id ON game_prices(game_id);
CREATE INDEX IF NOT EXISTS idx_game_prices_platform ON game_prices(platform_name);

-- 游戏媒体评分表
CREATE TABLE IF NOT EXISTS game_media_scores (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    media_name VARCHAR(255) NOT NULL,
    score DECIMAL(5,2),
    total_score DECIMAL(5,2),
    content_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, media_name)
);

CREATE INDEX IF NOT EXISTS idx_game_media_scores_game_id ON game_media_scores(game_id);
CREATE INDEX IF NOT EXISTS idx_game_media_scores_media_name ON game_media_scores(media_name);

-- 扩展 reviews 表，添加新字段（如果表存在）
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'reviews') THEN
        ALTER TABLE reviews 
        ADD COLUMN IF NOT EXISTS game_label_platform_names TEXT[],
        ADD COLUMN IF NOT EXISTS content_user_label_type_names TEXT[],
        ADD COLUMN IF NOT EXISTS author_user_id INTEGER,
        ADD COLUMN IF NOT EXISTS author_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS author_head_image_url TEXT,
        ADD COLUMN IF NOT EXISTS treads_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- 添加注释
COMMENT ON TABLE game_rank_relations IS '游戏和榜单的关联关系';
COMMENT ON TABLE game_prices IS '游戏多平台价格信息';
COMMENT ON TABLE game_media_scores IS '游戏媒体评分信息';

