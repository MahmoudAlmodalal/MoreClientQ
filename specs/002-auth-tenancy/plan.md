# Implementation Plan: Auth & Tenancy

**Branch**: `002-auth-tenancy` | **Date**: 2026-06-06 | **Spec**: [spec.md](file:///home/mahmoud/Desktop/MoreClientQ/specs/002-auth-tenancy/spec.md)

**Input**: Feature specification from `specs/002-auth-tenancy/spec.md`

## Summary

This feature implements the foundational authentication and tenancy architecture for the Multi-Tenant AI Assistant Platform. The solution provides secure tenant registration, subdomain-based resolution in Next.js middleware, FastAPI authentication utilizing stateless JWTs, database Row-Level Security (RLS) isolation in PostgreSQL, and static Role-Based Access Control (RBAC). A Redis blocklist will be utilized for instant token revocation, and the user invitation flow is simulated in Phase 1 without SMTP configurations.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript / Node 18+ (Frontend)

**Primary Dependencies**: FastAPI (python), Next.js 14+ (App Router), PyJWT, NextAuth.js, SQLAlchemy 2.0, Alembic, Redis (python-redis/ioredis)

**Storage**: PostgreSQL 16 (for structured tenant/user data and RLS), Redis 7 (for token blocklist, session validation, and tenant slug cache)

**Testing**: pytest (Backend integration and RLS checks), Playwright / Next.js middleware unit testing (Frontend)

**Target Platform**: Linux / Docker Compose (Local development and Production parity)

**Project Type**: Monolithic RAG SaaS (Web application with frontend and backend)

**Performance Goals**: Next.js middleware subdomain resolution < 15ms via Redis cache; JWT authentication and context injection overhead < 5ms; token/session revocation cluster-wide < 1 second.

**Constraints**: Tenant isolation must be strictly enforced at the DB layer via RLS policies; API rate-limiting must reject excessive requests (100 req/min/tenant); no SMTP configured in Phase 1 (simulated invitation link return).

**Scale/Scope**: Support 10k+ tenants, up to 1M users, single Postgres database, scalable Redis caching cluster.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Constraint | Status | Validation / Alignment Detail |
| :--- | :--- | :--- |
| **I. Multi-Tenancy RLS Isolation** | **PASSED** | PostgreSQL tables (`users`, `tenants`, `quota_logs`) will carry a UUID `tenant_id` and have Postgres RLS enabled. Middleware sets `app.current_tenant_id` locally. |
| **II. Per-Tenant Vector Store Isolation** | **PASSED** | ChromaDB collections are deferred to future phases (as resolved in Spec Clarifications Q3). |
| **III. Subdomain Resolution & JWT Validation** | **PASSED** | Next.js middleware resolves subdomains, validates them via Redis, and forwards `X-Tenant-ID`. FastAPI backend validates header against JWT claims. |
| **IV. Resource Quota & Rate Limiting** | **PASSED** | Rate limiting is deferred to future API middleware tasks; basic Redis integration is verified for JWT revocation and tenant cache. |
| **V. Decoupled Asynchronous Processing** | **PASSED** | Celery queueing is deferred to later ingest tasks. |
| **Technology Stack Constraints** | **PASSED** | Strictly uses Next.js 14, FastAPI, PostgreSQL 16, Redis 7, and Docker Compose. |
| **Compliance, Security, & Tenant Offboarding** | **PASSED** | Phase 1 offboarding strictly implements Postgres cascade deletes and JWT blocklist revocation. Chroma/MinIO cleanup is deferred. |

## Project Structure

### Documentation (this feature)

```text
specs/002-auth-tenancy/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/             # API endpoints (auth, registration, team/user management)
│   ├── core/            # Security, config, and middleware (TenantMiddleware, JWT verify)
│   ├── db/              # Session setup, database engine, migrations config
│   ├── models/          # SQLAlchemy schemas (Tenant, User, QuotaLog)
│   ├── services/        # Business logic (auth services, token management)
│   └── main.py          # App initialization and middleware registration
├── alembic/             # Database migrations
└── tests/               # Backend tests (unit, integration, RLS validation)

frontend/
├── app/                 # Next.js App Router (auth pages, registration, dashboard)
├── components/          # Reusable UI components
├── lib/                 # Utility files, API clients
└── middleware.ts        # Next.js subdomain resolution & tenant injection middleware
```

**Structure Decision**: Web application layout containing `backend/` and `frontend/` directories. All new/modified source files must align with these directories.

## Complexity Tracking

> *No Constitution Check violations detected. Current architecture strictly adheres to platform principles.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| None | N/A | N/A |
