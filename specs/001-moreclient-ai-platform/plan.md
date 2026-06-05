# Implementation Plan: MoreClient AI Enterprise Platform

**Branch**: `001-moreclient-ai-platform` | **Date**: 2026-06-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-moreclient-ai-platform/spec.md`

## Summary

The MoreClient AI Enterprise Platform is a multi-tenant AI customer support platform. It supports tenant registration, workspace configuration, RAG-based AI chat with hybrid search, human agent escalation, Stripe subscription billing, and a bilingual Arabic (RTL) / English (LTR) admin dashboard. 

The technical approach implements logical database isolation using PostgreSQL Row Level Security (RLS) via FastAPI middleware/dependencies executing `SET LOCAL app.current_tenant_id = :tenant_id`, a single shared Qdrant collection with metadata/payload filtering on `tenant_id` (simplified for low overhead), isolated prefixes in S3/MinIO, and distinct Redis namespaces. Region-selectable data residency routing is bypassed/simplified (no regional router or physical infrastructure constraints for local environment development). The backend is a FastAPI python service, and the frontend is a React SPA styled with Vanilla CSS to ensure compliance with design standards.

## Technical Context

**Language/Version**: Python 3.11 (Backend), Node.js v18+ with TypeScript (Frontend)

**Primary Dependencies**: 
- *Backend*: FastAPI, SQLAlchemy, Alembic, Pydantic, PyJWT, Stripe (with mock fallback), Qdrant-Client, OpenAI/Google-GenAI SDKs (with pluggable abstract factory layer, defaulting to Gemini), ClamAV (with mock fallback), sentence-transformers (for cross-encoder, with mock fallback)
- *Frontend*: React, TypeScript, Vite, Lucide-React, Recharts

**Storage**: PostgreSQL (RDBMS), Qdrant (Vector DB), AWS S3 or MinIO (Document Storage), Redis (Caching & Rate Limiting)

**Testing**: pytest, pytest-asyncio, httpx (Backend); Vitest, React Testing Library (Frontend)

**Target Platform**: Local development environment (Docker Compose/Linux) / standard unified cloud deployment (single regional database & backend service)

**Project Type**: Web Application (Frontend + Backend)

**Performance Goals**: 
- AI message generation and retrieval: < 5 seconds response time
- API endpoint latency: < 200ms (excluding LLM inference)
- Admin dashboard pages: < 2s load time under normal load

**Constraints**:
- Absolute tenant data isolation at rest via PostgreSQL RLS and Qdrant payload filters
- Single deployment environment (regional residency routing omitted per user request)
- Full RTL and Arabic character rendering support for all dashboard elements (Outfit + Cairo fonts)
- Stripe usage soft-limits with async overage billing calculations

**Scale/Scope**: Up to 10,000 tenants, 1,000,000 conversations per month, and 100 concurrent human agents.

## Constitution Check

*GATE: Passed. Principles from `.specify/memory/constitution.md` have been evaluated against this plan (with user deviations approved for regional routing and Qdrant collection density).*

| Principle | Status | Implementation Details / Verification |
|-----------|--------|--------------------------------------|
| **I. Tenant Isolation & Data Residency** | PASS | Handled via PostgreSQL RLS (middleware context resolution) and single Qdrant collection metadata/payload filtering on `tenant_id`. Dynamic regional database routing is omitted per user request. |
| **II. API-First & Standalone Libraries** | PASS | The RAG engine, billing (Stripe mockable), and audit log system will be implemented as standalone python modules in `backend/src/services/` and testable independently. |
| **III. Test-Driven Development (TDD)** | PASS | Unit/integration tests in `backend/tests/` and `frontend/tests/` will be written to validate contracts and schemas before finalizing implementation. |
| **IV. Hybrid Search & Vector RAG Accuracy** | PASS | Search pipeline in `backend/src/services/rag.py` executes sparse keyword (Postgres FTS) + dense vector search (Qdrant) combined via reciprocal rank fusion (RRF) and re-ranked using a local cross-encoder model (with mock fallback). |
| **V. Full Internationalization & RTL-First** | PASS | Frontend layout dynamically adjusts using a standard direction hook (`dir="rtl"`) on the main container with RTL CSS mirroring. Outfit (LTR) and Cairo (RTL) fonts are loaded via CSS tokens. |

## Project Structure

### Documentation (this feature)

```text
specs/001-moreclient-ai-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api.yaml         # OpenAPI spec for backend
│   └── widget.json      # Embeddable widget configuration schema
└── checklists/
    └── requirements.md  # Specification Quality Checklist
```

### Source Code (repository root)

We choose **Option 2: Web application** (frontend + backend) structure.

```text
backend/
├── src/
│   ├── main.py                    # FastAPI application entrypoint
│   ├── config.py                  # Environment variables & settings
│   ├── cli.py                     # CLI administration interface
│   ├── database.py                # Database connection & session lifecycle
│   ├── api/                       # API routes
│   │   ├── auth.py
│   │   ├── tenants.py
│   │   ├── assistants.py
│   │   ├── knowledge.py
│   │   ├── chat.py
│   │   ├── agent_chat.py
│   │   ├── leads.py
│   │   ├── training.py
│   │   ├── notifications.py
│   │   ├── exports.py
│   │   ├── analytics.py
│   │   ├── webhooks.py
│   │   ├── sockets.py             # WebSockets for live agent escalation
│   │   └── middleware/
│   │       └── rbac.py            # RBAC permission enforcement
│   ├── models/                    # DB Models (SQLAlchemy with RLS)
│   └── services/                  # Standalone services (RAG, billing, virus scan)
│       ├── scanner.py             # ClamAV virus scanning (with mock fallback)
│       ├── extractor.py           # Document text extraction & chunking
│       ├── vectorizer.py          # Embedding generation & vector indexing
│       ├── scraper.py             # URL scraping
│       ├── versioning.py          # Knowledge version snapshots
│       ├── search.py              # Hybrid search (PostgreSQL FTS + Qdrant payload filters)
│       ├── intelligence.py        # Intent, sentiment, query rewriting
│       ├── rag.py                 # LLM prompt builder & RAG generator (pluggable OpenAI/Gemini)
│       ├── agent_manager.py       # Agent routing (Round Robin / Least Busy / Skill)
│       ├── billing.py             # Stripe usage sync & overage metering (with mock fallback)
│       ├── notifications.py       # Email (with file/console log fallback) + in-app delivery
│       └── audit.py               # Immutable audit log middleware
└── tests/
    ├── conftest.py
    ├── unit/                      # Unit tests for services (RAG, billing)
    ├── integration/               # Integration tests (RLS validation, isolation)
    ├── contract/                  # API contract tests (one per API module)
    └── load/                      # Load and scale validation tests

frontend/
├── src/
│   ├── main.tsx                   # React entrypoint
│   ├── index.css                  # Global CSS / tokens / design variables (Outfit + Cairo fonts)
│   ├── components/                # UI components (widgets, RTL layout containers)
│   │   └── NotificationBell.tsx
│   ├── pages/                     # Dashboard screens
│   │   ├── Onboarding.tsx
│   │   ├── AssistantBuilder.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── AgentInbox.tsx
│   │   ├── Billing.tsx
│   │   ├── TrainingCenter.tsx
│   │   ├── Leads.tsx
│   │   └── Analytics.tsx
│   └── services/                  # API client libraries
└── tests/
    ├── setup.ts
    ├── components/                # Component & page rendering tests
    └── performance/               # Dashboard load time validation
```

**Structure Decision**: Option 2 (Web application) is selected to maintain clear separation between the Python FastAPI backend and the React TypeScript frontend.

## Complexity Tracking

*No principles violated. The project layout and stack conform to the Project Constitution.*
