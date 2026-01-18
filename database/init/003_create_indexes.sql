-- 创建索引

-- 游戏表索引
CREATE INDEX IF NOT EXISTS idx_games_external_id ON games(external_id);
CREATE INDEX IF NOT EXISTS idx_games_title ON games(title);
CREATE INDEX IF NOT EXISTS idx_games_platforms ON games USING GIN(platforms);
CREATE INDEX IF NOT EXISTS idx_games_tags ON games USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_games_publish_date ON games(publish_date);
CREATE INDEX IF NOT EXISTS idx_games_user_score ON games(user_score);
CREATE INDEX IF NOT EXISTS idx_games_raw_data ON games USING GIN(raw_data);
CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at);
CREATE INDEX IF NOT EXISTS idx_games_updated_at ON games(updated_at);

-- 复合索引
CREATE INDEX IF NOT EXISTS idx_games_platform_score ON games(platforms, user_score);
CREATE INDEX IF NOT EXISTS idx_games_publish_score ON games(publish_date, user_score);
