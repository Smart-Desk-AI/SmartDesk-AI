# SmartDesk-AI

> **AI-Powered Customer Support System** using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs)

SmartDesk AI is a production-ready backend platform that combines RAG, multi-provider LLMs, conversation management, ticket summarization, and email automation — all built on a clean, modular, provider-agnostic architecture.

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
- [Workflow](#workflow)
- [Roadmap](#roadmap--upcoming-features)

---

## Architecture Overview

```text
Customer Request
      |
      v
FastAPI Backend (Async)
      |
      +─────────────────────────────────────────────+
      |                                             |
      v                                             v
RAG Pipeline                              Conversation Manager
      |                                             |
      +──> Vector DB (Qdrant OR pgvector)           +──> PostgreSQL (SQLAlchemy)
      |         - Semantic search                   |         - Projects
      |         - Embedding indexing                |         - Conversations (JSONB)
      |                                             |         - DataChunks
      +──> Knowledge Base                           |         - Assets
            - FAQs                                  |
            - Company Policies                  MongoDB (Motor - async)
            - Refund Policies                       - Projects
            - Shipping Policies                     - Chunks
            - Product Documentation                 - Assets
            - Support Guides
      |
      v
LLM Provider (OpenAI OR Cohere)
      |
      +──> Generate Answer
      |
      v
Customer Response

==============================================

When Conversation Ends:
      |
      v
ConversationNLPController
      |
      +──> Summarize Conversation (LLM)
      |
      +──> Store Summary in PostgreSQL
      |
      +──> Email Ticket to Customer Service (SMTP)
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

### ✅ Docker Infrastructure
- Docker Compose setup running **MongoDB** and **pgvector** (PostgreSQL with the pgvector extension) as containerized services with persistent volumes and a shared backend network

---

## Technology Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI 0.104 |
| Runtime | Python (asyncio / async-first) |
| Server | Uvicorn |
| Configuration | Pydantic Settings + `.env` |

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
| Option A | Qdrant (via qdrant-client) |
| Option B | pgvector (PostgreSQL extension, via pgvector + SQLAlchemy) |

### Infrastructure
| Component | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
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

- Lightweight, in-process or server mode
- Supports cosine and dot-product distance
- Collections are created and deleted per project

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

---

## Project Structure

```
SmartDesk-AI/
├── docker/
│   ├── docker-compose.yml          # MongoDB + pgvector containers
│   ├── .env.example
│   └── mongodb/
├── src/
│   ├── main.py                     # FastAPI app, lifespan events, route registration
│   ├── requirements.txt
│   ├── .env.example
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
- Docker & Docker Compose
- PostgreSQL (or use the Docker service)
- An OpenAI or Cohere API key

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-org/SmartDesk-AI.git
cd SmartDesk-AI

pip install -r src/requirements.txt
```

### 2. Configure Environment

```bash
cp src/.env.example src/.env
# Edit src/.env with your credentials (see Environment Variables section)
```

### 3. Start Infrastructure (Docker)

```bash
cd docker
cp .env.example .env
# Set MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, POSTGRES_PASSWORD
docker compose up -d
```

### 4. Run Database Migrations

```bash
cd src/models/db_schemas/minirag
cp alembic.ini.example alembic.ini
# Update sqlalchemy.url in alembic.ini to your PostgreSQL connection string

alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

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

The `docker/docker-compose.yml` file provisions two services:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `mongodb` | `mongo:7-jammy` | `27007:27017` | Document store for projects, chunks, assets |
| `pgvector` | `pgvector/pgvector:0.8.0-pg17` | `5432:5432` | Relational DB + vector similarity search |

Both services share a `backend` bridge network and use named Docker volumes for data persistence.

```bash
cd docker
docker compose up -d         # Start services
docker compose down          # Stop services
docker compose down -v       # Stop and remove volumes
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

## Workflow

### Step 1 — Upload Knowledge Base
`POST /api/v1/upload/{project_id}` — Upload PDFs or documents. Files are streamed to disk and recorded as assets in the database.

### Step 2 — Process & Chunk
`POST /api/v1/process/{project_id}` — Extract text, split into overlapping chunks using LangChain, and store them in the database. Supports full-reset mode to re-process files.

### Step 3 — Index into Vector DB
`POST /api/v1/nlp/index/push/{project_id}` — Embed all chunks using the configured embedding provider and upsert into Qdrant or pgvector in batches.

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

- [ ] Fine-tuned FLAN-T5 (LoRA/PEFT on DialogSum) for local conversation summarization
- [ ] Sentiment analysis and priority classification (high / medium / low)
- [ ] Customer-facing confirmation email after ticket creation
- [ ] Customer satisfaction survey after ticket resolution
- [ ] Frontend (React / Next.js) interface
- [ ] AWS EC2 deployment configuration
- [ ] Rate limiting and API authentication

---

## License

[MIT](LICENSE)
