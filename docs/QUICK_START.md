# Game Odyssey 快速启动指南

## 🚀 一键执行列表

### 1. 安装 Ollama 和下载模型

```bash
# 安装 Ollama
brew install ollama

# 启动 Ollama 服务
ollama serve

# 下载 Embedding 模型
ollama pull nomic-embed-text

# 下载聊天模型 (根据你的 Mac 选择)
# Mac Air M2 24GB:
ollama pull llama3.2:3b

# Mac Pro M1 16GB:
ollama pull llama3.2:1b
```

### 2. 启动数据库

```bash
cd .

# 使用 Docker 启动 PostgreSQL
docker-compose up -d postgres

# 等待数据库启动 (约 10 秒)
sleep 10
```

### 3. 初始化数据库

```bash
cd ./backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库表
python scripts/init_db.py
```

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

**注意**: 根据你的 Mac 配置修改 `CHAT_MODEL_NAME`:
- M2 24GB: `llama3.2:3b` 或 `mistral:7b`
- M1 16GB: `llama3.2:1b` 或 `phi3:mini`

### 5. 抓取游戏数据

```bash
cd ./backend
source venv/bin/activate

# 抓取数据 (测试用，限制 50 条)
python scripts/run_crawler.py --limit 50

# 或抓取所有数据
# python scripts/run_crawler.py --all
```

### 6. 生成 Embedding

```bash
cd ./backend
source venv/bin/activate

# 确保 Ollama 服务运行
curl http://localhost:11434/api/tags

# 生成 Embedding
python scripts/run_embedding.py --limit 50 --batch-size 5

# 或生成所有游戏的 Embedding
# python scripts/run_embedding.py
```

### 7. 启动后端服务

```bash
cd ./backend
source venv/bin/activate

# 启动服务
python scripts/run_server.py
```

**验证后端:**
```bash
# 新开一个终端
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/games?page=1&page_size=5
```

### 8. 启动前端服务

```bash
# 新开一个终端
cd ./frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 9. 访问应用

- **前端**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs

---

## ✅ 验证检查

```bash
# 1. 检查 Ollama
curl http://localhost:11434/api/tags

# 2. 检查数据库
psql game_odyssey -c "SELECT COUNT(*) FROM games;"
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"

# 3. 检查后端
curl http://localhost:8000/health

# 4. 测试聊天 API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想玩开放世界游戏"}'
```

---

## 🔧 常见问题快速修复

### Ollama 连接失败
```bash
pkill ollama
ollama serve
```

### 数据库连接失败
```bash
docker-compose restart postgres
sleep 5
```

### Embedding 生成失败
```bash
# 检查模型
ollama list
# 重新下载
ollama pull nomic-embed-text
```

### 前端无法连接后端
```bash
# 检查后端是否运行
curl http://localhost:8000/health
# 检查端口
lsof -i :8000
```

---

## 📝 完整命令序列 (复制粘贴)

```bash
# ===== 1. 安装和启动 Ollama =====
brew install ollama
ollama serve &
sleep 5
ollama pull nomic-embed-text
ollama pull llama3.2:3b  # 或 llama3.2:1b

# ===== 2. 启动数据库 =====
cd .
docker-compose up -d postgres
sleep 10

# ===== 3. 初始化项目 =====
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ===== 4. 配置环境 =====
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

# ===== 5. 初始化数据库 =====
python scripts/init_db.py

# ===== 6. 抓取数据 =====
python scripts/run_crawler.py --limit 50

# ===== 7. 生成 Embedding =====
python scripts/run_embedding.py --limit 50 --batch-size 5

# ===== 8. 启动后端 (新终端) =====
# cd ./backend
# source venv/bin/activate
# python scripts/run_server.py

# ===== 9. 启动前端 (新终端) =====
# cd ./frontend
# npm install
# npm run dev
```

---

**详细文档请参考**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

