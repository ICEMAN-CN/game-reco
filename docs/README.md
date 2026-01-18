# Game Odyssey

基于 RAG 技术的游戏推荐系统

## 项目概述

Game Odyssey 是一个智能游戏推荐系统，通过抓取游戏数据、构建向量库，提供智能游戏推荐和 AI 聊天推荐功能。

## 技术栈

- **后端**: Python (FastAPI)
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS
- **数据库**: PostgreSQL + pgvector
- **定时任务**: Python APScheduler
- **Embedding**: LangChain + 可配置模型接口
- **AI 查询**: 可配置模型接口 (支持本地/远程)

## 项目结构

```
game-odyssey/
├── backend/          # Python 后端服务
├── frontend/         # React 前端
├── database/         # 数据库相关
└── docs/            # 文档
```

## 快速开始

### 📚 执行指南

- **[服务启动指南](SERVICE_STARTUP.md)** - 完整服务启动文档 (推荐)
- **[快速启动指南](QUICK_START.md)** - 一键执行命令列表
- **[详细设置指南](SETUP_GUIDE.md)** - 完整的设置步骤和说明
- **[执行检查清单](EXECUTION_CHECKLIST.md)** - 逐步执行检查清单
- **[代码审查报告](CODE_REVIEW.md)** - 代码完整性检查

### 🚀 快速开始 (5 分钟)

```bash
# 1. 安装 Ollama 和下载模型
brew install ollama
ollama serve &
ollama pull nomic-embed-text
ollama pull llama3.2:3b  # 或 llama3.2:1b

# 2. 启动数据库
docker-compose up -d postgres

# 3. 初始化项目
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py

# 4. 配置环境变量 (创建 .env 文件)
# 参考 SETUP_GUIDE.md 中的步骤 4

# 5. 抓取数据和生成 Embedding
python scripts/run_crawler.py --limit 50
python scripts/run_embedding.py --limit 50

# 6. 启动服务
python scripts/run_server.py  # 后端
cd ../frontend && npm install && npm run dev  # 前端
```

**详细步骤请参考**: [QUICK_START.md](QUICK_START.md) 或 [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 开发计划

- **Phase 1**: 游戏静态数据抓取、清洗、存储和基础 API ✅
- **Phase 2**: Embedding、RAG 服务和 AI 聊天推荐 ✅
- **Phase 3**: 游戏评论数据和用户行为数据 (待实现)

## 文档

- [架构文档](docs/architecture.md)
- [API 文档](docs/api.md)
- [爬虫文档](docs/crawler.md)

