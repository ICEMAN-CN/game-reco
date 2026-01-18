# Game Odyssey 项目执行指南

本文档提供完整的项目设置和执行步骤。

## 📋 前置要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (支持 pgvector)
- Ollama (用于本地模型)

## 🚀 执行步骤

### 步骤 1: 安装 Ollama 和下载模型

#### 1.1 安装 Ollama

```bash
# macOS
brew install ollama

# 或从官网下载: https://ollama.ai
```

#### 1.2 启动 Ollama 服务

```bash
# 启动 Ollama (会在后台运行)
ollama serve

# 验证服务是否运行
curl http://localhost:11434/api/tags
```

#### 1.3 下载 Embedding 模型

```bash
# 下载 nomic-embed-text (推荐，约 137MB)
ollama pull nomic-embed-text

# 验证模型
curl http://localhost:11434/api/embeddings \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "测试"
  }'
```

#### 1.4 下载聊天模型 (选择其一)

**Mac Air M2 24GB 推荐:**
```bash
# Llama 3.2 3B (约 2GB，性能好)
ollama pull llama3.2:3b

# 或 Mistral 7B (约 4.2GB，性能更好)
ollama pull mistral:7b
```

**Mac Pro M1 16GB 推荐:**
```bash
# Llama 3.2 1B (约 1.3GB，速度快)
ollama pull llama3.2:1b

# 或 Phi-3 Mini (约 2.3GB)
ollama pull phi3:mini
```

**验证聊天模型:**
```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "llama3.2:3b",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

---

### 步骤 2: 设置数据库

#### 2.1 启动 PostgreSQL

**使用 Docker (推荐):**
```bash
# 启动 PostgreSQL + pgvector
cd .
docker-compose up -d postgres

# 验证数据库
docker-compose ps
```

**或使用本地 PostgreSQL:**
```bash
# 创建数据库
createdb game_odyssey

# 安装 pgvector 扩展
psql game_odyssey -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 2.2 初始化数据库表结构

```bash
cd ./backend

# 运行初始化脚本
python scripts/init_db.py
```

**或手动执行 SQL:**
```bash
# 连接到数据库
psql game_odyssey

# 执行 SQL 文件
\i database/init/001_init_extensions.sql
\i database/init/002_create_games_table.sql
\i database/init/003_create_indexes.sql
\i database/init/004_create_game_embeddings_table.sql
```

**验证表结构:**
```bash
psql game_odyssey -c "\dt"
# 应该看到: games, game_embeddings 等表
```

---

### 步骤 3: 配置环境变量

#### 3.1 创建 .env 文件

```bash
cd ./backend

# 创建 .env 文件
cat > .env << EOF
# Database
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey

# Game Data API (外部数据源，需自行配置)
# GAME_DATA_API_URL=
# GAME_DATA_API_KEY=

# Embedding 模型 (本地)
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_MODEL_NAME=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_API_KEY=

# 聊天模型 (本地)
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=llama3.2:3b
CHAT_BASE_URL=http://localhost:11434
CHAT_API_KEY=

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
EOF
```

**注意:** 根据你的 Mac 配置调整 `CHAT_MODEL_NAME`:
- M2 24GB: `llama3.2:3b` 或 `mistral:7b`
- M1 16GB: `llama3.2:1b` 或 `phi3:mini`

---

### 步骤 4: 安装 Python 依赖

```bash
cd ./backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 如果 pgvector 安装失败，使用:
pip install pgvector
```

---

### 步骤 5: 抓取游戏数据

#### 5.1 运行爬虫

```bash
cd ./backend

# 确保虚拟环境已激活
source venv/bin/activate

# 抓取所有数据
python scripts/run_crawler.py --all

# 或限制数量 (测试用)
python scripts/run_crawler.py --limit 100
```

**验证数据:**
```bash
psql game_odyssey -c "SELECT COUNT(*) FROM games;"
psql game_odyssey -c "SELECT id, title, platforms FROM games LIMIT 5;"
```

---

### 步骤 6: 生成 Embedding

#### 6.1 确保 Ollama 服务运行

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 如果没有运行，启动它
ollama serve
```

#### 6.2 批量生成 Embedding

```bash
cd ./backend

# 确保虚拟环境已激活
source venv/bin/activate

# 生成所有游戏的 embedding
python scripts/run_embedding.py

# 或限制数量 (测试用)
python scripts/run_embedding.py --limit 50 --batch-size 5
```

**验证 Embedding:**
```bash
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"
psql game_odyssey -c "SELECT game_id, model_name, array_length(embedding_vector::text::float[], 1) as dims FROM game_embeddings LIMIT 1;"
```

#### 6.3 创建向量索引 (可选，提升检索速度)

```bash
psql game_odyssey << EOF
-- 创建向量索引 (需要先有数据)
CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
EOF
```

---

### 步骤 7: 启动后端服务

```bash
cd ./backend

# 确保虚拟环境已激活
source venv/bin/activate

# 启动服务
python scripts/run_server.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证 API:**
```bash
# 健康检查
curl http://localhost:8000/health

# 游戏列表
curl http://localhost:8000/api/v1/games?page=1&page_size=5

# 随机推荐
curl http://localhost:8000/api/v1/recommendations/random?limit=3

# 测试聊天 (需要先有 embedding 数据)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想玩开放世界游戏"}'
```

**访问 API 文档:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

### 步骤 8: 安装前端依赖

```bash
cd ./frontend

# 安装依赖
npm install

# 或使用 yarn
yarn install
```

---

### 步骤 9: 启动前端服务

```bash
cd ./frontend

# 启动开发服务器
npm run dev

# 或使用 yarn
yarn dev
```

**访问前端:**
- 前端地址: http://localhost:5173
- API 代理: 已配置为 http://localhost:8000

---

## ✅ 验证完整流程

### 1. 检查所有服务运行状态

```bash
# 检查 Ollama
curl http://localhost:11434/api/tags

# 检查 PostgreSQL
psql game_odyssey -c "SELECT version();"

# 检查后端 API
curl http://localhost:8000/health

# 检查前端
curl http://localhost:5173
```

### 2. 测试完整流程

1. **打开前端**: http://localhost:5173
2. **输入问题**: "我想玩开放世界游戏"
3. **查看结果**: 应该返回游戏推荐和游戏卡片

### 3. 检查数据

```bash
# 游戏数据
psql game_odyssey -c "SELECT COUNT(*) as games_count FROM games;"

# Embedding 数据
psql game_odyssey -c "SELECT COUNT(*) as embeddings_count FROM game_embeddings;"

# 检查数据完整性
psql game_odyssey -c "
SELECT 
    (SELECT COUNT(*) FROM games) as games,
    (SELECT COUNT(*) FROM game_embeddings) as embeddings,
    (SELECT COUNT(*) FROM games WHERE id IN (SELECT game_id FROM game_embeddings)) as games_with_embeddings;
"
```

---

## 🔧 常见问题

### 问题 1: Ollama 连接失败

```bash
# 检查 Ollama 是否运行
ps aux | grep ollama

# 重启 Ollama
pkill ollama
ollama serve
```

### 问题 2: pgvector 扩展安装失败

```bash
# 使用 Docker 镜像 (已包含 pgvector)
docker-compose up -d postgres

# 或手动安装
# macOS: brew install pgvector
# 然后重新编译 PostgreSQL
```

### 问题 3: Embedding 生成失败

```bash
# 检查模型是否下载
ollama list

# 测试模型
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

### 问题 4: 向量检索返回空结果

```bash
# 检查是否有 embedding 数据
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"

# 如果没有数据，运行 embedding 脚本
python scripts/run_embedding.py
```

### 问题 5: 前端无法连接后端

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 CORS 配置
# 在 backend/app/main.py 中确认 cors_origins 包含前端地址
```

---

## 📊 性能优化建议

### 1. Embedding 批量处理

```bash
# 使用较小的 batch_size 避免内存溢出
python scripts/run_embedding.py --batch-size 5
```

### 2. 向量索引优化

```bash
# 创建向量索引 (需要先有足够的数据)
psql game_odyssey << EOF
CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
EOF
```

### 3. 模型选择

- **Mac Air M2 24GB**: 可以使用 `llama3.2:3b` 或 `mistral:7b`
- **Mac Pro M1 16GB**: 建议使用 `llama3.2:1b` 或 `phi3:mini`

---

## 🎯 快速启动检查清单

- [ ] Ollama 已安装并运行
- [ ] Embedding 模型已下载 (`nomic-embed-text`)
- [ ] 聊天模型已下载 (`llama3.2:3b` 或 `llama3.2:1b`)
- [ ] PostgreSQL 已启动 (Docker 或本地)
- [ ] 数据库表已创建 (`python scripts/init_db.py`)
- [ ] 环境变量已配置 (`.env` 文件)
- [ ] Python 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 游戏数据已抓取 (`python scripts/run_crawler.py --all`)
- [ ] Embedding 已生成 (`python scripts/run_embedding.py`)
- [ ] 后端服务已启动 (`python scripts/run_server.py`)
- [ ] 前端依赖已安装 (`npm install`)
- [ ] 前端服务已启动 (`npm run dev`)

---

## 📝 下一步

1. **抓取更多数据**: 运行爬虫获取更多游戏
2. **优化 Embedding**: 调整文本组合策略
3. **改进 RAG**: 优化提示词和上下文构建
4. **添加功能**: 实现流式响应、历史记录等

---

**Happy Coding! 🚀**

