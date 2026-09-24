<p align="center">
  <h1 align="center">🧠 SmartDesk AI</h1>
  <p align="center">
    <strong>Enterprise-Grade AI Customer Support Platform</strong><br/>
    <em>Powered by Retrieval-Augmented Generation, Multi-Provider LLMs & Real-Time Conversation Intelligence</em>
  </p>
  <p align="center">
    <a href="#quick-start"><img src="https://img.shields.io/badge/Quick_Start-5_min-brightgreen?style=for-the-badge" alt="Quick Start"/></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"/></a>
    <a href="#api-reference"><img src="https://img.shields.io/badge/API-10_Endpoints-orange?style=for-the-badge" alt="API Endpoints"/></a>
    <a href="#observability--monitoring"><img src="https://img.shields.io/badge/Monitoring-Prometheus_%2B_Grafana-red?style=for-the-badge" alt="Observability"/></a>
  </p>
</p>

---

SmartDesk AI transforms customer support from reactive ticket queues into proactive, AI-driven resolution. The platform ingests your knowledge base documents, builds a high-performance vector search index, and provides **context-aware, multi-turn conversations** grounded in your proprietary data — with automatic ticket summarization and email dispatch to human agents when escalation is needed.

**Built for teams that refuse to choose between AI capability and operational control.**

---

## 📊 By the Numbers

| Metric | Value |
|---|---|
| **RESTful API Endpoints** | 10 fully documented (Swagger/OpenAPI) |
| **Embedding Dimensions** | 384 – 1,536 (configurable per provider) |
| **Supported LLM Providers** | 2 (OpenAI, Cohere) — independently mixable for generation & embedding |
| **Vector DB Backends** | 2 (Qdrant, pgvector) — hot-swappable via env variable |
| **Docker Services** | 9 orchestrated containers (FastAPI, Next.js, Nginx, pgvector, Qdrant, Prometheus, Grafana, Node Exporter, Postgres Exporter) |
| **Batch Indexing** | Paginated 50-record batches with `tqdm` progress tracking |
| **Nginx Upload Limit** | 100 MB per request, 300s proxy timeout |
| **Prometheus Metrics** | 2 core instruments: `http_request_total` (Counter) + `http_request_duration_seconds` (Histogram) |
| **Conversation Persistence** | JSONB-backed full message history with UUID session tracking |
| **Ticket Summarization** | Structured JSON output with 4-tier priority classification (critical / high / medium / low) |

---

## 🏗️ Architecture Overview

SmartDesk AI follows a **layered, provider-agnostic architecture** with clear separation between the API surface, business logic controllers, data access models, and pluggable LLM/VectorDB backends.

```text
                        ┌─────────────────────────────────────────┐
                        │          NGINX REVERSE PROXY             │
                        │         (Port 80 — Entry Point)          │
                        └─────────┬─────────────────┬──────────────┘
                                  │                 │
                           /api/* │                 │  /* (UI)
                                  ▼                 ▼
                        ┌─────────────────┐  ┌──────────────────┐
                        │  FastAPI Backend │  │  Next.js Frontend│
                        │  (Async, :8000)  │  │  (SSR, :3000)    │
                        └────────┬────────┘  └──────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
  ┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐
  │ RAG Pipeline  │    │  Conversation   │    │  Observability   │
  │               │    │  Manager        │    │  Stack           │
  └───────┬───────┘    └────────┬────────┘    └────────┬─────────┘
          │                     │                      │
    ┌─────┴──────┐     ┌───────┴────────┐      ┌──────┴──────────┐
    │            │     │                │      │                 │
    ▼            ▼     ▼                ▼      ▼                 ▼
  Qdrant     pgvector PostgreSQL    SMTP    Prometheus        Grafana
  (Vector)   (Vector) (Relational)  Email   (Scraping)       (Dashboards)
                         │
              ┌──────────┴──────────┐
              │  Projects           │
              │  DataChunks (JSONB) │
              │  Assets             │
              │  Conversations      │
              └─────────────────────┘

═══════════════════════════════════════════════════════════
                  CONVERSATION LIFECYCLE
═══════════════════════════════════════════════════════════

  User Query ──► Reformalize Query (context-aware)
                       │
                       ▼
              Embed Query (OpenAI / Cohere)
                       │
                       ▼
              Vector Similarity Search (top-k)
                       │
                       ▼
              Inject Context ──► LLM Generation
                       │
                       ▼
              Persist to JSONB ──► Return Answer
                       │
                  [On Close]
                       │
                       ▼
              Summarize (LLM) ──► JSON Ticket
                       │
                       ▼
              Email via SMTP ──► Support Team

═══════════════════════════════════════════════════════════
                  OBSERVABILITY STACK
═══════════════════════════════════════════════════════════

  Prometheus ──scrapes──► FastAPI /metrics
  Prometheus ──scrapes──► Node Exporter (CPU, RAM, Disk)
  Prometheus ──scrapes──► Postgres Exporter (DB metrics)
      │
      └──────► Grafana Dashboards (4 pre-configured)
```

### Request Flow — RAG Chat Pipeline

```text
┌─────────┐    POST /api/v1/conversation/chat/{id}     ┌──────────────────┐
│  Client  │ ─────────────────────────────────────────► │  FastAPI Router   │
└─────────┘                                             └────────┬─────────┘
                                                                 │
                                                                 ▼
                                                  ┌──────────────────────────┐
                                                  │ ConversationNLPController │
                                                  │                          │
                                                  │  1. Load/Create Conv     │
                                                  │  2. Reformalize Query    │
                                                  │  3. Embed → Vector Search│
                                                  │  4. Build RAG Prompt     │
                                                  │  5. LLM Generate Answer  │
                                                  │  6. Persist Messages     │
                                                  └──────────┬───────────────┘
                                                             │
                    ┌────────────────────────────────────────┼──────────────┐
                    │                                        │              │
                    ▼                                        ▼              ▼
            ┌──────────────┐                         ┌────────────┐  ┌──────────┐
            │ VectorDB     │                         │ PostgreSQL │  │ LLM      │
            │ (Qdrant /    │                         │ (Conv      │  │ (OpenAI /│
            │  pgvector)   │                         │  History)  │  │  Cohere) │
            └──────────────┘                         └────────────┘  └──────────┘
```

---

## ✨ Key Features

### 🔍 Multi-Stage RAG Pipeline
- **Document ingestion** → text extraction → recursive chunking (configurable size/overlap via LangChain) → vector embedding → batch indexing
- **Semantic search** with cosine or dot-product similarity against 384–1,536 dimension vectors
- **Context injection** into LLM prompts with strict document-adherence guardrails — zero hallucination by design

### 💬 Stateful Conversation Engine
- Full conversation history persisted in PostgreSQL as **JSONB** — no external session stores needed
- **History-aware query reformulation** resolves pronouns and references (e.g., "tell me more about *that*") before retrieval
- Automatic conversation lifecycle management: `active` → `closed` with UUID-based session tracking

### 🎫 Intelligent Ticket Summarization
- LLM-generated structured JSON tickets with title, summary, priority (`critical` / `high` / `medium` / `low`), category, and extracted customer information
- **Non-blocking SMTP dispatch** via `asyncio.to_thread` — email I/O never blocks the async event loop
- Auto-summarization on first email trigger; cached for subsequent requests

### 🔌 Provider-Agnostic Design (Factory Pattern)
- **LLM backends**: swap between OpenAI (`gpt-4o`, `text-embedding-3-small`) and Cohere (`command-r-plus`, `embed-english-v3.0`) with a single environment variable
- **Vector DB backends**: switch between Qdrant and pgvector at runtime — zero code changes
- **Mix-and-match**: use Cohere for embeddings + OpenAI for generation simultaneously
- Abstract interfaces (`LLMInterface`, `VectorDBInterface`) ensure new providers integrate in < 100 lines

### 📡 Full Observability Stack
- Custom `PrometheusMiddleware` tracks request count and latency by method, endpoint, and HTTP status
- 4 pre-built Grafana dashboards: FastAPI, Node Exporter, PostgreSQL, Qdrant
- Hidden metrics endpoint (`/TrhBVer`) excluded from Swagger docs for security

### 🖥️ Modern Frontend
- **Next.js 16 + React 19 + TypeScript** — 3 pages: Chat, Dashboard, RAG Search
- Fully-typed API client (`lib/api.ts`) wrapping all 10 backend endpoints
- Served through Nginx reverse proxy for unified port `80` access

### 🚀 CI/CD & Infrastructure
- **GitHub Actions** pipeline: push to `main` → SSH deploy → `systemctl restart` → health check with retry loop
- **9-container Docker Compose** stack with health checks, named volumes, and bridge networking
- Optional **systemd service** file for bare-metal Linux daemon deployment

---

## 🛠️ Tech Stack

### Generative AI & NLP
| Component | Technology | Rationale |
|---|---|---|
| LLM Generation | OpenAI API / Cohere API | Multi-provider flexibility; GPT-4o for accuracy, Command-R+ for cost efficiency |
| Embeddings | OpenAI `text-embedding-3-small` / Cohere `embed-english-v3.0` | 1,536-dim (OpenAI) or 1,024-dim (Cohere) dense vectors for semantic matching |
| Text Splitting | LangChain Text Splitters | Recursive character splitting with configurable chunk size & overlap |
| Prompt Engineering | LangChain Core + Custom Template Parser | Multi-locale prompt system (`$variable` substitution) with strict RAG guardrails |
| Query Reformulation | Custom + LangChain `ChatPromptTemplate` | History-aware reference resolution with hallucination guardrails |

### Backend
| Component | Technology | Rationale |
|---|---|---|
| Framework | FastAPI ≥ 0.110 | Native async/await, automatic OpenAPI docs, Pydantic validation |
| Runtime | Python 3.10+ (asyncio) | Async-first for non-blocking I/O across DB, LLM, and SMTP calls |
| Server | Uvicorn | ASGI server with hot-reload for development |
| Configuration | Pydantic Settings + `.env` | Type-safe env parsing with validation at startup |
| Metrics | Custom `PrometheusMiddleware` | Zero-dependency HTTP instrumentation (Counter + Histogram) |

### Frontend
| Component | Technology | Rationale |
|---|---|---|
| Framework | Next.js 16 | Server-side rendering, file-based routing, optimized builds |
| UI Library | React 19 | Latest concurrent rendering features |
| Language | TypeScript | Type safety across the entire API client layer |
| API Client | Typed fetch wrapper (`lib/api.ts`) | Centralized, type-safe access to all 10 backend endpoints |

### Databases
| Component | Technology | Rationale |
|---|---|---|
| Relational DB | PostgreSQL 17 (via SQLAlchemy async + asyncpg) | JSONB for flexible message storage; `asyncpg` for non-blocking queries |
| Vector DB — Option A | Qdrant v1.13.6 | Purpose-built vector search; gRPC support; native dashboard on `:6333` |
| Vector DB — Option B | pgvector 0.8.0 (PostgreSQL extension) | Zero-infrastructure vector search on existing PostgreSQL; HNSW + IVFFLAT indexes |
| Document DB | MongoDB (via Motor async driver) | Provisioned for document-oriented storage; async Motor client |
| Migrations | Alembic | Schema versioning for `projects`, `data_chunks`, `assets`, `conversations` |

### Infrastructure & DevOps
| Component | Technology | Rationale |
|---|---|---|
| Containerization | Docker + Docker Compose | 9-service orchestration with health checks and named volumes |
| Reverse Proxy | Nginx (stable-alpine) | Unified `:80` entry; 100 MB upload limit; 300s timeout for large files |
| CI/CD | GitHub Actions | Auto-deploy on `main` push via SSH + systemd restart |
| Monitoring | Prometheus v3.3.0 | Time-series metrics with auto-scraping from 3 exporters |
| Dashboards | Grafana 11.6.0 | Visualization for FastAPI, Node, PostgreSQL, and Qdrant metrics |
| Email | SMTP (smtplib + asyncio.to_thread) | Non-blocking email dispatch; supports TLS and SSL (port 465/587) |

---

## 📡 API Reference

### Base

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns API status |
| `GET` | `/api/v1` | Base router verification |

### Data Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload/{project_id}` | Stream-upload documents (PDF, etc.) with validation |
| `POST` | `/api/v1/process/{project_id}` | Extract text, chunk, and store in PostgreSQL |

### NLP & RAG Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/nlp/index/push/{project_id}` | Embed & index all chunks into vector DB (batched) |
| `GET` | `/api/v1/nlp/index/info/{project_id}` | Retrieve vector collection metadata |
| `POST` | `/api/v1/nlp/index/search/{project_id}` | Semantic similarity search |
| `POST` | `/api/v1/nlp/index/answer/{project_id}` | Full RAG: retrieve context + generate answer |

### Conversation Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/conversation/chat/{project_id}` | History-aware RAG chat with persistence |
| `POST` | `/api/v1/conversation/chat/{project_id}/close` | Close the active conversation session |
| `POST` | `/api/v1/conversation/chat/{project_id}/summarized_ticket_email` | Summarize & email support ticket |

### Observability

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/TrhBVer` | Prometheus metrics (excluded from Swagger) |

---

## 💻 API Usage Examples

### 1. Upload a Knowledge Base Document

```bash
curl -X POST "http://localhost:8000/api/v1/upload/1" \
  -F "file=@knowledge_base.pdf"
```

```json
{
  "signal": "file_upload_success",
  "file_name": "knowledge_base.pdf",
  "project_id": 1
}
```

### 2. Process & Chunk the Document

```bash
curl -X POST "http://localhost:8000/api/v1/process/1" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "knowledge_base.pdf",
    "chunk_size": 512,
    "overlap_size": 50,
    "do_rest": false
  }'
```

### 3. Index Chunks into Vector DB

```bash
curl -X POST "http://localhost:8000/api/v1/nlp/index/push/1" \
  -H "Content-Type: application/json" \
  -d '{
    "do_rest": false,
    "page_size": 50
  }'
```

```json
{
  "signal": "insert_into_vectordb_success",
  "inserted_count": 147
}
```

### 4. Chat with RAG (History-Aware)

```bash
curl -X POST "http://localhost:8000/api/v1/conversation/chat/1" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is your refund policy?",
    "limit": 5
  }'
```

```json
{
  "signal": "rag_answer_generated_success",
  "answer": "According to Document No: 3, our refund policy allows full refunds within 30 days of purchase...",
  "full_prompt": "...",
  "conversation_history": [
    { "role": "user", "content": "What is your refund policy?" },
    { "role": "assistant", "content": "According to Document No: 3..." }
  ],
  "retrieved_documents": [
    { "text": "...", "score": 0.92, "metadata": { "chunk_order": 3 } }
  ]
}
```

### 5. Close Conversation & Email Ticket

```bash
# Close the conversation
curl -X POST "http://localhost:8000/api/v1/conversation/chat/1/close"

# Generate summary and email to support team
curl -X POST "http://localhost:8000/api/v1/conversation/chat/1/summarized_ticket_email" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "support@company.com",
    "smtp_config": {}
  }'
```

```json
{
  "signal": "summarized_and_emailed_success",
  "conversation_id": 42
}
```

### 6. TypeScript Frontend Client

```typescript
import { api } from '@/lib/api';

// Upload a document
const uploadResult = await api.upload(projectId, file);

// Chat with RAG
const response = await api.chat(projectId, {
  text: "What payment methods do you accept?",
  limit: 5
});

// Email support ticket
await api.emailTicket(projectId, {
  recipient_email: "support@company.com",
  smtp_config: {}
});
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ (for frontend development) |
| Docker & Docker Compose | Latest stable |
| API Key | OpenAI or Cohere (at least one) |

### Option A — Docker Compose (Recommended)

Full-stack deployment with all 9 services in under 5 minutes.

```bash
# 1. Clone the repository
git clone https://github.com/Omar-Mahrous-am/SmartDesk-AI.git
cd SmartDesk-AI

# 2. Configure environment files
cd docker/env
cp .env.example.app .env.app
cp .env.example.postgres .env.postgres
cp .env.example.grafana .env.grafana
cp .env.example.postgres-exporter .env.postgres-exporter
cd ..

# 3. Copy Alembic config
cd minirag && cp alembic.example.ini alembic.ini && cd ..

# 4. Edit .env.app with your LLM API keys
#    Set GENERATION_BACKEND, EMBEDDING_BACKEND, OPEN_API_KEYS / COHERE_API_KEY

# 5. Launch the full stack
docker compose up --build -d
```

**Incremental startup** (recommended for first deployment):

```bash
# Start databases first — wait for healthcheck
docker compose up -d pgvector qdrant postgres-exporter
sleep 30

# Start application & observability services
docker compose up -d fastapi frontend nginx prometheus grafana node-exporter --build
```

### Option B — Local Development

```bash
# 1. Clone & install backend dependencies
git clone https://github.com/Omar-Mahrous-am/SmartDesk-AI.git
cd SmartDesk-AI
pip install -r src/requirements.txt

# 2. Configure environment
cp src/.env.example src/.env
# Edit src/.env with your credentials

# 3. Run database migrations
cd src/models/db_schemas/minirag
cp alembic.ini.example alembic.ini
# Update sqlalchemy.url in alembic.ini
alembic upgrade head
cd ../../../..

# 4. Start the backend
uvicorn src.main:app --reload

# 5. Start the frontend (separate terminal)
cd view
npm install
npm run dev
```

### Service Endpoints

| Service | URL | Notes |
|---|---|---|
| **Nginx (Entry Point)** | `http://localhost` | Unified proxy for all services |
| **FastAPI Backend** | `http://localhost:8000` | Direct API access |
| **Swagger Docs** | `http://localhost:8000/docs` | Interactive API documentation |
| **Next.js Frontend** | `http://localhost:3000` | Chat, Dashboard, RAG pages |
| **Prometheus** | `http://localhost:9090` | Metrics queries |
| **Grafana** | `http://localhost:3000` (Docker) | Dashboards (credentials in `.env.grafana`) |
| **Qdrant Dashboard** | `http://localhost:6333/dashboard` | Vector DB admin |

---

## ⚙️ Configuration

### Environment Variables

<details>
<summary><strong>Click to expand full configuration reference</strong></summary>

```env
# ══════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════
APP_NAME="SmartDesk-AI"
VERSION="0.1"
FILE_DEFAULT_CHUNK_SIZE=1048576          # 1 MB streaming chunk size

# ══════════════════════════════════════════
# POSTGRESQL (Relational DB + pgvector)
# ══════════════════════════════════════════
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost                   # Use 'pgvector' inside Docker
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE=minirag

# ══════════════════════════════════════════
# LLM — GENERATION
# ══════════════════════════════════════════
GENERATION_BACKEND=OPENAI                 # OPENAI | COHERE
GENERATION_MODEL_ID=gpt-4o
GENERATION_DEFAULT_MAX_TOKENS=200
GENERATION_DEFAULT_TEMPERATURE=0.1
INPUT_DEFAULT_MAX_CHARACTERS=1024

# ══════════════════════════════════════════
# LLM — EMBEDDINGS (can differ from generation)
# ══════════════════════════════════════════
EMBEDDING_BACKEND=COHERE                  # OPENAI | COHERE
EMBEDDING_MODEL_ID=embed-english-v3.0
EMBEDDING_MODEL_SIZE=1024                 # 1024 (Cohere) or 1536 (OpenAI)

# ══════════════════════════════════════════
# OPENAI CREDENTIALS
# ══════════════════════════════════════════
OPEN_API_KEYS=sk-...
OPEN_API_URL=https://api.openai.com/v1

# ══════════════════════════════════════════
# COHERE CREDENTIALS
# ══════════════════════════════════════════
COHERE_API_KEY=...

# ══════════════════════════════════════════
# VECTOR DATABASE
# ══════════════════════════════════════════
VECTOR_DB_BACKEND=QDRANT                  # QDRANT | PGVECTOR
VECTOR_DB_PATH=qdrant_db
VECTOR_DB_DISTANCE_METHOD=cosine          # cosine | dot
VECTOR_DB_PGVEC_INDEX_THRESHOLD=100       # Records before auto-indexing
VECTOR_DB_DEFAULT_VECTOR_SIZE=1024

# ══════════════════════════════════════════
# PROMPT TEMPLATES
# ══════════════════════════════════════════
DEFAULT_LANGUAGE=en
PRIMARY_LANGUAGE=en

# ══════════════════════════════════════════
# SMTP EMAIL
# ══════════════════════════════════════════
SMTP_SERVER=sandbox.smtp.mailtrap.io
SMTP_PORT=2525                            # 465 for SSL, 587 for TLS
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_SENDER=support@smartdesk.ai
SMTP_USE_TLS=True
```

</details>

### Vector DB Backend Configuration

Switch vector databases with **zero code changes** — only the environment variable matters:

<details>
<summary><strong>Qdrant Configuration</strong></summary>

```env
VECTOR_DB_BACKEND=QDRANT
VECTOR_DB_PATH=qdrant_db
VECTOR_DB_DISTANCE_METHOD=cosine
```

- Containerized via `qdrant/qdrant:v1.13.6` on ports `6333` (HTTP) and `6334` (gRPC)
- Native dashboard at `http://localhost:6333/dashboard`
- Collections created/deleted per project

</details>

<details>
<summary><strong>pgvector Configuration</strong></summary>

```env
VECTOR_DB_BACKEND=PGVECTOR
VECTOR_DB_DISTANCE_METHOD=cosine
VECTOR_DB_PGVEC_INDEX_THRESHOLD=100
VECTOR_DB_DEFAULT_VECTOR_SIZE=384
```

- Runs on the same PostgreSQL instance — zero additional infrastructure
- Auto-selects between `IVFFLAT` and `HNSW` index methods based on record count vs. threshold
- Collections stored as SQL tables prefixed with `pgvector_`

</details>

Both backends implement the same `VectorDBInterface` contract:

```python
class VectorDBInterface(ABC):
    def connect() / dis_connect()
    def create_collection() / delete_collection()
    def insert_many_collections()
    def search_by_vector() → List[RetrivedDocument]
    def get_collection_info()
```

### LLM Provider Configuration

Generation and embedding providers are **independently configurable** — mix-and-match freely:

| Configuration | OpenAI | Cohere |
|---|---|---|
| `GENERATION_BACKEND` | `OPENAI` | `COHERE` |
| `GENERATION_MODEL_ID` | `gpt-4o` | `command-r-plus` |
| `EMBEDDING_BACKEND` | `OPENAI` | `COHERE` |
| `EMBEDDING_MODEL_ID` | `text-embedding-3-small` | `embed-english-v3.0` |
| `EMBEDDING_MODEL_SIZE` | `1536` | `1024` |

> **Example**: Use Cohere `embed-english-v3.0` for cost-effective embeddings and OpenAI `gpt-4o` for high-quality generation — both simultaneously.

---

## 🐳 Docker Infrastructure

### Service Matrix

| Service | Image | Port(s) | Purpose |
|---|---|---|---|
| `fastapi` | Custom (Dockerfile) | `8000` | Async API backend |
| `frontend` | Custom (view/Dockerfile) | — | Next.js SSR frontend |
| `nginx` | `nginx:stable-alpine3.20-perl` | `80` | Reverse proxy + load balancer |
| `pgvector` | `pgvector/pgvector:0.8.0-pg17` | `5432` | Relational DB + vector extension |
| `qdrant` | `qdrant/qdrant:v1.13.6` | `6333`, `6334` | Vector DB (HTTP + gRPC) |
| `prometheus` | `prom/prometheus:v3.3.0` | `9090` | Metrics collection |
| `grafana` | `grafana/grafana:11.6.0-ubuntu` | `3000` | Metrics dashboards |
| `node-exporter` | `prom/node-exporter:v1.9.1` | `9100` | System metrics (CPU, RAM, Disk) |
| `postgres-exporter` | `prometheuscommunity/postgres-exporter:v0.17.1` | `9187` | PostgreSQL metrics |

### Docker Commands

```bash
cd docker

# Full lifecycle
docker compose up --build -d              # Build & start all services
docker compose down                        # Stop services (keep data)
docker compose down -v                     # Stop & remove volumes
docker compose down -v --remove-orphans    # Full cleanup

# Logs
docker compose logs fastapi -f             # Stream FastAPI logs
docker compose logs --tail=100             # Last 100 lines from all services
```

### Systemd Deployment (Linux)

```bash
sudo cp docker/minirag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable minirag
sudo systemctl start minirag

# Verify
sudo systemctl status minirag
```

---

## 📁 Project Structure

```
SmartDesk-AI/
├── .github/
│   └── workflows/
│       └── deploy-main.yaml               # CI/CD: SSH deploy on push to main
├── docker/
│   ├── docker-compose.yml                 # 9-service orchestration
│   ├── minirag.service                    # Systemd unit file
│   ├── env/                               # Per-service environment files
│   │   ├── .env.example.app
│   │   ├── .env.example.postgres
│   │   ├── .env.example.grafana
│   │   └── .env.example.postgres-exporter
│   ├── minirag/
│   │   ├── Dockerfile                     # FastAPI container
│   │   └── alembic.example.ini
│   ├── nginx/
│   │   └── default.conf                   # Reverse proxy rules
│   └── prometheus/
│       └── prometheus.yml                 # Scrape configuration
├── view/                                  # Next.js 16 + React 19 + TypeScript
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── app/
│       │   ├── chat/                      # Chat UI page
│       │   ├── dashboard/                 # Project management page
│       │   └── rag/                       # RAG search/answer page
│       ├── components/                    # Reusable UI components
│       ├── context/                       # React context providers
│       └── lib/
│           └── api.ts                     # Typed API client (10 endpoints)
├── src/
│   ├── main.py                            # App entry: lifespan, CORS, metrics, routes
│   ├── requirements.txt                   # 24 Python dependencies
│   ├── .env.example
│   ├── helpers/
│   │   └── config.py                      # Pydantic Settings (30+ env vars)
│   ├── routes/
│   │   ├── base.py                        # Health check endpoint
│   │   ├── data.py                        # Upload & process endpoints
│   │   ├── nlp.py                         # RAG indexing & search endpoints
│   │   └── conversation.py                # Chat, close, email ticket endpoints
│   ├── controllers/
│   │   ├── BaseController.py              # Abstract controller base
│   │   ├── DataController.py              # File validation & path generation
│   │   ├── NLPController.py               # RAG logic (index, search, answer)
│   │   ├── ConversationNLPController.py   # History-aware RAG + summarization + email
│   │   ├── ProcessController.py           # File extraction & chunking
│   │   └── ProjectController.py           # Project path management
│   ├── models/
│   │   ├── ProjectModel.py                # Project CRUD operations
│   │   ├── ChunkModel.py                  # Chunk operations (paginated)
│   │   ├── AssetModel.py                  # Asset CRUD operations
│   │   ├── ConversationModel.py           # Conversation CRUD + close logic
│   │   ├── enums/                         # Collection names, status enums, signals
│   │   └── db_schemas/
│   │       └── minirag/
│   │           ├── schemas/               # SQLAlchemy ORM models
│   │           └── alembic/               # Migration scripts
│   ├── schemas/                           # Pydantic request/response models
│   ├── stores/
│   │   ├── llm/
│   │   │   ├── LLMInterface.py            # Abstract LLM contract
│   │   │   ├── LLMProviderFactory.py      # Factory: OPENAI | COHERE
│   │   │   ├── providers/
│   │   │   │   ├── open_ai_provider.py    # OpenAI implementation
│   │   │   │   └── CoHereProvider.py      # Cohere implementation
│   │   │   └── templates/
│   │   │       ├── template_parser.py     # Multi-locale template engine
│   │   │       └── locales/en/            # English prompt templates
│   │   └── vectordb/
│   │       ├── VectorDBInterface.py       # Abstract VectorDB contract
│   │       ├── VectorDBProviderFactory.py # Factory: QDRANT | PGVECTOR
│   │       └── providers/
│   │           ├── QdrantDBProvider.py    # Qdrant implementation
│   │           └── PGVectorProvider.py    # pgvector implementation
│   └── utils/
│       └── metrics.py                     # PrometheusMiddleware + setup_metrics()
└── knowledge_base.pdf                     # Sample knowledge base document
```

---

## 🗄️ Database Migrations (Alembic)

Alembic manages schema versioning for 4 PostgreSQL tables: `projects`, `data_chunks`, `assets`, `conversations`.

```bash
cd src/models/db_schemas/minirag

# First-time setup
cp alembic.ini.example alembic.ini
# Edit alembic.ini → sqlalchemy.url = postgresql+psycopg2://user:pass@host/db

# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Roll back one step
alembic downgrade -1
```

---

## 📈 Observability & Monitoring

### Prometheus Metrics

The custom `PrometheusMiddleware` instruments every HTTP request:

| Metric | Type | Labels | Description |
|---|---|---|---|
| `http_request_total` | Counter | `method`, `endpoint`, `status` | Total request count |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request latency distribution |

### Grafana Dashboards

After Grafana is running at `http://localhost:3000`, add Prometheus as a data source (`http://prometheus:9090`) and import these community dashboards:

| Dashboard | Grafana ID | Description |
|---|---|---|
| FastAPI Observability | [18739](https://grafana.com/grafana/dashboards/18739) | Request rates, latencies, error rates |
| Node Exporter Full | [1860](https://grafana.com/grafana/dashboards/1860) | CPU, memory, disk, network |
| Qdrant | [23033](https://grafana.com/grafana/dashboards/23033) | Vector operations, collection stats |
| PostgreSQL Exporter | [12485](https://grafana.com/grafana/dashboards/12485) | Query performance, connection pools |

---

## 🔄 Workflow

```text
Step 1          Step 2              Step 3           Step 4            Step 5           Step 6
Upload ───────► Process ──────────► Index ─────────► Chat ───────────► Close ─────────► Email
  PDF             Extract text        Embed chunks     Query + RAG       Mark closed      Summarize
  Validate        Split chunks        Batch upsert     History-aware     Session ends     Send SMTP
  Store           Save to DB          Vector DB        Persist msgs                       JSON ticket
```

| Step | Endpoint | What Happens |
|---|---|---|
| **1. Upload** | `POST /api/v1/upload/{id}` | Stream file to disk; validate type & size; create asset record |
| **2. Process** | `POST /api/v1/process/{id}` | Extract text (PyPDF); recursive chunking (LangChain); store chunks in PostgreSQL |
| **3. Index** | `POST /api/v1/nlp/index/push/{id}` | Embed chunks via configured provider; paginated batch upsert into vector DB |
| **4. Chat** | `POST /api/v1/conversation/chat/{id}` | Reformalize query → embed → similarity search → inject context → LLM generate → persist |
| **5. Close** | `POST /api/v1/conversation/chat/{id}/close` | Set conversation status to `closed` |
| **6. Email** | `POST /api/v1/conversation/chat/{id}/summarized_ticket_email` | Auto-summarize → structured JSON ticket → SMTP dispatch |

---

## 🗺️ Roadmap

- [x] Core RAG pipeline with multi-provider support
- [x] History-aware conversational retrieval
- [x] LLM-powered ticket summarization with JSON output
- [x] SMTP email automation (async, non-blocking)
- [x] Prometheus + Grafana observability stack
- [x] Next.js 16 frontend with typed API client
- [x] Nginx reverse proxy with Docker Compose orchestration
- [x] GitHub Actions CI/CD pipeline
- [ ] Fine-tuned FLAN-T5 (LoRA/PEFT on DialogSum) for local summarization
- [ ] Sentiment analysis & priority classification (ML-based)
- [ ] Customer-facing confirmation email after ticket creation
- [ ] Customer satisfaction survey integration
- [ ] AWS EC2 / ECS deployment configuration
- [ ] Rate limiting & API key authentication (JWT)
- [ ] WebSocket support for real-time streaming responses

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/Omar-Mahrous-am">Omar Mahrous</a></strong>
</p>
