-- 创建游戏表 (games)
-- 存储游戏基础信息

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE NOT NULL,  -- 外部数据源游戏ID
    title VARCHAR(255) NOT NULL,          -- 游戏名称
    title_english VARCHAR(255),           -- 英文名称
    developer_name VARCHAR(255),          -- 开发商
    publisher_name VARCHAR(255),          -- 发行商
    description TEXT,                     -- 游戏描述 (从 detailInHtml 提取纯文本)
    description_html TEXT,                -- 原始 HTML 描述
    cover_image_url TEXT,                 -- 封面图URL
    thumbnail_url TEXT,                   -- 缩略图URL
    horizontal_image_url TEXT,            -- 横版图URL
    platforms TEXT[],                     -- 平台数组 ['PC', 'Xbox']
    platform_ids INTEGER[],               -- 平台ID数组
    publish_date DATE,                    -- 发布日期
    publish_timestamp BIGINT,             -- 发布时间戳
    user_score DECIMAL(3,1),              -- 用户评分
    score_users_count INTEGER,            -- 评分用户数
    playeds_count INTEGER,                -- 玩过人数
    want_plays_count INTEGER,             -- 想玩人数
    tags TEXT[],                          -- 标签数组 ['机甲', '机器人', ...]
    steam_game_id VARCHAR(50),            -- Steam 游戏ID
    steam_praise_rate DECIMAL(3,2),       -- Steam 好评率
    steam_header_image TEXT,             -- Steam 头图
    is_free BOOLEAN DEFAULT FALSE,        -- 是否免费
    price DECIMAL(10,2),                  -- 价格
    price_original DECIMAL(10,2),         -- 原价
    device_requirement_html TEXT,         -- 配置要求 HTML
    theme_color VARCHAR(50),              -- 主题色
    hot_value VARCHAR(50),                -- 热度值
    be_official_chinese_enable BOOLEAN,  -- 是否支持中文
    play_hours_caption VARCHAR(50),       -- 游戏时长
    real_players_score DECIMAL(3,1),    -- 认证玩家评分
    real_players_count INTEGER,          -- 认证玩家数量
    source VARCHAR(50) DEFAULT 'external', -- 数据来源
    raw_data JSONB,                       -- 原始 JSON 数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 添加注释
COMMENT ON TABLE games IS '游戏静态数据表';
COMMENT ON COLUMN games.external_id IS '外部数据源游戏ID';
COMMENT ON COLUMN games.raw_data IS '原始 JSON 数据，包含完整的 gameInfo';
