# Game Odyssey (game-reco) 项目深度技术分析文档

## 1. 项目概述

**Game Odyssey** 是一个基于 **RAG (Retrieval-Augmented Generation, 检索增强生成)** 架构的智能游戏推荐系统。

不同于传统的基于协同过滤（Collaborative Filtering）的推荐系统，本项目利用**大语言模型 (LLM)** 和**向量数据库**，能够理解用户的自然语言查询（例如："想玩一款画风唯美、剧情感人的独立游戏"），并通过语义搜索从数据库中检索最匹配的游戏，最后由 LLM 生成带有详细推荐理由的自然语言回复。

---

## 2. 技术架构栈

该项目采用了轻量级、现代化的 Python AI 后端技术栈：

| 模块 | 技术选型 | 作用 |
| :--- | :--- | :--- |
| **Web 框架** | **FastAPI** + Uvicorn | 提供高性能异步 API 接口，自动生成 OpenAPI 文档 |
| **数据库** | **PostgreSQL** | 关系型数据存储（游戏基础信息、评论、价格等） |
| **向量存储** | **pgvector** | PostgreSQL 插件，实现向量数据的存储与余弦相似度检索 |
| **ORM** | **SQLAlchemy 2.0** | 现代 Python ORM，处理数据库交互 |
| **LLM 编排** | **LangChain** | 封装 LLM 调用、Prompt 构建和链式处理 |
| **模型支持** | OpenAI / Claude / Local | 支持云端模型或本地模型（通过策略模式封装） |
| **爬虫** | BeautifulSoup4 + httpx | 抓取游戏元数据、评分和评论 |

---

## 3. 核心概念解释

### 3.1 RAG (检索增强生成)
这是本项目的核心心脏。
*   **传统 LLM 的局限**：ChatGPT 不知道你数据库里具体有哪些游戏，也无法实时更新游戏价格或评分。
*   **本项目的解决**：
    1.  **Retrieve (检索)**：先根据用户问题，去数据库里找 5 个最相关的游戏。
    2.  **Augment (增强)**：把这 5 个游戏的信息（包括实时价格、评分）“喂”给 LLM。
    3.  **Generate (生成)**：LLM 根据这些确凿的事实，生成最终的推荐语。

### 3.2 Embedding (向量化)
*   **定义**：将文字转化为一串数字（向量），例如 `[0.12, -0.98, 0.44, ...]`。
*   **作用**：让计算机理解“语义”。
    *   在向量空间中，“塞尔达”和“原神”的距离很近。
    *   “恐怖游戏”和“生化危机”的距离很近。
*   **实现**：本项目使用了 `EmbeddingService` 将游戏的“标题+简介+标签+评论+价格”混合成一段文本，计算出向量并存入 Postgres。

### 3.3 PGVector
*   **定义**：PostgreSQL 的一个扩展插件。
*   **优势**：允许在普通的 Postgres 表中存储向量列，并支持 `<=>` (余弦距离) 操作符。这意味着我们不需要维护额外的 Milvus 或 Pinecone 集群，极大简化了运维成本。

---

## 4. 核心业务流程逻辑

### 4.1 数据入库与索引流程 (离线/后台)

这个流程负责把非结构化的游戏数据转化为可检索的向量。

```mermaid
graph TD
    A[游戏爬虫 Crawler] -->|抓取| B(原始游戏数据 JSON)
    B -->|清洗/结构化| C{数据库 PostgreSQL}
    C -->|读取| D[EmbeddingService]
    D -->|拼接文本| E[Chunk Text]
    E -- 内容包括 --> E1[标题 & 简介]
    E -- 内容包括 --> E2[Tags & 平台]
    E -- 内容包括 --> E3[用户评论 (Top 5)]
    E -- 内容包括 --> E4[当前价格 & 评分]
    E -->|调用 Embedding API| F[向量模型 (OpenAI/Local)]
    F -->|返回向量 float[]| G[存入 game_embeddings 表]
    G -->|构建索引| H[pgvector HNSW Index]
```

### 4.2 用户推荐响应流程 (在线/实时)

这是用户发起一次聊天时的完整处理链路。

```mermaid
graph TD
    User[用户] -->|发送: "推荐个类似艾尔登法环的游戏"| API[FastAPI Endpoint]
    API -->|转发| RAG[RAGService]
    
    subgraph 检索阶段 Retrieve
    RAG -->|Embedding| QVec[查询向量 Query Vector]
    QVec -->|SQL 余弦距离排序| DB[(PostgreSQL + pgvector)]
    DB -->|返回 Top 5| Sims[相似游戏列表]
    end
    
    subgraph 增强阶段 Augment
    Sims -->|排除逻辑| Filter[过滤: 排除用户已提到的游戏]
    Filter -->|提取详情| Context[构建 Prompt 上下文]
    note1[上下文包含: 游戏名, 简介, 评分, 标签] -.-> Context
    end
    
    subgraph 生成阶段 Generate
    Context -->|组合| FinalPrompt[最终提示词]
    FinalPrompt -->|调用| LLM[大语言模型]
    LLM -->|生成| Response[结构化回复]
    end
    
    Response -->|解析| Result{解析器}
    Result -->|文本| T[推荐理由文案]
    Result -->|数据| D[推荐游戏 ID List]
    Result -->|引导| Q[后续追问建议]
    
    Result --> API
    API --> User
```

---

## 5. 关键代码模块解析

### 5.1 `rag_service.py` (核心大脑)
*   **`search_similar_games`**: 执行向量检索。如果向量检索失败（如 API 报错），会自动**降级 (Fallback)** 为 SQL `ILIKE` 模糊查询，保证系统高可用。
*   **`_parse_recommendation_response`**: 正则表达式解析器。LLM 输出的不仅仅是文本，还包含自定义标记（如 `---游戏ID---`），该函数将其解析为前端可用的结构化 JSON。
*   **Prompt Engineering**: 包含特殊的 System Prompt，强制 LLM **“只能推荐列表里的游戏”**，有效防止了 LLM 的“幻觉”问题（即编造不存在的游戏）。

### 5.2 `embedding_service.py` (数据转化)
*   **`embed_game`**: 这是一个非常精细的数据处理函数。它不是简单地 embedding 简介，而是聚合了**价格**（识别便宜/免费）、**评论**（识别玩家真实口碑）和**评分**。这使得用户搜索“好评如潮的免费游戏”时，向量检索能精准命中。

### 5.3 `models/game_embedding.py`
*   定义了数据库模型，直接使用了 `mapped_column(Vector(1536))`，这是 SQLAlchemy 对 pgvector 的原生支持方式。

---

## 6. 后端开发建议

如果您打算基于此项目进行二次开发，建议关注以下点：

1.  **混合检索 (Hybrid Search)**: 目前主要是向量检索。未来可以引入 **BM25 关键词检索**，与向量检索结果进行 **RRF (Reciprocal Rank Fusion)** 加权融合，能进一步提升对专有名词（如“马里奥”、“最终幻想”）的搜索准确率。
2.  **缓存层**: 热门问题的推荐结果可以存入 Redis，减少 LLM Token 消耗。
3.  **多轮对话**: 当前架构主要针对单轮问答。若要支持多轮（如“换一批”），需要在 RAG Service 中引入 `ConversationHistory`。

---
*文档生成时间: 2026-01-29*
