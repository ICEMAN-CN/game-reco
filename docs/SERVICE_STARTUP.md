# Game Odyssey 服务启动指南

本文档详细说明所有服务的启动顺序、端口配置和验证方法。

## 服务概览

| 服务名称 | 端口 | 依赖 | 说明 |
|---------|------|------|------|
| PostgreSQL | 5432 | - | 数据库服务 (Docker) |
| Ollama | 11434 | - | 聊天模型服务 |
| Embedding Service | 8000 | - | MLX 本地 Embedding 服务 |
| Backend API | 8001 | PostgreSQL, Ollama, Embedding | FastAPI 后端 |
| Frontend | 5173 | Backend API | React 前端 |

## 服务依赖关系

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ PostgreSQL  │     │   Ollama    │     │  Embedding  │
│   :5432     │     │   :11434    │     │   :8000     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Backend API │
                    │   :8001     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Frontend   │
                    │   :5173     │
                    └─────────────┘
```

## 启动顺序

按以下顺序启动服务，确保依赖服务先启动：

1. **PostgreSQL** - 数据库服务
2. **Ollama** - 聊天模型服务
3. **Embedding Service** - Embedding 服务 (可与 Ollama 并行启动)
4. **Backend API** - 后端 API 服务
5. **Frontend** - 前端服务

---

## 1. PostgreSQL 数据库

### 启动命令

```bash
# 进入项目根目录
cd .

# 使用 Docker Compose 启动
docker-compose up -d postgres

# 等待数据库完全启动
sleep 10
```

### 验证

```bash
# 检查容器状态
docker-compose ps

# 测试数据库连接
docker exec -it game_odyssey_db psql -U game_odyssey -c "SELECT version();"

# 或使用本地 psql
psql -h localhost -U game_odyssey -d game_odyssey -c "SELECT 1;"
```

### 初始化数据库 (首次运行)

```bash
cd backend
source venv/bin/activate  # 如果使用虚拟环境
python scripts/init_db.py
```

---

## 2. Ollama 服务 (聊天模型)

### 安装 (首次)

```bash
# macOS
brew install ollama

# 或从官网下载: https://ollama.ai
```

### 启动命令

```bash
# 启动 Ollama 服务 (后台运行)
ollama serve

# 或在新终端窗口运行，便于查看日志
```

### 下载模型 (首次)

```bash
# 下载聊天模型 (根据 Mac 配置选择)
# M2 24GB 或更高:
ollama pull qwen2.5:3b

# M1 16GB:
ollama pull qwen2.5:1.5b

# 查看已下载的模型
ollama list
```

### 验证

```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 测试聊天模型
curl http://localhost:11434/api/chat \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

---

## 3. Embedding 服务 (MLX 本地模型)

Embedding 服务使用 MLX 框架运行 Qwen3-Embedding-4B 模型。

### 安装依赖 (首次)

```bash
# 安装 MLX 相关依赖
pip install mlx mlx-lm fastapi uvicorn pydantic langchain-core
```

### 启动命令

```bash
# 进入项目根目录
cd .

# 启动 Embedding 服务 (端口 8000)
python scripts/app.py

# 或使用 uvicorn 启动
uvicorn scripts.app:app --host 0.0.0.0 --port 8000
```

**注意**: 首次启动会下载模型文件 (约 2-4GB)，请耐心等待。

### 验证

```bash
# 检查服务状态
curl http://localhost:8000/docs

# 测试 Embedding 生成
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["测试文本"]}'
```

---

## 4. Backend API (FastAPI)

### 配置环境变量

创建或编辑 `backend/.env` 文件：

```bash
cd backend

cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey

# Embedding 模型 (本地 MLX 服务)
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_MODEL_NAME=qwen3-embedding-4b
EMBEDDING_BASE_URL=http://localhost:8000

# 聊天模型 (本地 Ollama)
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=qwen2.5:3b
CHAT_BASE_URL=http://localhost:11434

# Server
HOST=0.0.0.0
PORT=8001
DEBUG=true
EOF
```

### 启动命令

```bash
cd ./backend

# 激活虚拟环境
source venv/bin/activate

# 启动后端服务 (端口 8001，避免与 Embedding 服务冲突)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 或使用启动脚本 (需修改端口)
# python scripts/run_server.py
```

### 验证

```bash
# 健康检查
curl http://localhost:8001/health

# 获取游戏列表
curl http://localhost:8001/api/v1/games?page=1&page_size=5

# 测试聊天 API (非流式)
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "推荐一个开放世界游戏"}'

# 测试聊天 API (流式)
curl -X POST http://localhost:8001/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "推荐一个开放世界游戏"}'
```

### API 文档

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 5. Frontend (React)

### 安装依赖 (首次)

```bash
cd ./frontend

# 安装依赖
npm install
```

### 启动命令

```bash
cd ./frontend

# 启动开发服务器
npm run dev
```

### 验证

- 访问: http://localhost:5173
- 确认页面加载正常
- 测试聊天功能

---

## 一键启动脚本

创建 `scripts/start_all.sh` 方便快速启动所有服务：

```bash
#!/bin/bash
set -e

PROJECT_ROOT="."

echo "=========================================="
echo "  Game Odyssey 服务启动"
echo "=========================================="

# 1. 启动 PostgreSQL
echo ""
echo "[1/5] 启动 PostgreSQL..."
cd $PROJECT_ROOT
docker-compose up -d postgres
sleep 5

# 2. 启动 Ollama
echo ""
echo "[2/5] 启动 Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 3
else
    echo "Ollama 已在运行"
fi

# 3. 启动 Embedding 服务
echo ""
echo "[3/5] 启动 Embedding 服务..."
cd $PROJECT_ROOT
python scripts/app.py &
sleep 10  # 等待模型加载

# 4. 启动 Backend API
echo ""
echo "[4/5] 启动 Backend API..."
cd $PROJECT_ROOT/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
sleep 3

# 5. 启动 Frontend
echo ""
echo "[5/5] 启动 Frontend..."
cd $PROJECT_ROOT/frontend
npm run dev &

echo ""
echo "=========================================="
echo "  所有服务已启动"
echo "=========================================="
echo ""
echo "服务地址:"
echo "  - PostgreSQL:      localhost:5432"
echo "  - Ollama:          localhost:11434"
echo "  - Embedding:       localhost:8000"
echo "  - Backend API:     localhost:8001"
echo "  - Frontend:        localhost:5173"
echo ""
echo "API 文档: http://localhost:8001/docs"
echo "前端地址: http://localhost:5173"
```

使用方法：

```bash
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

---

## 验证检查清单

启动所有服务后，执行以下检查确认一切正常：

```bash
# 1. PostgreSQL
docker exec -it game_odyssey_db psql -U game_odyssey -c "SELECT COUNT(*) FROM games;"

# 2. Ollama
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# 3. Embedding 服务
curl -s http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test"]}' | jq '.dimension'

# 4. Backend API
curl -s http://localhost:8001/health

# 5. Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

---

## 常见问题

### 端口冲突

**问题**: 端口已被占用

```bash
# 查看占用端口的进程
lsof -i :8000  # Embedding 端口
lsof -i :8001  # Backend 端口
lsof -i :5173  # Frontend 端口

# 终止进程
kill -9 <PID>
```

### Ollama 连接失败

**问题**: `connection refused` 错误

```bash
# 检查 Ollama 是否运行
ps aux | grep ollama

# 重启 Ollama
pkill ollama
ollama serve
```

### Embedding 服务启动慢

**原因**: 首次启动需要下载模型文件

**解决**: 耐心等待模型下载完成，通常需要 5-10 分钟（取决于网络速度）

### 数据库连接失败

**问题**: `connection refused` 或认证失败

```bash
# 检查 Docker 容器状态
docker-compose ps

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Backend API 启动失败

**问题**: 依赖服务未就绪

1. 确认 PostgreSQL 已启动并可连接
2. 确认 Embedding 服务 (8000) 已启动
3. 确认 Ollama (11434) 已启动
4. 检查 `.env` 配置是否正确

---

## 停止服务

### 停止所有服务

```bash
# 停止 Docker 容器
docker-compose down

# 停止 Ollama
pkill ollama

# 停止 Python 进程 (Embedding, Backend)
pkill -f "uvicorn"
pkill -f "scripts/app.py"

# 停止 Node 进程 (Frontend)
pkill -f "vite"
```

### 停止单个服务

```bash
# PostgreSQL
docker-compose stop postgres

# Ollama
pkill ollama

# Embedding 服务 (查找并停止)
lsof -i :8000 | grep python | awk '{print $2}' | xargs kill

# Backend API
lsof -i :8001 | grep python | awk '{print $2}' | xargs kill

# Frontend
lsof -i :5173 | grep node | awk '{print $2}' | xargs kill
```

---

## 相关文档

- [快速启动指南](QUICK_START.md)
- [详细设置指南](SETUP_GUIDE.md)
- [执行命令汇总](COMMANDS.md)
- [执行检查清单](EXECUTION_CHECKLIST.md)
