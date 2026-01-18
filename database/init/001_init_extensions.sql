-- 初始化 PostgreSQL 扩展
-- pgvector 用于向量存储 (Phase 2)

-- 创建 pgvector 扩展 (如果不存在)
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证扩展是否安装成功
SELECT * FROM pg_extension WHERE extname = 'vector';

