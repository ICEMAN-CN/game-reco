# Game Odyssey 执行检查清单

## 📋 执行步骤清单

### ✅ 步骤 1: 安装 Ollama 和下载模型

```bash
# 1.1 安装 Ollama
brew install ollama

# 1.2 启动 Ollama 服务 (后台运行)
ollama serve

# 1.3 验证 Ollama 运行
curl http://localhost:11434/api/tags

# 1.4 下载 Embedding 模型
ollama pull nomic-embed-text

# 1.5 下载聊天模型 (根据你的 Mac 选择)
# Mac Air M2 24GB:
ollama pull llama3.2:3b

# Mac Pro M1 16GB:
ollama pull llama3.2:1b

# 1.6 验证模型
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "测试"}'
```

**检查点**: ✅ Ollama 服务运行，模型已下载

---

### ✅ 步骤 2: 启动数据库

```bash
# 2.1 进入项目目录
cd .

# 2.2 启动 PostgreSQL (Docker)
docker-compose up -d postgres

# 2.3 等待数据库启动 (约 10 秒)
sleep 10

# 2.4 验证数据库
docker-compose ps
```

**检查点**: ✅ PostgreSQL 容器运行中

---

### ✅ 步骤 3: 初始化数据库表结构

```bash
# 3.1 进入后端目录
cd ./backend

# 3.2 创建虚拟环境
python -m venv venv

# 3.3 激活虚拟环境
source venv/bin/activate

# 3.4 安装 Python 依赖
pip install -r requirements.txt

# 3.5 初始化数据库
python scripts/init_db.py
```

**检查点**: ✅ 数据库表已创建

**验证命令**:
```bash
psql game_odyssey -c "\dt"
# 应该看到: games, game_embeddings 等表
```

---

### ✅ 步骤 4: 配置环境变量

```bash
# 4.1 创建 .env 文件
cd ./backend

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

# 4.2 验证 .env 文件
cat .env
```

**检查点**: ✅ .env 文件已创建

**注意**: 根据你的 Mac 配置修改 `CHAT_MODEL_NAME`:
- M2 24GB: `llama3.2:3b` 或 `mistral:7b`
- M1 16GB: `llama3.2:1b` 或 `phi3:mini`

---

### ✅ 步骤 5: 抓取游戏数据

```bash
# 5.1 确保在虚拟环境中
cd ./backend
source venv/bin/activate

# 5.2 抓取数据 (测试用，限制 50 条)
python scripts/run_crawler.py --limit 50

# 或抓取所有数据
# python scripts/run_crawler.py --all
```

**检查点**: ✅ 游戏数据已抓取

**验证命令**:
```bash
psql game_odyssey -c "SELECT COUNT(*) FROM games;"
psql game_odyssey -c "SELECT id, title, platforms FROM games LIMIT 5;"
```

---

### ✅ 步骤 6: 生成 Embedding

```bash
# 6.1 确保 Ollama 服务运行
curl http://localhost:11434/api/tags

# 6.2 确保在虚拟环境中
cd ./backend
source venv/bin/activate

# 6.3 生成 Embedding (测试用，限制 50 条)
python scripts/run_embedding.py --limit 50 --batch-size 5

# 或生成所有游戏的 Embedding
# python scripts/run_embedding.py
```

**检查点**: ✅ Embedding 已生成

**验证命令**:
```bash
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"
psql game_odyssey -c "SELECT game_id, model_name FROM game_embeddings LIMIT 5;"
```

---

### ✅ 步骤 7: 创建向量索引 (可选，提升性能)

```bash
# 7.1 创建向量索引 (需要先有 embedding 数据)
psql game_odyssey << 'EOF'
CREATE INDEX IF NOT EXISTS idx_game_embeddings_vector ON game_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);
EOF
```

**检查点**: ✅ 向量索引已创建

---

### ✅ 步骤 8: 启动后端服务

```bash
# 8.1 确保在虚拟环境中
cd ./backend
source venv/bin/activate

# 8.2 启动服务
python scripts/run_server.py

# 服务将在 http://localhost:8000 运行
```

**检查点**: ✅ 后端服务运行中

**验证命令** (新开终端):
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/games?page=1&page_size=5
```

**访问 API 文档**: http://localhost:8000/docs

---

### ✅ 步骤 9: 安装前端依赖

```bash
# 9.1 进入前端目录
cd ./frontend

# 9.2 安装依赖
npm install
```

**检查点**: ✅ 前端依赖已安装

---

### ✅ 步骤 10: 启动前端服务

```bash
# 10.1 启动开发服务器
cd ./frontend
npm run dev

# 前端将在 http://localhost:5173 运行
```

**检查点**: ✅ 前端服务运行中

**访问前端**: http://localhost:5173

---

## 🎯 完整验证

### 验证所有服务运行

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

# 5. 检查前端
curl http://localhost:5173
```

### 测试完整流程

1. 打开浏览器: http://localhost:5173
2. 输入问题: "我想玩开放世界游戏"
3. 查看结果: 应该返回游戏推荐和游戏卡片

---

## 🔧 故障排除

### 问题 1: Ollama 连接失败

```bash
# 检查 Ollama 是否运行
ps aux | grep ollama

# 重启 Ollama
pkill ollama
ollama serve
```

### 问题 2: 数据库连接失败

```bash
# 重启数据库
docker-compose restart postgres
sleep 5

# 检查数据库日志
docker-compose logs postgres
```

### 问题 3: Embedding 生成失败

```bash
# 检查模型
ollama list

# 测试模型
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

### 问题 4: 向量检索返回空结果

```bash
# 检查是否有 embedding 数据
psql game_odyssey -c "SELECT COUNT(*) FROM game_embeddings;"

# 如果没有数据，重新运行 embedding 脚本
python scripts/run_embedding.py
```

### 问题 5: 前端无法连接后端

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查端口占用
lsof -i :8000
lsof -i :5173
```

---

## 📊 数据统计检查

```bash
# 检查数据完整性
psql game_odyssey << 'EOF'
SELECT 
    (SELECT COUNT(*) FROM games) as games_count,
    (SELECT COUNT(*) FROM game_embeddings) as embeddings_count,
    (SELECT COUNT(*) FROM games WHERE id IN (SELECT game_id FROM game_embeddings)) as games_with_embeddings;
EOF
```

**预期结果**:
- `games_count`: 游戏总数
- `embeddings_count`: Embedding 总数
- `games_with_embeddings`: 有 Embedding 的游戏数 (应该等于 embeddings_count)

---

## ✅ 完成检查清单

- [ ] Ollama 已安装并运行
- [ ] Embedding 模型已下载 (`nomic-embed-text`)
- [ ] 聊天模型已下载 (`llama3.2:3b` 或 `llama3.2:1b`)
- [ ] PostgreSQL 已启动
- [ ] 数据库表已创建
- [ ] 环境变量已配置
- [ ] Python 依赖已安装
- [ ] 游戏数据已抓取
- [ ] Embedding 已生成
- [ ] 后端服务已启动
- [ ] 前端依赖已安装
- [ ] 前端服务已启动
- [ ] 完整流程测试通过

---

**所有步骤完成后，项目即可使用！** 🎉

