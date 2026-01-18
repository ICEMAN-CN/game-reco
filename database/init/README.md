# 数据库初始化 SQL 文件执行顺序

## 执行顺序

按以下顺序执行 SQL 文件：

1. **001_init_extensions.sql** - 创建 pgvector 扩展（需要 superuser 权限）
2. **002_create_games_table.sql** - 创建 games 表
3. **003_create_indexes.sql** - 创建 games 表的索引
4. **004_create_game_embeddings_table.sql** - 创建 game_embeddings 表
5. **006_create_reviews_table.sql** - 创建 reviews 表
6. **005_create_game_relations_tables.sql** - 创建关联表并扩展 reviews 表

## 迁移脚本（如果已执行过 1-6）

如果已经执行过上述 SQL 文件，需要执行迁移脚本：

7. **007_alter_game_embeddings_metadata.sql** - 修改 game_embeddings 表的 metadata 字段名为 metadata_json

## 注意事项

- 001_init_extensions.sql 需要 superuser 权限（如 postgres 用户）
- 007_alter_game_embeddings_metadata.sql 是迁移脚本，用于修改已存在的表结构
- 所有 SQL 文件都使用 `IF NOT EXISTS` 和 `IF EXISTS`，可以安全地重复执行
