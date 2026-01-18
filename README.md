# Game Odyssey

<p align="center">
  <img src="docs/images/home-page.jpg" alt="Game Odyssey" width="600">
</p>

<p align="center">
  <strong>🎮 基于 RAG 的智能游戏推荐系统</strong>
</p>

<p align="center">
  <a href="README.md">English</a> •
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#系统架构">系统架构</a> •
  <a href="#贡献指南">贡献指南</a>
</p>

---

## 项目简介

Game Odyssey 是一个智能游戏推荐系统，使用 **RAG（检索增强生成）** 技术提供个性化的游戏推荐。只需告诉它你想玩什么类型的游戏，系统会通过语义搜索在游戏数据库中检索，然后用自然语言生成推荐。

**核心亮点：**
- 🔍 **语义搜索**：按含义而非关键词查找游戏
- 🤖 **本地 LLM**：完全在本机运行，使用 Ollama
- 🎯 **智能推荐**：自动排除你提到的游戏
- 💬 **对话式交互**：生成后续问题，方便继续探索

## 功能特性

- **AI 聊天界面**：自然语言游戏推荐
- **向量搜索**：基于 pgvector 的语义相似度搜索
- **游戏卡片**：展示图片、评分、标签、价格等丰富信息
- **后续推荐**：自动生成相关问题，引导持续探索
- **图片代理**：解决外部游戏图片的 CORS 问题
- **完全本地化**：无需 API Key，使用 Ollama + MLX

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL + pgvector |
| Embedding | MLX (Qwen3-Embedding-4B) |
| LLM | Ollama (Qwen2.5:3b) |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker（用于 PostgreSQL）
- Ollama

### 1. 克隆项目

```bash
git clone https://github.com/ICEMAN-CN/game-odyssey.git
cd game-odyssey
```

### 2. 启动数据库

```bash
docker-compose up -d postgres
```

### 3. 配置后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制并配置环境变量
cp .env.example .env
```

### 4. 启动 Ollama 并下载模型

```bash
# 启动 Ollama 服务
ollama serve

# 在另一个终端下载聊天模型
ollama pull qwen2.5:3b
```

### 5. 启动 Embedding 服务

```bash
cd scripts
python app.py  # 运行在 8000 端口
```

### 6. 启动后端 API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 7. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 8. 打开浏览器

访问 **http://localhost:5173** 开始聊天！

### 一键启动（推荐）

```bash
# 启动所有服务
./scripts/start.sh

# 停止所有服务
./scripts/stop.sh

# 重启所有服务
./scripts/restart.sh
```

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端                                 │
│                   React + TypeScript                         │
│                     localhost:5173                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       后端 API                               │
│                  FastAPI + Python                            │
│                    localhost:8001                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  聊天 API    │  │  游戏 API    │  │  图片代理    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
│         │                 │                                  │
│         ▼                 ▼                                  │
│  ┌──────────────────────────────────┐                       │
│  │          RAG 服务                │                       │
│  │  - 向量检索                      │                       │
│  │  - LLM 生成                      │                       │
│  └──────┬──────────────────┬────────┘                       │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │    Embedding    │  │     Ollama      │
│   + pgvector    │  │      服务       │  │      LLM        │
│   localhost:5432│  │  localhost:8000 │  │ localhost:11434 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 项目结构

```
game-odyssey/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 端点
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── services/        # 业务逻辑
│   │   ├── model_providers/ # LLM 提供者
│   │   └── config.py        # 配置
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── services/        # API 服务
│   │   └── types/           # TypeScript 类型
│   └── package.json
├── database/
│   └── init/                # SQL 迁移脚本
├── scripts/
│   ├── app.py               # Embedding 服务
│   ├── start.sh             # 启动所有服务
│   └── stop.sh              # 停止所有服务
└── docs/
    └── *.md                 # 文档
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat` | POST | 获取游戏推荐 |
| `/api/v1/games` | GET | 游戏列表（分页） |
| `/api/v1/games/{id}` | GET | 游戏详情 |
| `/api/v1/images/proxy` | GET | 代理外部图片 |
| `/health` | GET | 健康检查 |

## 配置说明

详见 [backend/.env.example](backend/.env.example)：

```bash
# 数据库
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey

# 游戏数据 API（外部数据源，需自行配置）
# 本项目提供推荐系统框架，你需要配置自己的数据源或导入示例数据
# GAME_DATA_API_URL=
# GAME_DATA_API_KEY=

# Embedding 服务
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_BASE_URL=http://localhost:8000

# 聊天模型 (Ollama)
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=qwen2.5:3b
CHAT_BASE_URL=http://localhost:11434
```

## 数据源配置

本项目是一个**推荐系统框架**。要使用它，你需要：

1. **方案 A**：配置自己的游戏数据 API
   - 在 `.env` 中设置 `GAME_DATA_API_URL` 和 `GAME_DATA_API_KEY`
   - 爬虫会从你配置的端点获取数据

2. **方案 B**：导入示例数据
   - 使用数据库脚本导入自己的游戏数据
   - 参考 `database/` 文件夹中的 schema 定义

3. **方案 C**：使用公开的游戏 API
   - 集成 IGDB、RAWG 或 Steam API
   - 在 `backend/app/crawlers/` 中扩展爬虫

## 常见问题

### Ollama 连接失败

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 重启 Ollama
pkill ollama && ollama serve
```

### 图片无法显示

图片来自外部域名，已通过图片代理解决 CORS 问题。如仍有问题，检查后端日志。

### 推荐结果与卡片不一致

已修复。系统现在会确保文字推荐与卡片显示的游戏一致，并排除用户提到的游戏。

## 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件。

## 开发路线

- [x] Phase 1：游戏数据抓取、存储和基础 API
- [x] Phase 2：Embedding、RAG 服务和 AI 聊天
- [ ] Phase 3：用户评论和行为数据
- [ ] Phase 4：个性化推荐

## 致谢

- 游戏数据来源于公开的游戏平台
- 基于 Ollama、pgvector 和 MLX 生态构建
