# 数据库初始化 SQL 执行顺序

在 DBeaver 或其他数据库工具中，按以下顺序执行 SQL 文件：

## 执行顺序

1. **001_init_extensions.sql** - 创建 pgvector 扩展（需要 superuser 权限）

   ```sql
   -- 如果使用普通用户，需要先以 postgres 用户执行：
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **002_create_games_table.sql** - 创建 games 表

3. **003_create_indexes.sql** - 创建 games 表的索引

4. **004_create_game_embeddings_table.sql** - 创建 game_embeddings 表

5. **006_create_reviews_table.sql** - 创建 reviews 表

6. **005_create_game_relations_tables.sql** - 创建关联表并扩展 reviews 表

### 迁移脚本（如果已执行过 1-6）

7. **007_alter_game_embeddings_metadata.sql** - 修改 game_embeddings 表的 metadata 字段名为 metadata_json
   - 用于修复 SQLAlchemy 保留字冲突问题
   - 如果已执行过 1-6，需要执行此迁移脚本

## 快速执行

可以在 DBeaver 中一次性执行所有文件：

```sql
-- 1. 扩展（需要 superuser）
\i database/init/001_init_extensions.sql

-- 2. 游戏表
\i database/init/002_create_games_table.sql

-- 3. 索引
\i database/init/003_create_indexes.sql

-- 4. Embedding 表
\i database/init/004_create_game_embeddings_table.sql

-- 5. Reviews 表
\i database/init/006_create_reviews_table.sql

-- 6. 关联表
\i database/init/005_create_game_relations_tables.sql
```

或者直接执行 `database/schema.sql`（包含所有表的创建语句）

## 验证表是否创建成功

```sql
-- 查看所有表
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 应该看到以下表：
-- games
-- game_embeddings
-- game_media_scores
-- game_prices
-- game_rank_relations
-- reviews
```

## 注意事项

1. **扩展创建**：`CREATE EXTENSION vector` 需要 superuser 权限。如果使用普通用户，需要先以 `postgres` 用户执行。

2. **DBeaver 刷新**：执行 SQL 后，在 DBeaver 中右键点击数据库连接，选择 "Refresh" 或按 F5 刷新，才能看到新创建的表。

3. **连接检查**：确保 DBeaver 连接的是正确的数据库（`game_odyssey`）和正确的 schema（`public`）。

## 迁移脚本

如果已经执行过上述 SQL 文件（1-6），需要执行迁移脚本来修复 SQLAlchemy 保留字冲突：

**007_alter_game_embeddings_metadata.sql** - 将 `game_embeddings` 表的 `metadata` 字段重命名为 `metadata_json`

```sql
-- 执行迁移脚本
\i database/init/007_alter_game_embeddings_metadata.sql
```

这个脚本会：

- 检查 `metadata` 字段是否存在，如果存在则重命名为 `metadata_json`
- 如果 `metadata` 不存在但 `metadata_json` 也不存在，则添加 `metadata_json` 字段
- 如果 `metadata_json` 已存在，则不做任何操作

可以安全地重复执行，不会出错。
