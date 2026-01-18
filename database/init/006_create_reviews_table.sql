-- 创建 reviews 表 - 游戏评论数据
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

-- 添加注释
COMMENT ON TABLE reviews IS '游戏评论数据表';
