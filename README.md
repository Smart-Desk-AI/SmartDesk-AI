# SmartDesk-AI

> **AI-Powered Customer Support System** using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs)

SmartDesk AI is a production-ready full-stack platform that combines RAG, multi-provider LLMs, conversation management, ticket summarization, email automation, a Next.js frontend, and a complete observability stack — all built on a clean, modular, provider-agnostic architecture.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [What Has Been Built](#what-has-been-built)
- [Technology Stack](#technology-stack)
- [Database Support](#database-support)
- [Vector Database Support](#vector-database-support)
- [LLM Provider Support](#llm-provider-support)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Docker Setup](#docker-setup)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Monitoring & Observability](#monitoring--observability)
- [Frontend (Next.js)](#frontend-nextjs)
- [Workflow](#workflow)
- [Roadmap](#roadmap--upcoming-features)

---

## Architecture Overview

```text
                          ┌──────────────────────────────────────┐
                          │          Nginx Reverse Proxy          │
                          │        (Port 80 — entry point)        │
                          └──────────┬───────────────┬────────────┘
                                     │               │
                              /api/* │               │ /* (UI)
                                     ▼               ▼
                             FastAPI Backend    Next.js Frontend
                             (Async, Port 8000)  (Port 3000)
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                       │
              ▼                      ▼                       ▼
        RAG Pipeline        Conversation Manager     Prometheus Metrics
              │                      │               (PrometheusMiddleware)
    ┌─────────┴───────┐    ┌─────────┴──────┐
    ▼                 ▼    ▼                ▼
Qdrant            pgvector  PostgreSQL   SMTP Email
(Vector DB)     (pgvector)  (SQLAlchemy)  (asyncio)
                              │
                     Projects / Conversations
                     DataChunks / Assets (JSONB)

==============================================

When Conversation Ends:
      │
      ▼
ConversationNLPController
      │
      +──> Summarize Conversation (LLM)
      │
      +──> Store Summary in PostgreSQL
      │
      +──> Email Ticket to Customer Service (SMTP)

==============================================

Observability Stack:
  Prometheus (scrapes /metrics) ──> Grafana Dashboards
  Node Exporter (system metrics)
  Postgres Exporter (PostgreSQL metrics)
```

---

## What Has Been Built

### ✅ Core RAG Pipeline
- **File Upload**: Streaming upload endpoint for PDF and other documents with validation, chunking, and storage
- **Text Processing**: LangChain-based document loading and recursive text splitting with configurable chunk size and overlap
- **Vector Indexing**: Paginated batch indexing of document chunks into the chosen vector database (Qdrant or pgvector)
- **Semantic Search**: Query embedding + cosine/dot-product similarity search against indexed collections
- **RAG Answer Generation**: Retrieved context is injected into an LLM prompt to produce grounded, knowledge-base-aware answers

### ✅ Conversation Management
- **Persistent Conversations**: Each project has a conversation session backed by PostgreSQL with JSONB message storage
- **History-Aware Retrieval**: Conversation history is reformalized by the LLM before retrieval so queries are context-aware
- **Conversation Lifecycle**: Active/closed status tracking per conversation with UUID for external reference
- **State Persistence**: Appends new user/assistant messages to the existing conversation or creates a new one automatically

### ✅ Ticket Summarization & Email Automation
- **Auto-Summarization**: When a ticket email is triggered, the full conversation is summarized by the LLM if no summary exists yet
- **SMTP Email**: Sends a structured support ticket email (conversation ID, UUID, project ID, summary) to the customer service team
- **Non-blocking**: SMTP I/O is offloaded to a thread pool (`asyncio.to_thread`) to avoid blocking the async event loop

### ✅ Provider-Agnostic Architecture
- **VectorDB Factory**: Runtime selection between `QDRANT` and `PGVECTOR` via a single env variable
- **LLM Factory**: Runtime selection between `OPENAI` and `COHERE` for both generation and embedding clients, independently configurable
- **Interface-based design**: Both `VectorDBInterface` and `LLMInterface` define abstract contracts, making it trivial to plug in new providers

### ✅ Data Modeling (PostgreSQL via SQLAlchemy)
- **Projects**: Auto-incremented IDs + UUIDs, with ORM relationships to chunks, assets, and conversations
- **DataChunks**: Text content, metadata (JSONB), chunk order, and foreign keys to project and asset
- **Assets**: File metadata (name, size, type enum) linked to projects
- **Conversations**: UUID, title, full JSONB message history, status enum (active/closed), LLM-generated summary ticket, timestamps

### ✅ Database Migrations
- **Alembic** is configured under `src/models/db_schemas/minirag/` for schema versioning and migration management

### ✅ Prompt Template System
- Multi-locale template parser supporting `en` (and extensible to other languages)
- Templates for: `system_prompt`, `document_prompt`, `footer_prompt`, `summary_ticket_prompt`, and query reformalization via LangChain

### ✅ Monitoring & Observability
- **Prometheus Middleware**: Custom `PrometheusMiddleware` in `src/utils/metrics.py` tracks HTTP request counts and latency by method, endpoint, and status code
- **Metrics Endpoint**: Exposed via `setup_metrics(app)` — scraped automatically by Prometheus
- **Grafana**: Visualization dashboards for FastAPI, PostgreSQL, Qdrant, and system metrics
- **Node Exporter**: System-level metrics (CPU, memory, disk)
- **Postgres Exporter**: PostgreSQL-specific metrics fed into Prometheus

### ✅ CORS Support
- **CORSMiddleware** configured to allow requests from `http://localhost:3000` and `http://127.0.0.1:3000` (the Next.js dev server)

### ✅ Next.js Frontend
- Full **Next.js 16 + React 19** frontend in the `view/` directory
- Pages: **Chat** (`/chat`), **Dashboard** (`/dashboard`), **RAG** (`/rag`)
- Typed API client (`view/src/lib/api.ts`) wrapping all 10 backend endpoints
- Containerized via `view/Dockerfile` and served through the Nginx reverse proxy

### ✅ Docker Infrastructure
- **Fully containerized** stack: FastAPI, Next.js frontend, Nginx, pgvector, Qdrant, Prometheus, Grafana, Node Exporter, Postgres Exporter
- All services share a `backend` bridge network with named Docker volumes for persistence
- Structured `env/` directory for per-service environment files
- FastAPI waits for pgvector to pass a healthcheck before starting (`depends_on: condition: service_healthy`)
- Optional **systemd service** file (`docker/minirag.service`) for running as a Linux daemon

---

## Technology Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI ≥ 0.110 |
| Runtime | Python (asyncio / async-first) |
| Server | Uvicorn |
| Configuration | Pydantic Settings + `.env` |
| CORS | FastAPI CORSMiddleware |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 16 |
| UI Library | React 19 |
| Language | TypeScript |
| API Client | Typed fetch wrapper (`lib/api.ts`) |

### AI & NLP
| Component | Technology |
|---|---|
| LLM Generation | OpenAI API / Cohere API |
| Embeddings | OpenAI Embeddings / Cohere Embeddings |
| Document Splitting | LangChain Text Splitters |
| Prompt Templates | LangChain Core + custom locale parser |
| Conversation Reformalization | LangChain prompt chains |

### Databases
| Component | Technology |
|---|---|
| Relational DB | PostgreSQL (via SQLAlchemy async + asyncpg) |
| Document DB | MongoDB (via Motor async driver) |
| Migrations | Alembic |

### Vector Databases
| Component | Technology |
|---|---|
| Option A | Qdrant (via qdrant-client, containerized) |
| Option B | pgvector (PostgreSQL extension, via pgvector + SQLAlchemy) |

### Infrastructure & Observability
| Component | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx (stable-alpine) |
| Metrics | Prometheus + prometheus-client |
| Dashboards | Grafana |
| System Metrics | Node Exporter |
| DB Metrics | Postgres Exporter |
| Email | SMTP (smtplib, async via asyncio.to_thread) |

---

## Database Support

SmartDesk AI supports **two primary database backends** for storing structured data. Both can coexist:

### PostgreSQL (Primary — Relational)

Used via **SQLAlchemy async ORM** (`asyncpg` driver). Manages:

- `projects` table — project registry
- `data_chunks` table — text chunks with metadata
- `assets` table — uploaded file records
- `conversations` table — full message history (JSONB), status, and summaries

PostgreSQL is also used for **pgvector** (see below).

### MongoDB (Document Store — via Motor)

MongoDB is provisioned in Docker and supported via the async **Motor** client. It serves as the document store for:

- Project metadata
- Text chunks
- Asset records

The `DataBaseEnum` and model classes abstract the collection names (`projects`, `chunks`, `assets`) for consistency.

> **Note**: The current primary runtime path uses **PostgreSQL** for relational data. MongoDB is provisioned and supported by the data models but the main conversation flow operates over PostgreSQL.

---

## Vector Database Support

The vector database backend is selected **at runtime** via the `VECTOR_DB_BACKEND` environment variable. No code changes are required to switch providers.

### Qdrant

```env
VECTOR_DB_BACKEND=QDRANT
VECTOR_DB_PATH=qdrant_db
VECTOR_DB_DISTANCE_METHOD=cosine
```

- Available as a **Docker service** (`qdrant/qdrant:v1.13.6`) on ports `6333` (HTTP) and `6334` (gRPC)
- Supports cosine and dot-product distance
- Collections are created and deleted per project
- Dashboard: `http://localhost:6333/dashboard`

### pgvector (PostgreSQL Extension)

```env
VECTOR_DB_BACKEND=PGVECTOR
VECTOR_DB_DISTANCE_METHOD=cosine
VECTOR_DB_PGVEC_INDEX_THRESHOLD=100
VECTOR_DB_DEFAULT_VECTOR_SIZE=384
```

- Runs on the same PostgreSQL instance used for relational data
- Supports `IVFFLAT` and `HNSW` index methods
- Collections are SQL tables prefixed with `pgvector_`
- Indexing strategy: auto-selects index method based on record count vs. threshold

Both providers implement the same `VectorDBInterface` contract:

- `connect()` / `disconnect()`
- `create_collection()` / `delete_collection()`
- `insert_many_collections()`
- `search_by_vector()`
- `get_collection_info()`

---

## LLM Provider Support

Both the **generation** and **embedding** clients are independently configurable via env variables.

### OpenAI

```env
GENERATION_BACKEND=OPENAI
OPEN_API_KEYS=sk-...
OPEN_API_URL=https://api.openai.com/v1
GENERATION_MODEL_ID=gpt-4o
EMBEDDING_BACKEND=OPENAI
EMBEDDING_MODEL_ID=text-embedding-3-small
EMBEDDING_MODEL_SIZE=1536
```

### Cohere

```env
GENERATION_BACKEND=COHERE
COHERE_API_KEY=...
GENERATION_MODEL_ID=command-r-plus
EMBEDDING_BACKEND=COHERE
EMBEDDING_MODEL_ID=embed-english-v3.0
EMBEDDING_MODEL_SIZE=1024
```

> You can mix providers — e.g., use **Cohere for embeddings** and **OpenAI for generation** simultaneously.

---

## API Endpoints

### Base

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check / API status |
| GET | `/api/v1` | Base router check |

### Data Management (`/api/v1`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/upload/{project_id}` | Stream-upload a file (PDF, etc.) for a project |
| POST | `/api/v1/process/{project_id}` | Extract text, split into chunks, store in DB |

### NLP & RAG (`/api/v1/nlp`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/nlp/index/push/{project_id}` | Embed and index all chunks into the vector DB |
| GET | `/api/v1/nlp/index/info/{project_id}` | Retrieve vector collection metadata |
| POST | `/api/v1/nlp/index/search/{project_id}` | Semantic similarity search |
| POST | `/api/v1/nlp/index/answer/{project_id}` | Full RAG: retrieve context + generate answer |

### Conversation (`/api/v1/conversation`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/conversation/chat/{project_id}` | History-aware RAG chat with conversation persistence |
| POST | `/api/v1/conversation/chat/{project_id}/close` | Close the active conversation |
| POST | `/api/v1/conversation/chat/{project_id}/summarized_ticket_email` | Summarize conversation and email ticket to support team |

### Observability

| Method | Endpoint | Description |
|---|---|---|
| GET | `/TrhBVer` | Prometheus metrics scrape endpoint (hidden from docs) |

---

## Project Structure

```
SmartDesk-AI/
├── docker/
│   ├── docker-compose.yml          # Full stack: FastAPI, Frontend, Nginx, pgvector,
│   │                               #   Qdrant, Prometheus, Grafana, Node/Postgres Exporters
│   ├── minirag.service             # Systemd service file for Linux daemon deployment
│   ├── env/
│   │   ├── .env.example.app        # FastAPI app env template
│   │   ├── .env.example.postgres   # PostgreSQL env template
│   │   ├── .env.example.grafana    # Grafana env template
│   │   └── .env.example.postgres-exporter
│   ├── minirag/
│   │   ├── Dockerfile              # FastAPI container image
│   │   └── alembic.example.ini
│   ├── nginx/
│   │   └── default.conf            # Reverse proxy (/ → frontend, /api → FastAPI)
│   └── prometheus/
│       └── prometheus.yml          # Prometheus scrape config
├── view/                           # Next.js 16 + React 19 frontend
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── app/
│       │   ├── chat/               # Chat UI page
│       │   ├── dashboard/          # Project dashboard page
│       │   └── rag/                # RAG search/answer page
│       ├── components/
│       │   ├── chat/
│       │   ├── dashboard/
│       │   ├── layout/
│       │   └── rag/
│       ├── context/                # React context providers
│       └── lib/
│           └── api.ts              # Typed API client (wraps all 10 backend endpoints)
├── src/
│   ├── main.py                     # FastAPI app, lifespan events, CORS, metrics, routes
│   ├── requirements.txt
│   ├── .env.example
│   ├── utils/
│   │   └── metrics.py              # PrometheusMiddleware + setup_metrics()
│   ├── helpers/
│   │   └── config.py               # Pydantic Settings (all env vars)
│   ├── routes/
│   │   ├── base.py                 # Health check
│   │   ├── data.py                 # Upload & process endpoints
│   │   ├── nlp.py                  # RAG indexing & search endpoints
│   │   └── conversation.py         # Chat, close, and email ticket endpoints
│   ├── controllers/
│   │   ├── BaseController.py
│   │   ├── DataController.py       # File validation & path generation
│   │   ├── NLPController.py        # RAG logic (index, search, answer)
│   │   ├── ConversationNLPController.py  # History-aware RAG + summarization + email
│   │   ├── ProcessController.py    # File content extraction & chunking
│   │   └── ProjectController.py    # Project path management
│   ├── models/
│   │   ├── ProjectModel.py         # Project DB operations
│   │   ├── ChunkModel.py           # Chunk DB operations (paginated)
│   │   ├── AssetModel.py           # Asset DB operations
│   │   ├── ConversationModel.py    # Conversation CRUD + close logic
│   │   ├── MessagesModel.py        # Messages model (stub)
│   │   ├── BaseDataModel.py
│   │   ├── enums/
│   │   │   ├── DataBaseEnum.py     # Collection names, ConversationStatusEnum
│   │   │   ├── AssetTypeEnum.py
│   │   │   └── ResponseSignal.py   # Standardized API response signals
│   │   └── db_schemas/
│   │       └── minirag/
│   │           ├── alembic/        # Migration scripts
│   │           ├── alembic.ini
│   │           └── schemas/
│   │               ├── project.py
│   │               ├── datachunk.py
│   │               ├── asset.py
│   │               └── conversation.py
│   ├── schemas/
│   │   ├── data.py                 # ProcessRequest Pydantic model
│   │   ├── nlp.py                  # PushRequest, SearchRequest Pydantic models
│   │   └── conversation.py
│   ├── stores/
│   │   ├── llm/
│   │   │   ├── LLMEnums.py         # LLMEnums, OPENAIEnums, COHEREEnums, DocumentTypeEnum
│   │   │   ├── LLMInterface.py     # Abstract LLM interface
│   │   │   ├── LLMProviderFactory.py  # Factory: OPENAI | COHERE
│   │   │   ├── providers/
│   │   │   │   ├── open_ai_provider.py
│   │   │   │   └── CoHereProvider.py
│   │   │   └── templates/
│   │   │       ├── template_parser.py
│   │   │       └── locales/en/     # Prompt templates (RAG, summary, reformalize)
│   │   └── vectordb/
│   │       ├── VectorDBEnums.py    # VectorDBEnum, distance/index method enums
│   │       ├── VectorDBInterface.py   # Abstract VectorDB interface
│   │       ├── VectorDBProviderFactory.py  # Factory: QDRANT | PGVECTOR
│   │       └── providers/
│   │           ├── QdrantDBProvider.py
│   │           └── PGVectorProvider.py
│   └── assets/                     # Uploaded file storage (per project)
└── knowledge_base.pdf              # Sample knowledge base document
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend development)
- Docker & Docker Compose
- PostgreSQL (or use the Docker service)
- An OpenAI or Cohere API key

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-org/SmartDesk-AI.git
cd SmartDesk-AI

# Backend
pip install -r src/requirements.txt

# Frontend (optional, for local dev)
cd view && npm install && cd ..
```

### 2. Configure Environment

```bash
cp src/.env.example src/.env
# Edit src/.env with your credentials (see Environment Variables section)
```

### 3. Start Infrastructure (Docker — Recommended)

```bash
cd docker

# Copy and fill in per-service environment files
cd env
cp .env.example.app .env.app
cp .env.example.postgres .env.postgres
cp .env.example.grafana .env.grafana
cp .env.example.postgres-exporter .env.postgres-exporter
cd ..

# Copy Alembic config
cd minirag && cp alembic.example.ini alembic.ini && cd ..

# Start everything
docker compose up --build -d
```

To start services incrementally (recommended first time):

```bash
# Start databases first
docker compose up -d pgvector qdrant postgres-exporter
sleep 30
# Start remaining services
docker compose up -d fastapi frontend nginx prometheus grafana node-exporter --build
```

### 4. Run Database Migrations (local dev)

```bash
cd src/models/db_schemas/minirag
cp alembic.ini.example alembic.ini
# Update sqlalchemy.url in alembic.ini to your PostgreSQL connection string

alembic upgrade head
```

### 5. Start the Server (local dev)

```bash
# Backend
uvicorn src.main:app --reload

# Frontend (in a separate terminal)
cd view && npm run dev
```

| Service | URL |
|---|---|
| FastAPI API | `http://localhost:8000` |
| Swagger Docs | `http://localhost:8000/docs` |
| Next.js Frontend | `http://localhost:3000` |
| Nginx (entry point) | `http://localhost` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` (via Docker) |
| Qdrant Dashboard | `http://localhost:6333/dashboard` |

---

## Environment Variables

```env
# App
APP_NAME="SmartDesk-AI"
VERSION="0.1"
FILE_DEFAULT_CHUNK_SIZE=1048576    # 1 MB streaming chunk

# PostgreSQL (Relational DB + pgvector)
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_MAIN_DATABASE=minirag

# LLM — Generation
GENERATION_BACKEND=OPENAI          # OPENAI | COHERE
GENERATION_MODEL_ID=gpt-4o
GENERATION_DEFAULT_MAX_TOKENS=200
GENERATION_DEFAULT_TEMPERATURE=0.1
INPUT_DEFAULT_MAX_CHARACTERS=1024

# LLM — Embeddings (can be different from generation backend)
EMBEDDING_BACKEND=COHERE           # OPENAI | COHERE
EMBEDDING_MODEL_ID=embed-english-v3.0
EMBEDDING_MODEL_SIZE=1024

# OpenAI (if GENERATION_BACKEND or EMBEDDING_BACKEND = OPENAI)
OPEN_API_KEYS=sk-...
OPEN_API_URL=https://api.openai.com/v1

# Cohere (if GENERATION_BACKEND or EMBEDDING_BACKEND = COHERE)
COHERE_API_KEY=...

# Vector DB
VECTOR_DB_BACKEND=QDRANT           # QDRANT | PGVECTOR
VECTOR_DB_PATH=qdrant_db           # Local path for Qdrant
VECTOR_DB_DISTANCE_METHOD=cosine   # cosine | dot
VECTOR_DB_PGVEC_INDEX_THRESHOLD=100
VECTOR_DB_DEFAULT_VECTOR_SIZE=1024

# Prompt Templates
DEFAULT_LANGUAGE=en
PRIMARY_LANGUAGE=en

# SMTP Email
SMTP_SERVER=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_SENDER=support@smartdesk.ai
SMTP_USE_TLS=True
```

---

## Docker Setup

The `docker/docker-compose.yml` provisions the full stack:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `fastapi` | Custom (Dockerfile) | `8000:8000` | FastAPI backend |
| `frontend` | Custom (view/Dockerfile) | — | Next.js frontend (served via Nginx) |
| `nginx` | `nginx:stable-alpine3.20-perl` | `80:80` | Reverse proxy (`/api/*` → FastAPI, `/*` → frontend) |
| `pgvector` | `pgvector/pgvector:0.8.0-pg17` | `5432:5432` | Relational DB + vector similarity search |
| `qdrant` | `qdrant/qdrant:v1.13.6` | `6333:6333`, `6334:6334` | Vector DB (HTTP + gRPC) |
| `prometheus` | `prom/prometheus:v3.3.0` | `9090:9090` | Metrics collection |
| `grafana` | `grafana/grafana:11.6.0-ubuntu` | `3000:3000` | Metrics visualization |
| `node-exporter` | `prom/node-exporter:v1.9.1` | `9100:9100` | System-level metrics |
| `postgres-exporter` | `prometheuscommunity/postgres-exporter:v0.17.1` | `9187:9187` | PostgreSQL metrics |

All services share a `backend` bridge network and use named Docker volumes for data persistence.

```bash
cd docker
docker compose up --build -d          # Start all services
docker compose down                   # Stop services
docker compose down -v                # Stop and remove volumes
docker compose down -v --remove-orphans  # Full cleanup
```

### Systemd Deployment (Linux)

A `minirag.service` file is provided for running the full stack as a Linux system service:

```bash
sudo cp docker/minirag.service /etc/systemd/system/
sudo systemctl enable minirag
sudo systemctl start minirag
```

---

## Database Migrations (Alembic)

Alembic manages the PostgreSQL schema (`projects`, `data_chunks`, `assets`, `conversations` tables).

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

## Monitoring & Observability

### Prometheus Metrics

FastAPI exposes Prometheus metrics via the `PrometheusMiddleware` in `src/utils/metrics.py`:

- **`http_request_total`** — Counter by `method`, `endpoint`, `status`
- **`http_request_duration_seconds`** — Histogram by `method`, `endpoint`

Prometheus scrapes these automatically based on `docker/prometheus/prometheus.yml`.

### Grafana Dashboards

After starting Grafana at `http://localhost:3000` (credentials set in `.env.grafana`):

1. Add Prometheus as a data source: `http://prometheus:9090`
2. Import community dashboards:

| Dashboard | URL |
|---|---|
| FastAPI Observability | https://grafana.com/grafana/dashboards/18739 |
| Node Exporter Full | https://grafana.com/grafana/dashboards/1860 |
| Qdrant | https://grafana.com/grafana/dashboards/23033 |
| PostgreSQL Exporter | https://grafana.com/grafana/dashboards/12485 |

---

## Frontend (Next.js)

The `view/` directory contains a **Next.js 16 + React 19 + TypeScript** frontend.

### Pages

| Route | Description |
|---|---|
| `/` | Landing / redirect |
| `/dashboard` | Project management dashboard |
| `/chat` | History-aware RAG chat interface |
| `/rag` | Direct RAG search and answer panel |

### Typed API Client

`view/src/lib/api.ts` provides a fully-typed client wrapping all 10 backend endpoints:

```typescript
import { api } from '@/lib/api';

// Upload a file
const result = await api.upload(projectId, file);

// History-aware chat
const response = await api.chat(projectId, { text: "What is your refund policy?" });

// Email ticket
await api.emailTicket(projectId, { recipient_email: "support@company.com", smtp_config: {} });
```

### Running the Frontend Locally

```bash
cd view
npm install
npm run dev   # http://localhost:3000
```

Override the backend URL:

```env
# view/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The Nginx reverse proxy (Docker) routes all traffic through port `80`:
- `http://localhost/` → Next.js frontend
- `http://localhost/api/*` → FastAPI backend

---

## Workflow

### Step 1 — Upload Knowledge Base
`POST /api/v1/upload/{project_id}` — Upload PDFs or documents. Files are streamed to disk and recorded as assets in the database.

### Step 2 — Process & Chunk
`POST /api/v1/process/{project_id}` — Extract text, split into overlapping chunks using LangChain, and store them in the database. Supports full-reset mode to re-process files (also clears the associated vector collection).

### Step 3 — Index into Vector DB
`POST /api/v1/nlp/index/push/{project_id}` — Embed all chunks using the configured embedding provider and upsert into Qdrant or pgvector in batches. Progress is tracked with a `tqdm` progress bar in the server logs.

### Step 4 — Chat with RAG
`POST /api/v1/conversation/chat/{project_id}` — Customer sends a query. The system:
1. Checks for existing conversation history
2. Reformalizes the query using the LLM if history exists
3. Retrieves top-k semantically similar chunks from the vector DB
4. Injects context into the LLM prompt and generates an answer
5. Appends the exchange to the conversation history in PostgreSQL

### Step 5 — Close Conversation
`POST /api/v1/conversation/chat/{project_id}/close` — Marks the conversation as `closed`.

### Step 6 — Generate & Email Ticket
`POST /api/v1/conversation/chat/{project_id}/summarized_ticket_email` — Summarizes the full conversation using the LLM (if not already done) and sends a structured support ticket email to the customer service team via SMTP.

---

## Roadmap / Upcoming Features

- [x] Prometheus metrics middleware
- [x] Grafana observability stack
- [x] Next.js frontend (Chat, Dashboard, RAG pages)
- [x] Nginx reverse proxy
- [x] Qdrant as a containerized Docker service
- [ ] Fine-tuned FLAN-T5 (LoRA/PEFT on DialogSum) for local conversation summarization
- [ ] Sentiment analysis and priority classification (high / medium / low)
- [ ] Customer-facing confirmation email after ticket creation
- [ ] Customer satisfaction survey after ticket resolution
- [ ] AWS EC2 deployment configuration
- [ ] Rate limiting and API authentication

---

## License

[MIT](LICENSE)
