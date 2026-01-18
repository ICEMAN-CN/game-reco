-- 修改 game_embeddings 表的 metadata 字段名
-- 原因: metadata 是 SQLAlchemy 的保留字，需要重命名为 metadata_json

-- 检查字段是否存在，如果存在则重命名
DO $$
BEGIN
    -- 检查 metadata 字段是否存在
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'game_embeddings' 
        AND column_name = 'metadata'
    ) THEN
        -- 重命名字段
        ALTER TABLE game_embeddings 
        RENAME COLUMN metadata TO metadata_json;
        
        RAISE NOTICE '字段 metadata 已重命名为 metadata_json';
    ELSE
        -- 如果 metadata 不存在，检查 metadata_json 是否已存在
        IF NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'game_embeddings' 
            AND column_name = 'metadata_json'
        ) THEN
            -- 如果都不存在，添加新字段
            ALTER TABLE game_embeddings 
            ADD COLUMN metadata_json JSONB;
            
            RAISE NOTICE '已添加新字段 metadata_json';
        ELSE
            RAISE NOTICE '字段 metadata_json 已存在，无需修改';
        END IF;
    END IF;
END $$;

-- 添加注释
COMMENT ON COLUMN game_embeddings.metadata_json IS '元数据 JSON，重命名自 metadata 以避免与 SQLAlchemy 保留字冲突';

