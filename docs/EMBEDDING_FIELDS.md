# Embedding 字段选择逻辑

## 概述

本文档说明 Game Odyssey 项目中，游戏数据的 embedding 生成使用了哪些字段，以及字段组合的逻辑。

## 数据来源

Embedding 数据来自以下数据库表：
- `games` - 游戏基础信息
- `game_prices` - 游戏价格信息（多平台）
- `game_media_scores` - 媒体评分
- `reviews` - 用户评论

## 字段选择逻辑

### 1. 游戏基础信息（来自 `games` 表）

| 字段 | 说明 | 是否必选 |
|------|------|---------|
| `title` | 游戏名称（中文） | 是 |
| `title_english` | 游戏英文名称 | 否 |
| `platforms` | 支持平台列表（数组） | 否 |
| `tags` | 游戏标签列表（数组） | 否 |
| `description` | 游戏描述（纯文本，限制500字符） | 否 |

**格式化规则：**
- 游戏名称：`游戏名称: {title}`
- 英文名称：`英文名称: {title_english}`（如果存在）
- 平台：`支持平台: {platform1}, {platform2}, ...`（如果存在）
- 标签：`标签: {tag1}, {tag2}, ...`（如果存在）
- 描述：`游戏描述: {description}`（截取前500字符，如果存在）

### 2. 价格信息（来自 `game_prices` 表）

**数据获取：**
- 查询条件：`game_id = {game.id}`
- 获取所有平台的价格记录

**格式化规则：**
- 免费游戏：`{platform}平台: 免费`
- 付费游戏：`{platform}平台: ¥{price}`
- 有史低价格：`{platform}平台: ¥{price}, 史低¥{price_lowest}`

**输出格式：**
```
价格信息: Steam平台: ¥199; PSN平台: ¥299, 史低¥149; NS平台: 免费
```

### 3. 媒体评分（来自 `game_media_scores` 表）

**数据获取：**
- 查询条件：`game_id = {game.id}`
- 获取所有媒体的评分记录

**格式化规则：**
- 10分制：`{media_name} {score}/10`（如：`IGN 9.2/10`）
- 100分制：`{media_name} {score}/100`（如：`Metacritic 92/100`）
- 其他：`{media_name} {score}/{total_score}`

**输出格式：**
```
媒体评分: IGN 9.2/10, Metacritic 92/100, GameSpot 8.5/10
```

### 4. 用户评论（来自 `reviews` 表）

**数据获取：**
- 查询条件：`game_id = {game.id} AND content IS NOT NULL AND content != ''`
- 排序：按 `publish_time DESC`（最新优先）
- 限制：最多 5 条评论
- 每条评论内容限制：200 字符

**格式化规则：**
- 每条评论单独处理，超过200字符截断
- 多条评论用 ` | ` 分隔

**输出格式：**
```
用户评论: 这游戏剧情超棒，但优化一般... | 开放世界RPG，探索自由度高... | 画面精美，值得推荐...
```

## 完整文本组合示例

```
游戏名称: 解限机
英文名称: Mecha BREAK
支持平台: PC, Xbox
标签: 机甲, 机器人, 动作
价格信息: Steam平台: ¥199; PSN平台: ¥299, 史低¥149
游戏描述: 这是一款机甲题材的动作游戏，玩家将驾驶机甲在开放世界中战斗...
媒体评分: IGN 9.2/10, Metacritic 92/100, GameSpot 8.5/10
用户评论: 这游戏剧情超棒，但优化一般... | 开放世界RPG，探索自由度高... | 画面精美，值得推荐...
```

## 实现位置

### 核心逻辑

1. **`backend/app/services/embedding_service.py`**
   - `embed_game()` 方法：从数据库获取关联数据，构建 `game_data` 字典
   - 调用 `GameCleaner.extract_embedding_fields()` 生成文本

2. **`backend/app/cleaners/game_cleaner.py`**
   - `extract_embedding_fields()` 方法：将 `game_data` 字典格式化为文本字符串
   - 处理所有字段的格式化逻辑

### 数据流程

```
Game 对象
  ↓
EmbeddingService.embed_game()
  ├─ 查询 game_prices → price_infes[]
  ├─ 查询 game_media_scores → media_scores[]
  ├─ 查询 reviews → reviews[]
  └─ 构建 game_data 字典
      ↓
GameCleaner.extract_embedding_fields()
  └─ 格式化为文本字符串
      ↓
LocalModelProvider.embed_texts()
  └─ 调用 MLX API 生成 embedding
```

## 字段优先级

1. **核心字段（高优先级）**
   - 游戏名称（title）
   - 游戏描述（description）
   - 标签（tags）

2. **重要字段（中优先级）**
   - 平台信息（platforms）
   - 价格信息（price_infes）
   - 媒体评分（media_scores）

3. **补充字段（低优先级）**
   - 英文名称（title_english）
   - 用户评论（reviews，最多5条）

## 注意事项

1. **文本长度限制**
   - 描述：最多 500 字符
   - 评论：每条最多 200 字符
   - 评论数量：最多 5 条

2. **数据完整性**
   - 所有字段都是可选的（除了 title）
   - 如果某个字段不存在，不会影响其他字段的处理
   - 空值会被自动跳过

3. **性能考虑**
   - 评论查询使用 `LIMIT 5` 限制数量
   - 逐个调用 API 生成 embedding，避免 OOM
   - 数据库查询使用索引优化（`game_id`）

4. **向量维度**
   - 当前使用 Qwen3-Embedding-4B 模型
   - 向量维度：**2560**
   - 如果维度不匹配，会抛出异常

## 更新历史

- 2026-01-11: 初始版本，包含基础字段、价格、媒体评分、评论
- 2026-01-11: 添加媒体评分格式化逻辑（支持10分制和100分制）
