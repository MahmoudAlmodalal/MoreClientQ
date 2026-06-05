# Implementation Plan: MoreClient AI Enterprise Platform

**Branch**: `003-fix-all-buge` | **Date**: 2026-06-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-fix-all-buge/spec.md`

## Summary

The MoreClient AI Enterprise Platform is a multi-tenant AI customer support platform. It supports tenant registration, workspace configuration, RAG-based AI chat with hybrid search, human agent escalation, Stripe subscription billing, and a bilingual Arabic (RTL) / English (LTR) admin dashboard.

This plan is based on the decisions established in `001-moreclient-ai-platform` and carries them forward with clarification refinements from the `003-fix-all-buge` spec: explicit processing SLAs, cosine similarity threshold for context pruning, mandatory CSAT triggers, per-source hallucination re-indexing, usage alert thresholds, and frontend RBAC rendering requirements.

The technical approach implements logical database isolation using PostgreSQL Row Level Security (RLS) via FastAPI middleware/dependencies executing `SET LOCAL app.current_tenant_id = :tenant_id`, a single shared Qdrant collection with metadata/payload filtering on `tenant_id`, isolated prefixes in S3/MinIO, and distinct Redis namespaces. The backend is a FastAPI Python service; the frontend is a React SPA styled with Vanilla CSS.

## Technical Context

**Language/Version**: Python 3.11 (Backend), Node.js v18+ with TypeScript (Frontend)

**Primary Dependencies**:
- *Backend*: FastAPI, SQLAlchemy, Alembic, Pydantic, PyJWT, Stripe (with mock fallback), Qdrant-Client, OpenAI/Google-GenAI SDKs (pluggable abstract factory layer, defaulting to Gemini), ClamAV (with mock fallback), sentence-transformers (cross-encoder, with mock fallback)
- *Frontend*: React, TypeScript, Vite, Lucide-React, Recharts

**Storage**: PostgreSQL (RDBMS), Qdrant (Vector DB), AWS S3 or MinIO (Document Storage), Redis (Caching & Rate Limiting)

**Testing**: pytest, pytest-asyncio, httpx (Backend); Vitest, React Testing Library (Frontend)

**Target Platform**: Local development environment (Docker Compose / Linux) / standard unified cloud deployment

**Project Type**: Web Application (Frontend + Backend)

**Performance Goals**:
- AI message generation and retrieval: < 5 seconds response time
- Knowledge processing pipeline: < 2 minutes per megabyte of uploaded file size (Ready status)
- API endpoint latency: < 200ms (excluding LLM inference)
- Admin dashboard pages: < 2s load time under normal load

**Constraints**:
- Absolute tenant data isolation at rest via PostgreSQL RLS and Qdrant payload filters
- S3/MinIO storage uses tenant-prefixed folder paths; Redis uses tenant-prefixed key namespaces
- Full RTL and Arabic character rendering support for all dashboard elements (Outfit + Cairo fonts)
- Stripe usage soft-limits with async overage billing calculations
- RAG context pruning must discard chunks with cosine similarity < 0.75 before LLM context assembly
- URL scraping capped at depth 1 and 50 total pages per tenant
- CSAT prompt is mandatory (not optional) when an agent marks a conversation resolved
- RBAC enforcement on the frontend: navigation links, buttons, settings pages, and forms MUST be conditionally rendered (hidden or disabled) based on the authenticated user's role

**Scale/Scope**: Up to 10,000 tenants, 1,000,000 conversations per month, and 100 concurrent human agents.

## Constitution Check

*GATE: Passed. Principles from `.specify/memory/constitution.md` have been evaluated against this plan.*

| Principle | Status | Implementation Details |
|-----------|--------|------------------------|
| **I. Tenant Isolation & Data Residency** | PASS | PostgreSQL RLS via middleware context resolution; Qdrant single collection with `tenant_id` payload filter; S3/MinIO tenant-prefixed folders; Redis tenant-prefixed namespaces. |
| **II. API-First & Standalone Libraries** | PASS | RAG engine, billing adapter, and audit log system implemented as standalone Python modules in `backend/src/services/`, independently testable. CLI interface in `backend/src/cli.py`. |
| **III. Test-Driven Development (TDD)** | PASS | Unit/integration tests in `backend/tests/` and `frontend/tests/` written before feature code. All API endpoints have contract tests validating input/output schemas. |
| **IV. Hybrid Search & Vector RAG Accuracy** | PASS | `backend/src/services/search.py` executes sparse keyword (PostgreSQL FTS) + dense vector (Qdrant payload filter) combined via RRF, re-ranked by cross-encoder. Context pruned at 0.75 cosine similarity. |
| **V. Full Internationalization & RTL-First** | PASS | Frontend uses HTML `dir` attribute + logical CSS properties. Outfit (LTR) and Cairo (RTL) fonts loaded via CSS tokens. All forms, tables, and navigation verified in both directions. |

## Spec Refinements from 003

The following clarifications from `003`'s spec over `001` become concrete implementation constraints:

| FR | Constraint | Affected Module |
|----|-----------|-----------------|
| Knowledge processing | Ready status within **2 min / MB** | `services/extractor.py`, `services/vectorizer.py` |
| FR-010 | URL scraping: depth 1, max **50 pages** / tenant | `services/scraper.py` |
| FR-015 | Context compression: prune chunks < **0.75 cosine similarity** | `services/search.py`, `services/rag.py` |
| US-4 / FR-017 | CSAT prompt **mandatory** on agent-resolved conversations | `api/agent_chat.py`, widget CSAT endpoint |
| FR-022 | Hallucination flag must trigger **re-indexing** of specific source file | `services/vectorizer.py`, `api/training.py` |
| FR-009 | Guardrails escalation rules: **message threshold** AND **confidence threshold** | `services/intelligence.py` |
| FR-026/027 | Usage alerts at **80% and 100%** of plan limit | `services/billing.py`, `services/notifications.py` |
| FR-029 | Frontend RBAC: conditional rendering of **all UI elements** | `frontend/src/components/`, all pages |
| FR-033 | Exports triggered via **explicit download buttons** in settings dashboard | `frontend/src/pages/Settings.tsx`, `api/exports.py` |
| FR-007 | Isolation enforced at **database connection and network routing** levels | `database.py`, deployment config |

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-all-buge/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── api.yaml         # OpenAPI spec for backend
│   └── widget.json      # Embeddable widget configuration schema
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

**Option 2: Web application** (frontend + backend)

```text
backend/
├── src/
│   ├── main.py                    # FastAPI application entrypoint
│   ├── config.py                  # Environment variables & settings
│   ├── cli.py                     # CLI administration interface (FR-034)
│   ├── database.py                # Database connection & RLS session lifecycle
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
│   └── services/                  # Standalone services
│       ├── scanner.py             # ClamAV virus scanning (mock fallback)
│       ├── extractor.py           # Document text extraction & chunking
│       ├── vectorizer.py          # Embedding + vector indexing + re-indexing
│       ├── scraper.py             # URL scraping (depth 1, max 50 pages)
│       ├── versioning.py          # Knowledge version snapshots
│       ├── search.py              # Hybrid search + 0.75 cosine pruning
│       ├── intelligence.py        # Intent, sentiment, query rewriting, guardrails
│       ├── rag.py                 # LLM prompt builder & RAG generator
│       ├── agent_manager.py       # Agent routing (Round Robin / Least Busy / Skill)
│       ├── billing.py             # Stripe usage sync, overage, 80%/100% alerts
│       ├── notifications.py       # Email + in-app delivery
│       └── audit.py               # Immutable audit log middleware
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    ├── contract/
    └── load/

frontend/
├── src/
│   ├── main.tsx
│   ├── index.css                  # Global CSS / tokens (Outfit + Cairo fonts)
│   ├── components/
│   │   ├── NotificationBell.tsx
│   │   └── RBACGuard.tsx          # Conditional render wrapper by role (FR-029)
│   ├── pages/
│   │   ├── Onboarding.tsx
│   │   ├── AssistantBuilder.tsx
│   │   ├── KnowledgeBase.tsx
│   │   ├── AgentInbox.tsx
│   │   ├── Billing.tsx
│   │   ├── TrainingCenter.tsx
│   │   ├── Leads.tsx
│   │   ├── Analytics.tsx
│   │   └── Settings.tsx           # Export download buttons (FR-033)
│   └── services/
└── tests/
    ├── setup.ts
    ├── components/
    └── performance/
```

**Structure Decision**: Option 2 (Web application) selected to maintain clear separation between the Python FastAPI backend and the React TypeScript frontend.

## Complexity Tracking

*No principles violated. The project layout and stack conform to the Project Constitution.*
