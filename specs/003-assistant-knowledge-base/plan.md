# Implementation Plan: Assistant & Knowledge Base

**Branch**: `003-assistant-knowledge-base` | **Date**: 2026-06-06 | **Spec**: [spec.md](file:///home/mahmoud/Desktop/MoreClientQ/specs/003-assistant-knowledge-base/spec.md)

**Input**: Feature specification from `/specs/003-assistant-knowledge-base/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

The **Assistant & Knowledge Base Management** feature enables tenant administrators (with `owner` or `admin` roles) to create and configure custom AI assistants, customize behavior (such as model, system prompt, temperature, and token limit), and populate a retrieval-augmented generation (RAG) knowledge base.
Admins can upload files (PDF, DOCX, TXT) or submit public URLs. Files are stored in MinIO and processed asynchronously via Celery. Document parsing, chunking, and embedding generation are run in background tasks and upserted into tenant-isolated collections (`tenant_{uuid}`) in ChromaDB. The system enforces tenant plan-based resource quotas and synchronous pre-flight URL validation.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript / Next.js 14 App Router (Frontend)

**Primary Dependencies**: FastAPI 0.110.0, Celery 5.3.6, Redis 7, PyMuPDF 1.23.26, docx2txt 0.8, httpx 0.27.0, minio>=7.2.0, tailwindcss, shadcn/ui

**Storage**: PostgreSQL 16 (metadata), ChromaDB 0.4.24 (vectors), MinIO (object storage)

**Testing**: pytest + pytest-asyncio (Backend), Jest + React Testing Library (Frontend)

**Target Platform**: Linux Server (Dockerized via docker-compose)

**Project Type**: Web service / SaaS dashboard

**Performance Goals**:
- Ingestion of documents up to 10MB complete within 3 minutes under normal load.
- Document deletion from DB and ChromaDB index reflected in search results within 30 seconds.
- Ingestion status updates reflected within 5 seconds of task progression.

**Constraints**:
- Strictly enforce Row-Level Security (RLS) at the PostgreSQL database level on all tenant-scoped tables.
- Use dedicated ChromaDB collections (`tenant_{uuid}`) per tenant to isolate vector data.
- Enforce tenant quota limits at the API layer (e.g. Starter: max 1 assistant, 5 documents).
- File size limit of 10 MB per upload.
- Block assistant deletion if there are active conversations, displaying the active count.
- Enforce unique filenames per assistant's knowledge base.
- Enforce Redis token-bucket API rate limits through existing Nginx and FastAPI middleware for all assistant and document endpoints.

**Scale/Scope**: Multitenant SaaS architecture supporting thousands of isolated tenants with Starter, Pro, Business, and Enterprise tiers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Multi-Tenancy RLS Isolation**: **PASSED**. The `Assistant` and `Document` tables extend `Base` and `TenantMixin` which ensures the `tenant_id` column is present. The RLS policies exist on both tables. All queries set `app.current_tenant_id` context.
- **Principle II: Per-Tenant Vector Store Isolation**: **PASSED**. chroma_client uses `tenant_{uuid}` as collection names. Upserts include the `tenant_id` in document metadata for multi-level filtering validation.
- **Principle III: Subdomain-Based Resolution & JWT**: **PASSED**. Frontend middleware resolves subdomain to tenant slug, extracts/validates tenant slug, passes `X-Tenant-ID` header. The backend validates JWT content.
- **Principle IV: Resource Quota Enforcement**: **PASSED**. API endpoints check tenant-specific limits from `app/core/quotas.py` prior to creation, and assistant/document routes remain behind the existing Redis token-bucket rate limits at the Nginx and FastAPI middleware layers.
- **Principle V: Decoupled Asynchronous Processing**: **PASSED**. Long-running extraction and indexing tasks are delegated to Celery workers on the `ingestion` queue.

## Project Structure

### Documentation (this feature)

```text
specs/003-assistant-knowledge-base/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 data design
├── quickstart.md        # Phase 1 setup and testing instructions
├── contracts/
│   └── api-endpoints.md # Interface contract for the endpoints
└── tasks.md             # Phase 2 tasks list (created during tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── assistants.py   # NEW: Assistant management endpoints
│   │           └── documents.py    # NEW: Knowledge base / document management endpoints
│   ├── core/
│   │   └── quotas.py               # NEW: Quota limits configuration
│   ├── models/
│   │   ├── assistant.py
│   │   └── document.py
│   ├── services/
│   │   ├── rag/
│   │   │   ├── chunker.py          # NEW: Custom character splitter
│   │   │   ├── embedder.py         # Embedding wrappers
│   │   │   └── pipeline.py         # RAG pipeline integrations
│   │   └── storage.py              # MinIO client wrapper
│   └── tasks/
│       ├── celery_app.py
│       └── ingest.py               # NEW: Background ingestion celery tasks
└── tests/
    └── api/
        ├── test_assistants.py      # NEW: API tests for assistants
        └── test_documents.py       # NEW: API tests for document upload & processing

frontend/
├── app/
│   └── (dashboard)/
│       └── dashboard/
│           ├── assistants/
│           │   ├── page.tsx        # NEW: Assistants list/creation dashboard
│           │   └── [id]/
│           │       └── knowledge-base/
│           │           └── page.tsx # NEW: Knowledge base management & file upload
│           └── layout.tsx
└── components/
    ├── assistants/
    │   ├── assistant-card.tsx      # NEW: Card UI for assistant config
    │   └── assistant-form.tsx      # NEW: Create/Edit Assistant modal
    └── knowledge-base/
        ├── document-list.tsx       # NEW: Polling document list with status badges
        ├── file-upload.tsx         # NEW: Drag-and-drop file upload with validation
        └── url-ingest-form.tsx     # NEW: Form for URL ingestion
```

**Structure Decision**: Option 2: Web application (monorepo backend/ and frontend/ directories).

## Complexity Tracking

*No violations detected.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | | |
