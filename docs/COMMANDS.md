# Game Odyssey 执行命令汇总

## 📋 所有执行命令 (按顺序)

### 1. 安装 Ollama 和下载模型

```bash
# 安装 Ollama
brew install ollama

# 启动 Ollama 服务 (后台)
ollama serve

# 下载 Embedding 模型
ollama pull nomic-embed-text

# 下载聊天模型 (根据 Mac 配置选择)
# Mac Air M2 24GB:
ollama pull llama3.2:3b
# 或
ollama pull mistral:7b

# Mac Pro M1 16GB:
ollama pull llama3.2:1b
# 或
ollama pull phi3:mini

# 验证模型
ollama list
```

---

### 2. 启动数据库

```bash
cd .

# 启动 PostgreSQL (Docker)
docker-compose up -d postgres

# 等待启动
sleep 10

# 验证
docker-compose ps
```

---

### 3. 初始化后端项目

```bash
cd ./backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

### 4. 配置环境变量

```bash
cd ./backend

# 创建 .env 文件
cat > .env << 'EOF'
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_MODEL_NAME=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=llama3.2:3b
CHAT_BASE_URL=http://localhost:11434
HOST=0.0.0.0
PORT=8000
DEBUG=true
EOF
```

**注意**: 根据你的 Mac 修改 `CHAT_MODEL_NAME`

---

### 5. 初始化数据库

```bash
cd ./backend
source venv/bin/activate

# 运行初始化脚本
python scripts/init_db.py

# 验证表结构
psql game_odyssey -c "\dt"
```

---

### 6. 抓取游戏数据

```bash
cd ./backend
source venv/bin/activate

# 测试抓取 (限制 50 条)
python scripts/run_crawler.py --limit 50

# 或抓取所有数据
python scripts/run_crawler.py --all

# 验证数据
psql game_odyssey -c "SELECT COUNT(*) FROM games;"
psql game_odyssey -c "SELECT id, title FROM games LIMIT 5;"
```

---

### 7. 生成 Embedding

```bash
cd ./backend
source venv/bin/activate

# 确保 Ollama 运行
curl http://localhost:11434/api/tags

# 生成 Embedding (测试用)
python scripts/run_embedding.py --limit 50 --batch-size 5

# 或生成所有游戏的 Embedding
python scripts/run_embedding.py

# 验证 Embedding
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"
```

---

### 8. 创建向量索引 (可选)

```bash
psql game_odyssey << 'EOF'
CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
EOF
```

---

### 9. 启动后端服务

```bash
cd ./backend
source venv/bin/activate

# 启动服务
python scripts/run_server.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**验证后端** (新开终端):
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/games?page=1&page_size=5
```

**访问 API 文档**: http://localhost:8000/docs

---

### 10. 安装前端依赖

```bash
cd ./frontend

# 安装依赖
npm install
```

---

### 11. 启动前端服务

```bash
cd ./frontend

# 启动开发服务器
npm run dev
```

**访问前端**: http://localhost:5173

---

## 🔍 验证命令

### 检查所有服务

```bash
# 1. Ollama
curl http://localhost:11434/api/tags

# 2. 数据库
psql game_odyssey -c "SELECT version();"

# 3. 后端
curl http://localhost:8000/health

# 4. 前端
curl http://localhost:5173
```

### 检查数据

```bash
# 游戏数据
psql game_odyssey -c "SELECT COUNT(*) FROM games;"

# Embedding 数据
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"

# 数据完整性
psql game_odyssey -c "
SELECT 
    (SELECT COUNT(*) FROM games) as games,
    (SELECT COUNT(*) FROM game_embeddings) as embeddings,
    (SELECT COUNT(*) FROM games WHERE id IN (SELECT game_id FROM game_embeddings)) as games_with_embeddings;
"
```

### 测试 API

```bash
# 游戏列表
curl http://localhost:8000/api/v1/games?page=1&page_size=5

# 随机推荐
curl http://localhost:8000/api/v1/recommendations/random?limit=3

# 聊天推荐
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想玩开放世界游戏"}'
```

---

## 🔧 常用维护命令

### 重启服务

```bash
# 重启 Ollama
pkill ollama
ollama serve

# 重启数据库
docker-compose restart postgres

# 重启后端 (Ctrl+C 停止，然后重新运行)
python scripts/run_server.py
```

### 查看日志

```bash
# 数据库日志
docker-compose logs postgres

# 后端日志 (在运行服务的终端查看)
```

### 清理数据

```bash
# 清空游戏数据 (谨慎使用)
psql game_odyssey -c "TRUNCATE games CASCADE;"

# 清空 Embedding 数据
psql game_odyssey -c "TRUNCATE game_embeddings;"
```

---

## 📝 一键执行脚本 (可选)

创建 `setup.sh` 脚本:

```bash
#!/bin/bash
set -e

echo "🚀 Game Odyssey 项目设置"

# 1. 检查 Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama 未安装，请先安装: brew install ollama"
    exit 1
fi

# 2. 启动 Ollama
echo "📦 启动 Ollama..."
ollama serve &
sleep 5

# 3. 下载模型
echo "📥 下载模型..."
ollama pull nomic-embed-text
ollama pull llama3.2:3b

# 4. 启动数据库
echo "🗄️  启动数据库..."
docker-compose up -d postgres
sleep 10

# 5. 初始化后端
echo "🔧 初始化后端..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. 初始化数据库
echo "📊 初始化数据库..."
python scripts/init_db.py

# 7. 创建 .env
echo "⚙️  创建配置文件..."
cat > .env << 'EOF'
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_MODEL_NAME=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=llama3.2:3b
CHAT_BASE_URL=http://localhost:11434
HOST=0.0.0.0
PORT=8000
DEBUG=true
EOF

echo "✅ 设置完成！"
echo ""
echo "下一步:"
echo "1. 抓取数据: python scripts/run_crawler.py --limit 50"
echo "2. 生成 Embedding: python scripts/run_embedding.py --limit 50"
echo "3. 启动后端: python scripts/run_server.py"
echo "4. 启动前端: cd ../frontend && npm install && npm run dev"
```

保存为 `setup.sh`，然后:
```bash
chmod +x setup.sh
./setup.sh
```

---

## 📚 相关文档

- [快速启动指南](QUICK_START.md)
- [详细设置指南](SETUP_GUIDE.md)
- [执行检查清单](EXECUTION_CHECKLIST.md)
- [代码审查报告](CODE_REVIEW.md)

