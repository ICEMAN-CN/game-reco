# Game Odyssey 项目计划

## 项目概述

Game Odyssey 是一个基于 RAG 技术的游戏推荐系统，通过抓取游戏数据、构建向量库，提供智能游戏推荐和 AI 聊天推荐功能。

## 技术栈

- **后端**: Python (FastAPI)
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS (参考 backoffice-cms)
- **数据库**: PostgreSQL + pgvector
- **定时任务**: Python APScheduler (集成到后端或独立服务)
- **Embedding**: LangChain + 可配置模型接口 (支持本地/远程)
- **AI 查询**: 可配置模型接口 (支持本地/远程)
- **向量存储**: PostgreSQL + pgvector

## 项目目录结构

```javascript
game-odyssey/
├── README.md
├── .gitignore
├── docker-compose.yml              # 本地开发环境
├── requirements.txt                # Python 依赖
│
├── backend/                         # Python 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── scheduler.py            # 定时任务调度器 (APScheduler)
│   │   │
│   │   ├── api/                    # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── games.py        # 游戏相关 API
│   │   │   │   ├── recommendations.py  # 推荐 API
│   │   │   │   └── chat.py         # AI 聊天 API
│   │   │
│   │   ├── models/                 # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── game.py             # 游戏模型
│   │   │   ├── review.py            # 评论模型
│   │   │   └── recommendation.py   # 推荐模型
│   │   │
│   │   ├── services/               # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── game_service.py     # 游戏服务
│   │   │   ├── crawler_service.py  # 爬虫服务
│   │   │   ├── cleaning_service.py # 数据清洗服务
│   │   │   ├── recommendation_service.py  # 推荐服务
│   │   │   ├── rag_service.py      # RAG 服务
│   │   │   └── embedding_service.py # Embedding 服务
│   │   │
│   │   ├── crawlers/               # 数据抓取模块
│   │   │   ├── __init__.py
│   │   │   ├── base_crawler.py     # 基础爬虫类
│   │   │   ├── game_data_crawler.py # 游戏数据爬虫
│   │   │   └── utils.py            # 爬虫工具函数
│   │   │
│   │   ├── cleaners/               # 数据清洗模块
│   │   │   ├── __init__.py
│   │   │   ├── game_cleaner.py     # 游戏数据清洗
│   │   │   └── review_cleaner.py   # 评论数据清洗
│   │   │
│   │   ├── model_providers/        # 模型接口提供者
│   │   │   ├── __init__.py
│   │   │   ├── base_provider.py    # 基础提供者接口
│   │   │   ├── local_provider.py   # 本地模型提供者 (Ollama, vLLM等)
│   │   │   ├── openai_provider.py  # OpenAI API 提供者
│   │   │   ├── anthropic_provider.py # Anthropic API 提供者
│   │   │   └── custom_provider.py  # 自定义 API 提供者
│   │   │
│   │   ├── schedulers/             # 定时任务
│   │   │   ├── __init__.py
│   │   │   ├── crawler_jobs.py     # 爬虫任务
│   │   │   ├── cleaning_jobs.py    # 清洗任务
│   │   │   └── embedding_jobs.py  # Embedding 任务
│   │   │
│   │   └── utils/                  # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   │
│   ├── migrations/                 # 数据库迁移
│   │   ├── versions/
│   │   └── alembic.ini
│   │
│   ├── tests/                      # 测试
│   │   ├── __init__.py
│   │   ├── test_crawlers.py
│   │   ├── test_cleaners.py
│   │   ├── test_api.py
│   │   └── test_model_providers.py
│   │
│   └── scripts/                     # 脚本
│       ├── init_db.py              # 初始化数据库
│       ├── seed_data.py             # 种子数据
│       └── run_scheduler.py         # 独立运行 scheduler
│
├── frontend/                        # React 前端
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts              # Vite 配置
│   ├── tailwind.config.js          # Tailwind 配置
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css               # 全局样式
│   │   │
│   │   ├── components/             # 组件
│   │   │   ├── Layout.tsx           # 主布局 (参考 backoffice-cms)
│   │   │   ├── ChatInterface.tsx    # 对话框主界面 (参考 ChatGPT/Grok)
│   │   │   ├── MessageList.tsx      # 消息列表
│   │   │   ├── MessageItem.tsx      # 单条消息
│   │   │   ├── GameCard.tsx        # 游戏卡片
│   │   │   ├── GameCardList.tsx    # 游戏卡片列表
│   │   │   ├── InputArea.tsx       # 输入区域
│   │   │   └── LoadingIndicator.tsx # 加载指示器
│   │   │
│   │   ├── pages/                  # 页面
│   │   │   └── ChatPage.tsx        # 聊天页面 (主页面)
│   │   │
│   │   ├── services/               # API 服务
│   │   │   ├── api.ts              # API 客户端 (Axios)
│   │   │   ├── gameService.ts      # 游戏服务
│   │   │   └── chatService.ts     # 聊天服务
│   │   │
│   │   ├── hooks/                  # React Hooks
│   │   │   ├── useChat.ts          # 聊天 Hook
│   │   │   └── useGames.ts        # 游戏 Hook
│   │   │
│   │   ├── types/                  # TypeScript 类型
│   │   │   ├── game.ts
│   │   │   ├── chat.ts
│   │   │   └── api.ts
│   │   │
│   │   └── utils/                  # 工具函数
│   │       └── constants.ts
│   │
│   └── public/
│
├── database/                        # 数据库相关
│   ├── migrations/                 # SQL 迁移文件
│   │   ├── 001_create_games_table.sql
│   │   ├── 002_create_reviews_table.sql
│   │   ├── 003_create_embeddings_table.sql
│   │   ├── 004_create_pgvector_extension.sql
│   │   └── 005_create_indexes.sql
│   │
│   └── schema.sql                  # 完整 schema
│
└── docs/                           # 文档
    ├── architecture.md              # 架构文档
    ├── api.md                       # API 文档
    ├── crawler.md                   # 爬虫文档
    ├── model_config.md             # 模型配置文档
    └── deployment.md               # 部署文档
```



## 数据库 Schema 设计

### games 表

- id (PK, SERIAL)
- name (VARCHAR, 游戏名称)
- genre (VARCHAR, 类型)
- platform (VARCHAR[], 平台数组)
- release_date (DATE, 发布日期)
- rating (DECIMAL, 评分)
- description (TEXT, 描述)
- raw_data (JSONB, 原始数据)
- source (VARCHAR, 数据来源, 如 'external')
- created_at, updated_at (TIMESTAMP)

### reviews 表

- id (PK, SERIAL)
- game_id (FK -> games.id)
- user_name (VARCHAR, 用户名)
- rating (DECIMAL, 评分)
- content (TEXT, 评论内容)
- sentiment (VARCHAR, 情感分析结果)
- raw_data (JSONB)
- source (VARCHAR)
- created_at, updated_at (TIMESTAMP)

### game_embeddings 表 (用于 RAG)

- id (PK, SERIAL)
- game_id (FK -> games.id)
- embedding_vector (vector, pgvector 类型)
- chunk_text (TEXT, 文本块)
- metadata (JSONB)
- model_name (VARCHAR, 使用的模型名称)
- created_at (TIMESTAMP)

### embedding_history 表

- record_id (PK, SERIAL)
- game_id (FK -> games.id)
- records_count (INTEGER)
- batches_count (INTEGER)
- successful_batches (INTEGER)
- failed_batches (INTEGER)
- batch_size (INTEGER)
- model_name (VARCHAR, 使用的模型)
- error_messages (TEXT)
- processing_timestamp (TIMESTAMP)
- created_at, updated_at (TIMESTAMP)

### model_configs 表 (模型配置)

- id (PK, SERIAL)
- name (VARCHAR, 配置名称)
- provider_type (VARCHAR, 'local' | 'openai' | 'anthropic' | 'custom')
- model_name (VARCHAR, 模型名称)
- base_url (VARCHAR, API 基础URL)
- api_key (VARCHAR, API密钥, 加密存储)
- config (JSONB, 额外配置)
- is_embedding (BOOLEAN, 是否用于embedding)
- is_chat (BOOLEAN, 是否用于聊天)
- is_active (BOOLEAN, 是否激活)
- created_at, updated_at (TIMESTAMP)

## 模块实现计划

### 1. 游戏数据抓取模块

**功能**:

- 从外部数据源抓取游戏数据
- 支持一次性抓取和定时抓取
- 数据存储到 PostgreSQL

**实现要点**:

- `backend/app/crawlers/base_crawler.py`: 基础爬虫抽象类
- `backend/app/crawlers/game_data_crawler.py`: 游戏数据爬虫实现
- `backend/app/services/crawler_service.py`: 爬虫服务
- `backend/app/schedulers/crawler_jobs.py`: 定时任务函数

**技术细节**:

- 使用 requests/httpx 进行 HTTP 请求
- 支持重试机制和错误处理
- 数据去重和增量更新
- 使用 APScheduler 定时执行

### 2. 数据清洗模块

**功能**:

- 将多平台/多来源的游戏数据统一格式
- 数据验证和清理
- 生成结构化游戏库数据

**实现要点**:

- `backend/app/cleaners/game_cleaner.py`: 游戏数据清洗逻辑
- `backend/app/cleaners/review_cleaner.py`: 评论数据清洗
- `backend/app/services/cleaning_service.py`: 清洗服务
- `backend/app/schedulers/cleaning_jobs.py`: 清洗定时任务

**清洗规则**:

- 字段映射和标准化
- 缺失值处理
- 数据去重
- 格式验证

### 3. 可配置模型接口模块

**功能**:

- 支持本地模型 (Ollama, vLLM, 本地部署)
- 支持远程 API (OpenAI, Anthropic, 自定义)
- 统一接口抽象
- 配置管理

**实现要点**:

- `backend/app/model_providers/base_provider.py`: 基础提供者接口
- `backend/app/model_providers/local_provider.py`: 本地模型 (Ollama/vLLM)
- `backend/app/model_providers/openai_provider.py`: OpenAI API
- `backend/app/model_providers/anthropic_provider.py`: Anthropic API
- `backend/app/model_providers/custom_provider.py`: 自定义 API
- `backend/app/config.py`: 模型配置管理

**配置示例**:

```python
# config.yaml 或环境变量
models:
  embedding:
    provider: "local"  # local | openai | anthropic | custom
    model_name: "nomic-embed-text"
    base_url: "http://localhost:11434"  # Ollama
    api_key: null
  
  chat:
    provider: "openai"
    model_name: "gpt-4"
    base_url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
```



### 4. Embedding 模块

**功能**:

- 使用可配置的模型进行 embedding
- 批量处理游戏数据
- 存储到 PostgreSQL + pgvector
- 支持增量更新

**实现要点**:

- `backend/app/services/embedding_service.py`: Embedding 服务
- `backend/app/schedulers/embedding_jobs.py`: Embedding 定时任务
- 使用 LangChain 的 Embeddings 接口
- 支持批量处理和错误重试
- 历史记录追踪

**技术架构**:

- 使用 LangChain 的 RAG 框架
- 通过模型提供者接口调用 embedding
- 支持本地和远程模型
- 批量处理和错误重试
- 历史记录追踪

### 5. RAG 服务模块

**功能**:

- 向量检索
- RAG 查询
- 上下文构建
- 结果生成

**实现要点**:

- `backend/app/services/rag_service.py`: RAG 核心逻辑
- 使用 LangChain 的 RetrievalQA
- 支持可配置的 LLM 模型
- 集成到后端 API

### 6. 后端 API 模块

**功能**:

- 游戏查询 API
- 随机推荐 API
- AI 聊天推荐 API
- 游戏详情 API

**实现要点**:

- `backend/app/main.py`: FastAPI 应用
- `backend/app/api/v1/games.py`: 游戏相关端点
- `backend/app/api/v1/recommendations.py`: 推荐端点
- `backend/app/api/v1/chat.py`: 聊天端点
- `backend/app/services/recommendation_service.py`: 推荐逻辑

**API 端点**:

- `GET /api/v1/games`: 游戏列表
- `GET /api/v1/games/{id}`: 游戏详情
- `GET /api/v1/recommendations/random`: 随机推荐
- `POST /api/v1/chat`: AI 聊天推荐 (流式响应)

### 7. 定时任务调度模块

**功能**:

- 定时执行数据抓取
- 定时执行数据清洗
- 定时执行 embedding
- 可配置调度策略

**实现要点**:

- `backend/app/scheduler.py`: APScheduler 配置
- `backend/app/schedulers/crawler_jobs.py`: 爬虫任务
- `backend/app/schedulers/cleaning_jobs.py`: 清洗任务
- `backend/app/schedulers/embedding_jobs.py`: Embedding 任务
- 集成到 FastAPI 应用或独立运行

**调度配置**:

```python
# 可以配置在 config.yaml 或环境变量
scheduler:
  crawler:
    enabled: true
    schedule: "0 2 * * *"  # 每天凌晨2点
  cleaning:
    enabled: true
    schedule: "0 3 * * *"  # 每天凌晨3点
  embedding:
    enabled: true
    schedule: "0 4 * * *"  # 每天凌晨4点
```



### 8. 前端 UI 模块

**功能**:

- 对话框式聊天界面 (参考 ChatGPT/Grok)
- 游戏卡片列表展示
- 消息流式显示
- 响应式设计

**实现要点** (参考 backoffice-cms 技术栈):

- React 18 + TypeScript
- Vite 构建工具
- Tailwind CSS 样式
- Lucide React 图标
- Axios HTTP 客户端

**主要组件**:

- `ChatInterface.tsx`: 对话框主界面
- 消息列表区域
- 输入区域
- 游戏卡片展示区域
- `MessageList.tsx`: 消息列表
- `MessageItem.tsx`: 单条消息 (用户/AI)
- `GameCard.tsx`: 游戏卡片
- `GameCardList.tsx`: 游戏卡片列表
- `InputArea.tsx`: 输入框和发送按钮

**UI 特性**:

- 流式消息显示 (SSE 或 WebSocket)
- Markdown 渲染
- 代码高亮
- 游戏卡片点击展开详情
- 响应式布局

## 执行计划

### Phase 1: 项目初始化 (1-2 天)

1. 创建项目目录结构
2. 初始化 Git 仓库
3. 设置开发环境 (Docker, 依赖管理)
4. 创建数据库 Schema
5. 配置基础框架 (FastAPI, React + Vite)

### Phase 2: 模型接口系统 (2-3 天)

1. 实现基础模型提供者接口
2. 实现本地模型提供者 (Ollama)
3. 实现远程 API 提供者 (OpenAI, Anthropic)
4. 实现配置管理系统
5. 测试模型接口

### Phase 3: 数据抓取模块 (3-4 天)

1. 实现基础爬虫框架
2. 实现游戏数据爬虫
3. 实现定时任务调度
4. 测试数据抓取流程

### Phase 4: 数据清洗模块 (2-3 天)

1. 实现数据清洗逻辑
2. 创建清洗定时任务
3. 测试数据清洗流程

### Phase 5: Embedding 和 RAG 模块 (4-5 天)

1. 实现 embedding 服务 (使用可配置模型)
2. 实现 RAG 服务
3. 创建 embedding 定时任务
4. 测试 embedding 和 RAG 流程

### Phase 6: 后端 API (3-4 天)

1. 实现游戏查询 API
2. 实现推荐 API
3. 实现聊天 API (流式响应)
4. API 测试

### Phase 7: 前端 UI (4-5 天)

1. 搭建 React 项目 (Vite + Tailwind)
2. 实现对话框界面 (参考 ChatGPT/Grok)
3. 实现游戏卡片组件
4. 实现流式消息显示
5. UI 测试和优化

### Phase 8: 集成测试和优化 (2-3 天)

1. 端到端测试
2. 性能优化
3. 文档完善

## 关键技术决策

1. **定时任务**: 使用 APScheduler (Python scheduler), 集成到后端或独立运行
2. **模型接口**: 可配置的提供者模式, 支持本地和远程模型
3. **Embedding**: LangChain + 可配置模型接口
4. **向量存储**: PostgreSQL + pgvector
5. **API 框架**: FastAPI (Python 异步支持)
6. **前端框架**: React 18 + TypeScript + Vite + Tailwind CSS (参考 backoffice-cms)
7. **UI 风格**: 对话框式界面 (参考 ChatGPT/Grok)

## 注意事项

1. 模型配置需要支持环境变量和配置文件
2. API 密钥需要加密存储
3. 支持模型热切换 (无需重启服务)
4. 错误处理和日志记录要完善
5. 支持增量更新和去重
6. 前端需要支持流式响应 (SSE 或 WebSocket)