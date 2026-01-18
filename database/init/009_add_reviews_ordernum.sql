-- 添加 ordernum 字段到 reviews 表
-- 用于记录评论在 API 返回的 listElements 中的原始顺序

-- 添加 ordernum 字段
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS ordernum INTEGER;

-- 创建复合索引用于优化按 game_id 和 ordernum 排序的查询
CREATE INDEX IF NOT EXISTS idx_reviews_game_id_ordernum ON reviews(game_id, ordernum);

-- 添加注释
COMMENT ON COLUMN reviews.ordernum IS '评论在 API 返回列表中的原始顺序（从1开始）';
