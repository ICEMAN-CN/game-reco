# Game Odyssey

<p align="center">
  <img src="docs/images/home-page.jpg" alt="Game Odyssey" width="600">
</p>

<p align="center">
  <strong>🎮 AI-Powered Game Recommendation System with RAG</strong>
</p>

<p align="center">
  <a href="README.zh-CN.md">中文文档</a> •
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## What is Game Odyssey?

Game Odyssey is an intelligent game recommendation system that uses **RAG (Retrieval-Augmented Generation)** to provide personalized game suggestions. Tell it what kind of game you want, and it will search through a database of games using semantic search, then generate natural language recommendations.

**Key Highlights:**
- 🔍 **Semantic Search**: Find games by meaning, not just keywords
- 🤖 **Local LLM**: Runs entirely on your machine with Ollama
- 🎯 **Smart Recommendations**: Excludes games you already mentioned
- 💬 **Conversational**: Suggests follow-up questions for exploration

## Features

- **AI Chat Interface**: Natural language game recommendations
- **Vector Search**: pgvector-powered semantic similarity search
- **Game Cards**: Rich display with images, scores, tags, and prices
- **Follow-up Suggestions**: Auto-generated questions for continued exploration
- **Image Proxy**: Solves CORS issues for external game images
- **Fully Local**: No API keys required - runs on Ollama + MLX

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | PostgreSQL + pgvector |
| Embedding | MLX (Qwen3-Embedding-4B) |
| LLM | Ollama (Qwen2.5:3b) |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL)
- Ollama

### 1. Clone and Setup

```bash
git clone https://github.com/ICEMAN-CN/game-odyssey.git
cd game-odyssey
```

### 2. Start Database

```bash
docker-compose up -d postgres
```

### 3. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
```

### 4. Start Ollama & Download Models

```bash
# Start Ollama service
ollama serve

# Download chat model (in another terminal)
ollama pull qwen2.5:3b
```

### 5. Start Embedding Service

```bash
cd scripts
python app.py  # Runs on port 8000
```

### 6. Start Backend API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 7. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 8. Open in Browser

Visit **http://localhost:5173** and start chatting!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   React + TypeScript                         │
│                     localhost:5173                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│                  FastAPI + Python                            │
│                    localhost:8001                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Chat API    │  │  Games API   │  │ Image Proxy  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
│         │                 │                                  │
│         ▼                 ▼                                  │
│  ┌──────────────────────────────────┐                       │
│  │         RAG Service              │                       │
│  │  - Vector Search                 │                       │
│  │  - LLM Generation                │                       │
│  └──────┬──────────────────┬────────┘                       │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │    Embedding    │  │     Ollama      │
│   + pgvector    │  │    Service      │  │      LLM        │
│   localhost:5432│  │  localhost:8000 │  │ localhost:11434 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Project Structure

```
game-odyssey/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── model_providers/ # LLM providers
│   │   └── config.py        # Configuration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   └── package.json
├── database/
│   └── init/                # SQL migrations
├── scripts/
│   ├── app.py               # Embedding service
│   ├── start.sh             # Start all services
│   └── stop.sh              # Stop all services
└── docs/
    └── *.md                 # Documentation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Get game recommendations |
| `/api/v1/games` | GET | List games with pagination |
| `/api/v1/games/{id}` | GET | Get game details |
| `/api/v1/images/proxy` | GET | Proxy external images |
| `/health` | GET | Health check |

## Configuration

See [backend/.env.example](backend/.env.example) for all configuration options:

```bash
# Database
DATABASE_URL=postgresql://game_odyssey:game_odyssey@localhost:5432/game_odyssey

# Game Data API (external data source - configure your own)
# This project provides the infrastructure for game recommendations.
# You need to configure your own data source or import sample data.
# GAME_DATA_API_URL=
# GAME_DATA_API_KEY=

# Embedding Service
EMBEDDING_MODEL_PROVIDER=local
EMBEDDING_BASE_URL=http://localhost:8000

# Chat Model (Ollama)
CHAT_MODEL_PROVIDER=local
CHAT_MODEL_NAME=qwen2.5:3b
CHAT_BASE_URL=http://localhost:11434
```

## Data Source

This project is a **recommendation system framework**. To use it, you need to:

1. **Option A**: Configure your own game data API
   - Set `GAME_DATA_API_URL` and `GAME_DATA_API_KEY` in `.env`
   - The crawler will fetch data from your configured endpoint

2. **Option B**: Import sample data
   - Use the database scripts to import your own game data
   - See `database/` folder for schema definitions

3. **Option C**: Use public game APIs
   - Integrate with IGDB, RAWG, or Steam APIs
   - Extend the crawler in `backend/app/crawlers/`
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [x] Phase 1: Game data crawling, storage, and basic API
- [x] Phase 2: Embedding, RAG service, and AI chat
- [ ] Phase 3: User reviews and behavior data
- [ ] Phase 4: Personalized recommendations

## Acknowledgments

- Game data sourced from public gaming platforms
- Built with Ollama, pgvector, and the MLX ecosystem