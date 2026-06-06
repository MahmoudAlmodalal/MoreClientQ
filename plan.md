# Multi-Tenant AI Assistant Platform — Full Implementation Plan
> Monolithic RAG SaaS | FastAPI + Next.js | Production-Ready

---

## Table of Contents

1. [System Architecture & Tech Stack](#1-system-architecture--tech-stack)
2. [Project Structure](#2-project-structure)
3. [Database Design](#3-database-design)
4. [Authentication & Multi-Tenancy](#4-authentication--multi-tenancy)
5. [Backend API — FastAPI](#5-backend-api--fastapi)
6. [RAG Pipeline](#6-rag-pipeline)
7. [Task Queue — Celery + Redis](#7-task-queue--celery--redis)
8. [Real-Time — WebSockets](#8-real-time--websockets)
9. [Landing Page](#9-landing-page)
10. [Frontend — Next.js App](#10-frontend--nextjs-app)
11. [Security & Compliance](#11-security--compliance)
12. [Monitoring & Observability](#12-monitoring--observability)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment & CI/CD](#14-deployment--cicd)
15. [Implementation Phases & Timeline](#15-implementation-phases--timeline)

---

## 1. System Architecture & Tech Stack

### 1.1 Core Technologies

| Component | Technology | Description |
|---|---|---|
| Frontend | Next.js 14+ (App Router) | React framework with Server Components & Middleware |
| Backend | FastAPI (Python 3.11+) | High-performance ASGI framework |
| Primary Database | PostgreSQL 16 | Relational DB with RLS for tenant isolation |
| Vector Database | ChromaDB | Per-tenant isolated collections for RAG |
| Cache & Broker | Redis 7 | Session cache, Celery broker, rate limiting |
| Task Queue | Celery 5 | Async file ingestion & RAG pipeline |
| Real-Time | FastAPI WebSockets | Live chat & human handoff |
| Auth | NextAuth.js (frontend) + JWT (backend) | RBAC with subdomain awareness |
| Object Storage | MinIO (self-hosted) / S3 | Document & media file storage |
| Reverse Proxy | Nginx | SSL termination, subdomain routing |
| Containerization | Docker + Docker Compose | Dev & production parity |

### 1.2 Multi-Tenancy Strategy

**Database Isolation:** Shared PostgreSQL database with Row-Level Security (RLS) policies enforced at the database level. Every tenant-specific table carries a mandatory `tenant_id` (UUID) column. Application-level middleware validates the tenant on every request before any query runs.

**Vector Isolation:** ChromaDB uses a collection named `tenant_{uuid}` per tenant. All upserted documents embed `tenant_id` in metadata for cross-validation at query time. Collections are deleted on tenant offboarding.

**Frontend Routing:** Subdomain-based routing (`client1.platform.com`) resolved in Next.js Middleware. The subdomain slug is extracted, validated against the tenant registry, and injected as a header (`X-Tenant-ID`) forwarded to the FastAPI backend.

**Compute Isolation:** Shared compute with per-tenant rate limiting enforced via Redis token buckets on both the API gateway (Nginx) and the FastAPI middleware layer.

### 1.3 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)              │
│          SSL termination + subdomain routing          │
└──────────────┬──────────────────────┬────────────────┘
               │                      │
       ┌───────▼──────┐      ┌────────▼────────┐
       │  Next.js App │      │   FastAPI Backend│
       │  (Port 3000) │◄────►│   (Port 8000)   │
       │  App Router  │      │   ASGI/Uvicorn  │
       └──────────────┘      └────────┬────────┘
                                      │
              ┌───────────────────────┼───────────────┐
              │                       │               │
       ┌──────▼──────┐       ┌────────▼──────┐ ┌─────▼──────┐
       │  PostgreSQL │       │   ChromaDB    │ │   Redis    │
       │  (RLS + RDB)│       │ (Vector Store)│ │(Cache/MQ)  │
       └─────────────┘       └───────────────┘ └─────┬──────┘
                                                      │
                                             ┌────────▼───────┐
                                             │  Celery Workers│
                                             │ (RAG Ingestion)│
                                             └────────────────┘
```

---

## 2. Project Structure

```
ai-assistant-platform/
├── backend/                          # FastAPI monolith
│   ├── alembic/                      # DB migrations
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Shared dependencies (DB, auth, tenant)
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── auth.py
│   │   │       ├── tenants.py
│   │   │       ├── assistants.py
│   │   │       ├── documents.py
│   │   │       ├── chat.py
│   │   │       ├── analytics.py
│   │   │       └── webhooks.py
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic Settings
│   │   │   ├── security.py           # JWT, password hashing
│   │   │   ├── middleware.py         # Tenant resolution middleware
│   │   │   └── ratelimit.py          # Redis token bucket
│   │   ├── db/
│   │   │   ├── base.py               # SQLAlchemy Base
│   │   │   ├── session.py            # Async session factory
│   │   │   └── rls.py                # RLS policy helpers
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── assistant.py
│   │   │   ├── document.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── rag/
│   │   │   │   ├── embedder.py       # Embedding wrapper (OpenAI / local)
│   │   │   │   ├── retriever.py      # ChromaDB query logic
│   │   │   │   └── pipeline.py       # Full RAG chain
│   │   │   ├── llm.py                # LLM provider abstraction
│   │   │   ├── storage.py            # MinIO/S3 client
│   │   │   └── websocket_manager.py  # WS connection registry
│   │   ├── tasks/                    # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── ingest.py             # Document ingestion task
│   │   │   └── cleanup.py            # Expired session cleanup
│   │   └── main.py                   # FastAPI app factory
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/                         # Next.js 14 App Router
│   ├── app/
│   │   ├── (marketing)/              # Landing page route group
│   │   │   ├── page.tsx              # Landing page (/)
│   │   │   ├── pricing/page.tsx
│   │   │   └── layout.tsx            # Marketing layout
│   │   ├── (auth)/                   # Auth route group
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/              # Protected tenant dashboard
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── assistants/
│   │   │   ├── documents/
│   │   │   ├── conversations/
│   │   │   ├── analytics/
│   │   │   └── layout.tsx
│   │   ├── api/                      # Next.js API routes (auth callbacks)
│   │   └── layout.tsx
│   ├── components/
│   │   ├── landing/                  # Landing page sections
│   │   │   ├── Hero.tsx
│   │   │   ├── Features.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   ├── Pricing.tsx
│   │   │   ├── Testimonials.tsx
│   │   │   └── Footer.tsx
│   │   ├── chat/
│   │   │   ├── ChatWidget.tsx        # Embeddable widget
│   │   │   └── ChatWindow.tsx
│   │   └── ui/                       # shadcn/ui components
│   ├── middleware.ts                  # Subdomain resolution
│   ├── lib/
│   │   ├── api.ts                    # Typed API client
│   │   └── auth.ts                   # NextAuth config
│   └── public/
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## 3. Database Design

### 3.1 Entity Relationship Overview

```
tenants ──< users ──< conversations ──< messages
   │                                       │
   ├──< assistants ──< documents           │
   │         │                             │
   │         └──< knowledge_base           │
   └──< subscription_plans                 └──< message_sources
```

### 3.2 Core Tables (PostgreSQL)

```sql
-- Tenants (SaaS customers / companies)
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            VARCHAR(63) UNIQUE NOT NULL,   -- subdomain key
    name            VARCHAR(255) NOT NULL,
    plan            VARCHAR(50) NOT NULL DEFAULT 'starter',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    settings        JSONB NOT NULL DEFAULT '{}',   -- AI config, branding
    monthly_quota   INT NOT NULL DEFAULT 1000,     -- message quota
    used_quota      INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    full_name       VARCHAR(255),
    role            VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner|admin|member
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- AI Assistants (configurable bots per tenant)
CREATE TABLE assistants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    system_prompt   TEXT NOT NULL DEFAULT '',
    model           VARCHAR(100) NOT NULL DEFAULT 'gpt-4o-mini',
    temperature     FLOAT NOT NULL DEFAULT 0.7,
    max_tokens      INT NOT NULL DEFAULT 1024,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    widget_config   JSONB NOT NULL DEFAULT '{}',  -- colors, position, greeting
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Documents (uploaded knowledge files)
CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    assistant_id    UUID REFERENCES assistants(id) ON DELETE SET NULL,
    filename        VARCHAR(512) NOT NULL,
    storage_key     VARCHAR(1024) NOT NULL,        -- MinIO/S3 object key
    file_type       VARCHAR(50) NOT NULL,           -- pdf|docx|txt|url
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|processing|ready|failed
    chunk_count     INT,
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Conversations
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    assistant_id    UUID NOT NULL REFERENCES assistants(id) ON DELETE CASCADE,
    session_token   VARCHAR(255) UNIQUE NOT NULL,  -- visitor session
    visitor_name    VARCHAR(255),
    visitor_email   VARCHAR(255),
    status          VARCHAR(50) NOT NULL DEFAULT 'active',  -- active|resolved|handed_off
    channel         VARCHAR(50) NOT NULL DEFAULT 'web',     -- web|api
    metadata        JSONB NOT NULL DEFAULT '{}',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- Messages
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,    -- user|assistant|system
    content         TEXT NOT NULL,
    tokens_used     INT DEFAULT 0,
    latency_ms      INT,
    sources         JSONB DEFAULT '[]',      -- [{doc_id, chunk, score}]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Quota usage log (hourly rollup)
CREATE TABLE quota_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period          TIMESTAMPTZ NOT NULL,   -- truncated to hour
    message_count   INT NOT NULL DEFAULT 0,
    token_count     INT NOT NULL DEFAULT 0
);
```

### 3.3 Row-Level Security (RLS)

```sql
-- Enable RLS on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: app role can only see rows matching current_tenant_id setting
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation ON messages
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
-- (Repeat for all tables)

-- Before every DB transaction, set the config:
-- SET LOCAL app.current_tenant_id = '<uuid>';
```

### 3.4 Indexes

```sql
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_assistants_tenant ON assistants(tenant_id);
CREATE INDEX idx_documents_tenant_status ON documents(tenant_id, status);
CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX idx_conversations_session ON conversations(session_token);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_tenant_created ON messages(tenant_id, created_at DESC);
```

---

## 4. Authentication & Multi-Tenancy

### 4.1 Authentication Flow

```
Visitor → Next.js → Middleware (resolve subdomain → tenant_id)
                   ↓
Dashboard User → NextAuth.js → JWT (contains tenant_id + role)
                              ↓
                      FastAPI: verify JWT, inject tenant_id into DB session
```

### 4.2 Tenant Resolution Middleware (Next.js)

```typescript
// frontend/middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(req: NextRequest) {
  const hostname = req.headers.get('host') || '';
  const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN!;

  // Extract subdomain slug
  const slug = hostname.replace(`.${rootDomain}`, '');

  if (slug === rootDomain || slug === 'www') {
    return NextResponse.next(); // Marketing pages — no tenant
  }

  // Validate slug against tenant registry (fast Redis lookup via API)
  const tenantRes = await fetch(`${process.env.BACKEND_URL}/api/v1/tenants/resolve/${slug}`, {
    headers: { 'X-Internal-Secret': process.env.INTERNAL_SECRET! }
  });

  if (!tenantRes.ok) {
    return NextResponse.redirect(new URL('/404', req.url));
  }

  const { tenant_id } = await tenantRes.json();

  const res = NextResponse.next();
  res.headers.set('X-Tenant-ID', tenant_id);
  res.headers.set('X-Tenant-Slug', slug);
  return res;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### 4.3 Tenant Middleware (FastAPI)

```python
# backend/app/core/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

class TenantMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {"/health", "/api/v1/tenants/resolve", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Missing tenant context")

        # Validate from Redis cache (TTL: 5 min)
        cache: redis.Redis = request.app.state.redis
        tenant_data = await cache.get(f"tenant:{tenant_id}")
        if not tenant_data:
            # Fall back to DB and repopulate cache
            tenant_data = await self._load_from_db(tenant_id, request)

        request.state.tenant_id = tenant_id
        request.state.tenant = tenant_data
        return await call_next(request)
```

### 4.4 JWT Structure

```json
{
  "sub": "user_uuid",
  "tenant_id": "tenant_uuid",
  "tenant_slug": "clientname",
  "role": "admin",
  "exp": 1735000000
}
```

### 4.5 RBAC Roles

| Role | Permissions |
|---|---|
| `owner` | Full access. Billing, delete tenant, manage all users |
| `admin` | Manage assistants, documents, view analytics |
| `member` | View conversations, respond in human handoff |
| `viewer` | Read-only analytics dashboard |

---

## 5. Backend API — FastAPI

### 5.1 App Factory

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import TenantMiddleware, RateLimitMiddleware
from app.api.v1.router import api_router
from app.db.session import engine
from app.tasks.celery_app import celery_app
import redis.asyncio as redis

def create_app() -> FastAPI:
    app = FastAPI(title="AI Assistant Platform", version="1.0.0")

    app.add_middleware(TenantMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup():
        app.state.redis = redis.from_url("redis://localhost:6379")

    return app

app = create_app()
```

### 5.2 API Endpoints

#### Tenants
```
POST   /api/v1/auth/register          — Register new tenant + owner account
POST   /api/v1/auth/login             — Login, return JWT
POST   /api/v1/auth/refresh           — Refresh token
GET    /api/v1/tenants/resolve/{slug} — Internal: resolve slug → tenant_id
GET    /api/v1/tenants/me             — Get current tenant info
PATCH  /api/v1/tenants/me             — Update tenant settings/branding
```

#### Users
```
GET    /api/v1/users                  — List users in tenant
POST   /api/v1/users/invite           — Invite user by email
PATCH  /api/v1/users/{id}             — Update role
DELETE /api/v1/users/{id}             — Remove user
```

#### Assistants
```
GET    /api/v1/assistants             — List assistants
POST   /api/v1/assistants             — Create assistant
GET    /api/v1/assistants/{id}        — Get assistant config
PATCH  /api/v1/assistants/{id}        — Update config/prompt/model
DELETE /api/v1/assistants/{id}        — Delete (cascades knowledge base)
GET    /api/v1/assistants/{id}/embed  — Get embeddable widget code
```

#### Documents (Knowledge Base)
```
POST   /api/v1/documents/upload       — Upload file (triggers ingestion task)
POST   /api/v1/documents/url          — Ingest from URL
GET    /api/v1/documents              — List documents with status
DELETE /api/v1/documents/{id}         — Delete + remove from vector store
GET    /api/v1/documents/{id}/status  — Polling ingestion status
```

#### Chat
```
POST   /api/v1/chat/{assistant_id}    — REST chat endpoint (stateless)
WS     /api/v1/ws/chat/{assistant_id} — WebSocket streaming chat
POST   /api/v1/chat/handoff           — Escalate to human agent
```

#### Analytics
```
GET    /api/v1/analytics/overview     — Message count, sessions, quota usage
GET    /api/v1/analytics/conversations — Paginated conversation list
GET    /api/v1/analytics/messages      — Message-level detail
GET    /api/v1/analytics/performance   — Latency, token cost breakdown
```

#### Webhooks
```
POST   /api/v1/webhooks               — Register outbound webhook
GET    /api/v1/webhooks               — List webhooks
DELETE /api/v1/webhooks/{id}          — Delete webhook
POST   /api/v1/webhooks/{id}/test     — Fire test payload
```

### 5.3 Shared Dependency Injection

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, Request
from app.db.session import AsyncSession, get_session
from app.core.security import verify_jwt

async def get_db(request: Request) -> AsyncSession:
    async with AsyncSession() as session:
        # Set RLS context variable for this transaction
        await session.execute(
            f"SET LOCAL app.current_tenant_id = '{request.state.tenant_id}'"
        )
        yield session

async def get_current_user(request: Request, db = Depends(get_db)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = verify_jwt(token)
    if payload.get("tenant_id") != request.state.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return payload

def require_role(*roles: str):
    async def _check(user = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _check
```

---

## 6. RAG Pipeline

### 6.1 Architecture

```
Upload ──► S3/MinIO ──► Celery Task
                             │
                        Text Extraction
                        (PyMuPDF, docx2txt, html2text)
                             │
                        Chunking (LangChain RecursiveCharacterTextSplitter)
                        chunk_size=512, overlap=64
                             │
                        Embedding (OpenAI text-embedding-3-small or local)
                             │
                        ChromaDB Upsert (collection: tenant_{uuid})
                             │
                        Mark document status = "ready"
```

### 6.2 Ingestion Task

```python
# backend/app/tasks/ingest.py
from celery import shared_task
from app.services.rag.embedder import get_embedder
from app.services.storage import download_file
import chromadb

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def ingest_document(self, document_id: str, tenant_id: str, storage_key: str, file_type: str):
    try:
        # 1. Download from object store
        raw_bytes = download_file(storage_key)

        # 2. Extract text
        text = extract_text(raw_bytes, file_type)  # PyMuPDF, docx2txt, etc.

        # 3. Chunk
        chunks = chunk_text(text, chunk_size=512, overlap=64)

        # 4. Embed
        embedder = get_embedder()
        embeddings = embedder.embed_documents([c.text for c in chunks])

        # 5. Upsert to ChromaDB
        client = chromadb.HttpClient(host="chromadb", port=8000)
        collection = client.get_or_create_collection(f"tenant_{tenant_id}")
        collection.upsert(
            ids=[f"{document_id}_{i}" for i in range(len(chunks))],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[{
                "tenant_id": tenant_id,
                "document_id": document_id,
                "chunk_index": i,
                "source": storage_key
            } for i, c in enumerate(chunks)]
        )

        # 6. Update DB status
        update_document_status(document_id, "ready", chunk_count=len(chunks))

    except Exception as exc:
        update_document_status(document_id, "failed", error=str(exc))
        raise self.retry(exc=exc)
```

### 6.3 RAG Query Pipeline

```python
# backend/app/services/rag/pipeline.py
async def run_rag(
    query: str,
    tenant_id: str,
    assistant: Assistant,
    conversation_history: list[dict]
) -> AsyncIterator[str]:

    # 1. Retrieve relevant chunks from ChromaDB
    collection = chroma_client.get_collection(f"tenant_{tenant_id}")
    results = collection.query(
        query_texts=[query],
        n_results=5,
        where={"tenant_id": tenant_id}  # Cross-validate tenant
    )

    # 2. Build context block
    context = "\n\n".join(results["documents"][0]) if results["documents"] else ""

    # 3. Build prompt
    messages = [
        {"role": "system", "content": f"{assistant.system_prompt}\n\nContext:\n{context}"},
        *conversation_history[-10:],  # Last 10 turns
        {"role": "user", "content": query}
    ]

    # 4. Stream LLM response
    async for chunk in llm_client.stream(
        model=assistant.model,
        messages=messages,
        temperature=assistant.temperature,
        max_tokens=assistant.max_tokens
    ):
        yield chunk

    # 5. Return sources metadata for citation
    return results["metadatas"][0]
```

---

## 7. Task Queue — Celery + Redis

### 7.1 Configuration

```python
# backend/app/tasks/celery_app.py
from celery import Celery

celery_app = Celery(
    "ai_platform",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "app.tasks.ingest.*": {"queue": "ingestion"},
        "app.tasks.cleanup.*": {"queue": "maintenance"},
    },
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.cleanup.purge_expired_sessions",
            "schedule": 3600.0,  # Every hour
        },
        "rollup-quota-logs": {
            "task": "app.tasks.cleanup.rollup_quota_logs",
            "schedule": 3600.0,
        },
    }
)
```

### 7.2 Task Queues

| Queue | Workers | Tasks |
|---|---|---|
| `ingestion` | 2–4 | Document text extraction + embedding |
| `maintenance` | 1 | Session cleanup, quota rollup |
| `notifications` | 1 | Email invites, handoff alerts |

---

## 8. Real-Time — WebSockets

### 8.1 Chat WebSocket Handler

```python
# backend/app/api/v1/chat.py
from fastapi import WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from app.services.rag.pipeline import run_rag

@router.websocket("/ws/chat/{assistant_id}")
async def websocket_chat(
    websocket: WebSocket,
    assistant_id: str,
    session_token: str,
    request: Request
):
    tenant_id = request.state.tenant_id
    await manager.connect(websocket, session_token)

    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("message", "")

            # Load conversation history from cache
            history = await get_conversation_history(session_token)

            # Stream RAG response token by token
            full_response = ""
            async for token in run_rag(query, tenant_id, assistant, history):
                await websocket.send_json({"type": "token", "content": token})
                full_response += token

            # Signal end of stream
            await websocket.send_json({"type": "done", "content": full_response})

            # Persist to DB asynchronously
            await persist_message(session_token, query, full_response, tenant_id)

    except WebSocketDisconnect:
        manager.disconnect(session_token)
```

### 8.2 Human Handoff Protocol

```
Visitor sends: { "type": "handoff_request" }
     ↓
Server broadcasts to all online agents for that tenant via Redis Pub/Sub
     ↓
Available agent accepts: { "type": "handoff_accept", "agent_id": "..." }
     ↓
Conversation status → "handed_off"
AI stops auto-responding
Agent and visitor share the same WebSocket room
     ↓
Agent resolves: { "type": "resolve" }
Conversation status → "resolved", AI can resume
```

---

## 9. Landing Page

### 9.1 Purpose & Audience

The landing page targets SMB owners and startup founders who want to add an AI customer support assistant to their product — without infrastructure overhead. It converts cold traffic into trial signups.

**Key conversion goals:**
- Hero: Capture attention + single CTA ("Start Free Trial")
- Features: Justify the value before asking for money
- How It Works: Reduce friction by showing simplicity (3 steps)
- Social Proof: Build trust via testimonials + logos
- Pricing: Transparent tiers to self-qualify leads
- Final CTA: Urgency close at bottom

### 9.2 Page Sections

#### Section 1: Navigation
```
Logo | Features | How It Works | Pricing | Docs | [Login] [Start Free →]
```

#### Section 2: Hero
- **Headline:** "Your AI support agent, live in 10 minutes."
- **Sub-headline:** "Embed a GPT-powered assistant trained on your docs into any product. No ML expertise needed."
- **CTA buttons:** "Start Free Trial" (primary) | "See a Demo" (secondary, opens modal)
- **Visual:** Animated chat widget preview with simulated live conversation
- **Trust strip:** "No credit card required · Free 14-day trial · Cancel anytime"

#### Section 3: Social Proof Strip
Logos of recognizable client companies or technology partners (OpenAI, Stripe, etc.).

#### Section 4: Features (3-column grid)
| Feature | Icon | Description |
|---|---|---|
| RAG Knowledge Base | 📄 | Upload PDFs, docs, or URLs. The AI answers from your content only. |
| Multi-Tenant Isolation | 🔒 | Each client's data is fully isolated. RLS + dedicated vector collections. |
| Real-Time Streaming | ⚡ | WebSocket streaming for instant token-by-token responses. |
| Human Handoff | 👤 | Escalate any conversation to a live agent in one click. |
| Analytics Dashboard | 📊 | Track usage, latency, and cost per conversation. |
| Embeddable Widget | 🧩 | One `<script>` tag. Customizable colors, language, and greeting. |

#### Section 5: How It Works (3 steps)
1. **Create your assistant** — Name it, write a system prompt, pick a model.
2. **Upload your knowledge** — Drag in PDFs, docs, or paste URLs.
3. **Embed on your site** — Copy one script tag. Done.

#### Section 6: Live Demo
Interactive embedded demo widget (your own platform dogfooding itself). Visitor can ask questions and see real streaming AI responses.

#### Section 7: Pricing

| Plan | Price | Quota | Features |
|---|---|---|---|
| Starter | Free | 500 msgs/mo | 1 assistant, 5 documents, community support |
| Pro | $49/mo | 5,000 msgs/mo | 5 assistants, 100 docs, analytics, webhooks |
| Business | $199/mo | 25,000 msgs/mo | Unlimited assistants, priority support, SLA |
| Enterprise | Custom | Unlimited | Dedicated infra, SSO, custom models, on-prem |

#### Section 8: Testimonials
3–4 quote cards from fictional / early-access customers. Include name, company, and avatar.

#### Section 9: Footer CTA
"Ready to deploy your AI assistant?" + email capture + "Start Free Trial" button.

#### Section 10: Footer
Links: Product, Docs, Blog, Changelog, Status, Privacy, Terms | Social links.

### 9.3 Technical Implementation (Next.js)

```tsx
// frontend/app/(marketing)/page.tsx
import { Hero } from '@/components/landing/Hero';
import { Features } from '@/components/landing/Features';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { Pricing } from '@/components/landing/Pricing';
import { Testimonials } from '@/components/landing/Testimonials';
import { CtaBanner } from '@/components/landing/CtaBanner';

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <LogoStrip />
      <Features />
      <HowItWorks />
      <LiveDemo />
      <Pricing />
      <Testimonials />
      <CtaBanner />
    </main>
  );
}
```

### 9.4 Design System (Landing)
- **Font pair:** `Geist` (headings, bold weight) + `Geist Mono` (code/tech snippets)
- **Color palette:**
  - Background: `#0a0a0a` (near-black)
  - Surface: `#111111`
  - Primary: `#7C3AED` (violet-600)
  - Accent: `#22D3EE` (cyan-400)
  - Text primary: `#F9FAFB`
  - Text muted: `#6B7280`
- **Theme:** Dark, technical, startup-grade — confident without being flashy
- **Animations:** Fade-up on scroll for sections, typewriter effect on hero headline, pulsing dot on live demo widget

### 9.5 SEO & Performance
- Next.js `generateMetadata()` for all pages
- `og:image` generated via `@vercel/og` (dynamic OG cards)
- Page speed target: LCP < 1.5s, CLS < 0.05
- All images as Next.js `<Image>` with `priority` on hero
- Landing page is fully static (no client-side data fetching)

---

## 10. Frontend — Next.js App

### 10.1 Dashboard Layout

```
Sidebar (collapsible)          Main content
├── Overview (Dashboard)       ┌──────────────────────────────┐
├── Assistants                 │  Page header + breadcrumb    │
├── Knowledge Base             ├──────────────────────────────┤
├── Conversations              │                              │
├── Analytics                  │  Page-specific content       │
├── Settings                   │                              │
└── Billing                    └──────────────────────────────┘
```

### 10.2 Key Dashboard Pages

**Dashboard Overview** — Quota meter, message count, active conversations, quick-create button.

**Assistants List** — Cards with status badge, message count, last active. Create/Edit/Delete actions.

**Assistant Editor** — System prompt editor (CodeMirror), model picker, temperature slider, widget preview panel (live-updated).

**Knowledge Base** — Drag-and-drop upload zone, document list with status badges (pending / processing / ready / failed), delete action triggers ChromaDB cleanup task.

**Conversations** — Table with visitor info, status, message count. Click-through to full conversation replay.

**Analytics** — Line chart (messages/day), bar chart (token cost/model), quota usage ring chart, latency P50/P95 table.

**Widget Configurator** — Visual editor for colors, position, greeting message. Live preview iframe. Copy embed code button.

### 10.3 Embeddable Chat Widget

The widget is a standalone `<script>` + `<iframe>` bundle served from the Next.js app at `/widget/{assistant_id}`. It connects via WebSocket to the FastAPI backend and streams responses in real time.

```html
<!-- What the tenant pastes on their website -->
<script
  src="https://platform.com/widget.js"
  data-assistant="asst_xxxxx"
  data-theme="dark"
  data-position="bottom-right"
></script>
```

---

## 11. Security & Compliance

### 11.1 Security Checklist

- **HTTPS everywhere** — Nginx enforces HTTPS with HSTS headers. All cookies `Secure; HttpOnly; SameSite=Strict`.
- **JWT expiry** — Access tokens: 15 min. Refresh tokens: 7 days stored in `HttpOnly` cookie.
- **API rate limiting** — Redis token bucket: 100 req/min per tenant by default. Burst allowed.
- **RLS enforcement** — Every DB session sets `app.current_tenant_id`. Queries without it fail at DB level.
- **Input validation** — All inputs go through Pydantic schemas. HTML in chat messages is stripped.
- **File upload safety** — MIME type validation, max 50 MB, virus scan stub (ClamAV integration point).
- **Secret management** — All secrets via environment variables. Never hardcoded. `.env.example` committed, `.env` gitignored.
- **Webhook signatures** — Outbound webhooks signed with HMAC-SHA256 using tenant-specific secret.
- **Dependency scanning** — `pip-audit` + `npm audit` in CI.

### 11.2 Tenant Data Deletion (GDPR)

On tenant offboarding:
1. Delete all PostgreSQL rows (cascade via FK)
2. Drop ChromaDB collection `tenant_{uuid}`
3. Delete all MinIO objects under `tenant/{uuid}/`
4. Revoke all active JWTs via Redis blocklist

---

## 12. Monitoring & Observability

### 12.1 Stack

| Layer | Tool |
|---|---|
| Structured Logs | `structlog` (FastAPI) → stdout → Loki |
| Metrics | `prometheus_fastapi_instrumentator` → Prometheus → Grafana |
| Tracing | OpenTelemetry → Jaeger |
| Uptime | Healthcheck endpoint `/health` polled by Nginx upstream |
| Error Tracking | Sentry (both FastAPI and Next.js) |
| Alerts | Grafana alerting → Slack webhook |

### 12.2 Key Metrics to Track

- `api_request_duration_seconds` (p50, p95 per route)
- `rag_query_duration_seconds` (embedding + retrieval + LLM separately)
- `celery_task_runtime_seconds` (ingestion task duration by file size)
- `tenant_message_count_total` (quota enforcement check)
- `chromadb_collection_size` (per tenant)
- `websocket_active_connections`

### 12.3 Health Check Endpoint

```python
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute("SELECT 1")                          # DB
    await redis.ping()                                    # Redis
    chroma_client.heartbeat()                             # ChromaDB
    return {"status": "ok", "timestamp": datetime.utcnow()}
```

---

## 13. Testing Strategy

### 13.1 Backend (pytest + pytest-asyncio)

```
tests/
├── unit/
│   ├── test_rag_pipeline.py      — chunking, embedding mock
│   ├── test_tenant_middleware.py — slug resolution, rejection
│   └── test_security.py          — JWT sign/verify, RLS activation
├── integration/
│   ├── test_chat_api.py          — full REST chat flow with real DB
│   ├── test_document_ingest.py   — upload → Celery → ChromaDB
│   └── test_websocket_chat.py    — WS streaming test
└── e2e/
    └── test_tenant_isolation.py  — cross-tenant data leakage test
```

### 13.2 Frontend (Vitest + Playwright)

- **Unit:** Component tests with React Testing Library
- **E2E:** Playwright tests for full registration → assistant creation → chat flows
- **Key E2E tests:**
  - Subdomain resolves correct tenant
  - Document upload shows processing → ready state
  - Chat widget connects, streams, and saves messages
  - Human handoff escalation works

### 13.3 Security Tests

- Cross-tenant access attempt: Request with valid JWT but wrong subdomain → must return 403
- RLS leak test: Raw SQL `SELECT * FROM messages` without `SET LOCAL app.current_tenant_id` → must return 0 rows
- Rate limit enforcement: 101st request within 60s window → 429

---

## 14. Deployment & CI/CD

### 14.1 Docker Compose (Production)

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: [./nginx/nginx.conf:/etc/nginx/nginx.conf, ./nginx/ssl:/etc/nginx/ssl]
    depends_on: [frontend, backend]

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_ROOT_DOMAIN=platform.com
      - BACKEND_URL=http://backend:8000
    depends_on: [backend]

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/platform
      - REDIS_URL=redis://redis:6379
      - CHROMADB_HOST=chromadb
    depends_on: [postgres, redis, chromadb]

  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker -Q ingestion -c 4
    depends_on: [redis, postgres, chromadb, minio]

  celery_beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on: [redis]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: platform
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

  chromadb:
    image: chromadb/chroma:latest
    volumes: [chroma_data:/chroma/.chroma]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password
    volumes: [minio_data:/data]

volumes:
  postgres_data:
  redis_data:
  chroma_data:
  minio_data:
```

### 14.2 GitHub Actions CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test }
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
        working-directory: frontend
      - run: npm run test
        working-directory: frontend

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          pip install ruff mypy
          ruff check backend/
          mypy backend/app/

  build:
    needs: [backend-tests, frontend-tests, lint]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
      - run: docker compose push
```

---

## 15. Implementation Phases & Timeline

### Phase 0 — Foundation (Week 1)
- [x] Git monorepo initialized, branch strategy defined
- [x] Docker Compose dev environment working (all services up)
- [x] PostgreSQL schema + Alembic migrations initialized
- [x] FastAPI app skeleton with health check
- [x] Next.js 14 project with shadcn/ui installed
- [x] `.env` configuration aligned across services

### Phase 1 — Auth & Tenancy (Week 2)
- [ ] Tenant registration + slug uniqueness enforcement
- [ ] JWT auth (login, refresh, revoke)
- [ ] Next.js Middleware subdomain resolution
- [ ] FastAPI TenantMiddleware + RLS activation
- [ ] RBAC role checks on all protected routes
- [ ] Login + Register pages (frontend)

### Phase 2 — Assistant & Knowledge Base (Weeks 3–4)
- [ ] Assistant CRUD API + frontend pages
- [ ] MinIO/S3 file upload endpoint
- [ ] Celery ingestion pipeline (PDF, DOCX, URL)
- [ ] ChromaDB per-tenant collection creation
- [ ] Document list with status polling (Server-Sent Events or polling)
- [ ] Document delete + ChromaDB cleanup

### Phase 3 — Chat Engine (Week 5)
- [ ] REST chat endpoint (non-streaming)
- [ ] WebSocket streaming endpoint
- [ ] RAG retrieval + LLM integration
- [ ] Conversation + Message persistence
- [ ] Token usage tracking + quota enforcement
- [ ] Human handoff protocol + Redis Pub/Sub

### Phase 4 — Landing Page (Week 6)
- [ ] Marketing layout and navigation
- [ ] Hero section with animated chat preview
- [ ] Features, How It Works, Pricing sections
- [ ] Live demo widget (dogfooding)
- [ ] Testimonials, footer CTA
- [ ] SEO metadata, OG cards
- [ ] Mobile responsiveness audit

### Phase 5 — Dashboard & Widget (Week 7)
- [ ] Dashboard overview page with charts (Recharts)
- [ ] Conversation viewer
- [ ] Analytics page (message trends, latency, cost)
- [ ] Embeddable widget builder + code snippet copy
- [ ] Widget iframe bundle (`/widget/{assistant_id}`)

### Phase 6 — Production Hardening (Week 8)
- [ ] Rate limiting tuning + abuse detection
- [ ] Structured logging + Sentry integration
- [ ] Prometheus metrics + Grafana dashboards
- [ ] Security audit (OWASP checklist)
- [ ] Full E2E test suite with Playwright
- [ ] Cross-tenant isolation penetration test
- [ ] Performance profiling (p95 < 3s for RAG response)
- [ ] Nginx SSL configuration + HSTS

### Phase 7 — Launch (Week 9)
- [ ] Stripe billing integration (quota enforcement on plan limits)
- [ ] Email invites via Resend/SendGrid
- [ ] Docs site (Mintlify or Docusaurus)
- [ ] Status page (Better Uptime)
- [ ] Staging → production deploy on VPS / Cloud VM
- [ ] DNS wildcard record `*.platform.com → server IP`

---

## Appendix: Key Environment Variables

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/platform
REDIS_URL=redis://redis:6379
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=super-secret-key
JWT_ALGORITHM=HS256
INTERNAL_SECRET=internal-service-secret

# Frontend
NEXT_PUBLIC_ROOT_DOMAIN=platform.com
NEXT_PUBLIC_API_URL=https://platform.com/api
BACKEND_URL=http://backend:8000
NEXTAUTH_SECRET=nextauth-secret
NEXTAUTH_URL=https://platform.com
```

---

*Document version: 1.0 | Last updated: 2026*
