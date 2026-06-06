# Implementation Plan: Chat Engine

**Branch**: `004-chat-engine` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-chat-engine/spec.md`

## Summary

Implement the Chat Engine for the multi-tenant AI assistant platform. This covers a synchronous REST chat endpoint, a real-time WebSocket streaming endpoint, RAG retrieval + LLM integration with automatic model fallback, conversation and message persistence with RLS, token usage tracking with quota enforcement, and a deterministic human handoff protocol backed by Redis Pub/Sub. A corresponding Next.js chat UI will consume both transport layers.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript / Node.js 20 (frontend)

**Primary Dependencies**:
- Backend: FastAPI 0.110, SQLAlchemy 2.0 (async), asyncpg, Alembic, Celery 5, Redis 5, ChromaDB 0.4, openai SDK (or compatible LLM client), PyJWT 2.8
- Frontend: Next.js 14 (App Router), NextAuth.js, shadcn/ui, native WebSocket API

**Storage**: PostgreSQL 16 (conversations, messages, quota_logs via RLS) + ChromaDB (vector store, per-tenant collection) + Redis 7 (rate-limiting, pub/sub, token bucket)

**Testing**: pytest + pytest-asyncio (backend); Jest + React Testing Library (frontend)

**Target Platform**: Linux server via Docker Compose

**Project Type**: Multi-tenant SaaS web service (backend REST + WebSocket API + Next.js frontend)

**Performance Goals**:
- REST response p95 < 3.0 s under normal load
- WebSocket first token < 500 ms for 90% of requests
- Handoff event propagation via Pub/Sub < 100 ms
- Quota check overhead < 10 ms per request

**Constraints**:
- Zero cross-tenant data leakage (RLS + per-tenant ChromaDB collection)
- All database transactions MUST set `SET LOCAL app.current_tenant_id` before queries
- Token quota enforced before calling LLM; hard stop on mid-stream quota breach
- Fixed context window of last 10 messages per conversation

**Scale/Scope**: Multi-tenant SaaS; initial target ~50 concurrent tenants, hundreds of concurrent chats

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Multi-Tenancy RLS Isolation | ✅ PASS | `conversations`, `messages`, `quota_logs` all carry `tenant_id`; RLS will be enforced via `TenantMixin` + Alembic migrations |
| II | Per-Tenant Vector Store Isolation | ✅ PASS | All ChromaDB queries scoped to `tenant_{uuid}` collection; `tenant_id` embedded in document metadata for cross-verification |
| III | Subdomain Resolution & JWT Validation | ✅ PASS | REST + WebSocket endpoints validate JWT on every request; `X-Tenant-ID` header matched against JWT `tenant_id` claim |
| IV | Resource Quota Enforcement & Rate Limiting | ✅ PASS | Redis token bucket enforces rate limits; pre-flight quota check blocks requests; mid-stream quota breach terminates the stream |
| V | Decoupled Async Processing | ✅ PASS | LLM calls are non-blocking async; Pub/Sub via Redis is async; Celery used only for ingestion (not blocking chat) |

**Gate result: PASS — all 5 principles satisfied.**

## Project Structure

### Documentation (this feature)

```text
specs/004-chat-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── rest-chat.md     # POST /v1/chat endpoint contract
│   └── ws-chat.md       # WebSocket /v1/ws/chat endpoint contract
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── chat.py          # NEW: REST chat endpoint
│   │       │   └── ws_chat.py       # NEW: WebSocket streaming endpoint
│   │       └── router.py            # MODIFY: register new routers
│   ├── models/
│   │   ├── conversation.py          # MODIFY: add handoff status enum, title field
│   │   └── message.py               # EXISTING: already has tokens_used, sources
│   ├── schemas/
│   │   └── chat.py                  # NEW: Pydantic schemas for chat requests/responses
│   ├── services/
│   │   ├── chat_service.py          # NEW: orchestrates RAG + LLM + persistence
│   │   ├── llm_service.py           # NEW: LLM client with primary/fallback model logic
│   │   ├── quota_service.py         # NEW: token quota enforcement via Redis
│   │   ├── handoff_service.py       # NEW: keyword/regex matching + Redis Pub/Sub
│   │   └── rag/
│   │       └── chroma_client.py     # EXISTING: extend with retrieval method
│   └── core/
│       └── config.py                # MODIFY: add LLM keys, model names, handoff keywords
│
├── alembic/
│   └── versions/
│       └── xxxx_add_chat_engine_schema.py  # NEW migration

frontend/
├── app/
│   └── dashboard/
│       └── assistants/
│           └── [id]/
│               └── chat/
│                   └── page.tsx     # NEW: Chat UI page
├── components/
│   └── chat/
│       ├── ChatWindow.tsx           # NEW: Message list + input box
│       ├── MessageBubble.tsx        # NEW: Individual message display
│       ├── StreamingDot.tsx         # NEW: Animated typing indicator
│       └── HandoffBanner.tsx        # NEW: Handoff state notification
└── lib/
    └── chat-api.ts                  # NEW: REST + WebSocket client helpers
```

**Structure Decision**: Web application (Option 2). Existing `backend/app/` and `frontend/` structure extended with new modules; no new top-level projects added.

## Complexity Tracking

> No constitution violations detected. This section is intentionally left minimal.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Dual transport (REST + WS) | FR-001 requires non-streaming REST; FR-002 requires WebSocket streaming | A single transport cannot satisfy both synchronous and streaming use-cases |
