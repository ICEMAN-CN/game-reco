-- 修改 game_embeddings 表的向量维度从 768 改为 2560
-- 用于支持 Qwen3-Embedding-4B 模型
-- 注意：此操作需要先删除现有数据或重建表

-- 方案1：如果表为空或可以清空数据，直接修改列类型
-- ALTER TABLE game_embeddings ALTER COLUMN embedding_vector TYPE vector(2560);

-- 方案2：如果表有数据，需要先备份、删除、重建
-- 步骤1：备份数据（可选）
-- CREATE TABLE game_embeddings_backup AS SELECT * FROM game_embeddings;

-- 步骤2：删除现有数据（因为向量维度改变，无法直接转换）
-- TRUNCATE TABLE game_embeddings;

-- 步骤3：修改列类型
-- ALTER TABLE game_embeddings ALTER COLUMN embedding_vector TYPE vector(2560);

-- 方案3：重建表（推荐，更安全）
DO $$
BEGIN
    -- 检查表是否存在
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'game_embeddings') THEN
        -- 检查当前维度
        IF EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'game_embeddings' 
            AND column_name = 'embedding_vector'
            AND data_type = 'USER-DEFINED'
        ) THEN
            -- 检查维度是否为 768
            -- 注意：PostgreSQL 无法直接查询 vector 类型的维度，需要通过其他方式判断
            -- 这里假设如果表存在且列存在，需要更新
            
            -- 删除现有数据（因为维度改变无法直接转换）
            RAISE NOTICE '清空现有 embedding 数据（维度从 768 改为 2560）...';
            TRUNCATE TABLE game_embeddings;
            
            -- 删除列
            ALTER TABLE game_embeddings DROP COLUMN IF EXISTS embedding_vector;
            
            -- 重新创建列（2560维）
            ALTER TABLE game_embeddings ADD COLUMN embedding_vector vector(2560);
            
            RAISE NOTICE '向量维度已更新为 2560';
        ELSE
            RAISE NOTICE 'embedding_vector 列不存在或类型不正确';
        END IF;
    ELSE
        RAISE NOTICE 'game_embeddings 表不存在，请先运行 004_create_game_embeddings_table.sql';
    END IF;
END $$;

-- 更新默认模型名称
UPDATE game_embeddings SET model_name = 'qwen3-embedding-4b' WHERE model_name = 'nomic-embed-text';

COMMENT ON COLUMN game_embeddings.embedding_vector IS '游戏文本的 embedding 向量 (Qwen3-Embedding-4B, 2560维)';
