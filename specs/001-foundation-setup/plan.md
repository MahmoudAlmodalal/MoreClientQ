# Implementation Plan: Project Foundation Setup

**Branch**: `001-foundation-setup` | **Date**: 2026-06-05 | **Spec**: [spec.md](file:///home/mahmoud/Desktop/MoreClientQ/specs/001-foundation-setup/spec.md)

**Input**: Feature specification from `/specs/001-foundation-setup/spec.md`

## Summary

This plan outlines the setup for Phase 0 (Project Foundation Setup). We will establish a multi-project monorepo containing a FastAPI backend skeleton, Next.js 14 frontend skeleton (configured with shadcn/ui), Alembic database migrations, and a docker-compose configuration orchestrating 8 local development services (Postgres, Redis, ChromaDB, MinIO, Next.js, FastAPI, Celery worker, Celery beat).

## Technical Context

**Language/Version**: Python 3.11+, Node 20+, TypeScript

**Primary Dependencies**: FastAPI, Next.js 14, Alembic, Celery 5, shadcn/ui

**Storage**: PostgreSQL 16 (Relational DB), ChromaDB (Vector Store), Redis 7 (Cache, Broker, Rate Limiting), MinIO (Object Storage)

**Testing**: pytest (backend), Vitest and Playwright (frontend)

**Target Platform**: Linux (Docker / Docker Compose dev environment)

**Project Type**: Monolithic RAG SaaS

**Performance Goals**: Clean Docker Compose environment startup time under 3 minutes; health check endpoint response latency under 150ms.

**Constraints**: Local dev environment uses HTTP (SSL termination by Nginx is deferred to production deployment phases); environment configuration must be centralized using a root `.env` template.

**Scale/Scope**: Local development environment with 8 orchestrated containers running concurrently.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Multi-Tenancy RLS Isolation**: [PASS] Alembic migrations initialized in this phase will configure the schema with the mandatory `tenant_id` column on all tenant tables, supporting CASCADE deletions on tenant removal. RLS setup script structure will be defined.
- **Principle II: Per-Tenant Vector Store Isolation**: [PASS] ChromaDB HTTP server is orchestrated via docker-compose to verify client connections and health check.
- **Principle III: Subdomain-Based Resolution**: [PASS] Next.js 14 dev container is prepared to support middleware resolution in subsequent phases.
- **Principle IV: Resource Quota & Rate Limiting**: [PASS] Redis container included in the local orchestration.
- **Principle V: Decoupled Asynchronous Processing**: [PASS] Celery worker and Celery beat container configurations included in the compose setup to support file ingestion workflows.
- **Core Technology Stack Constraints**: [PASS] FastAPI, Next.js, Postgres 16, Redis 7, ChromaDB, and MinIO versions matched.

All Gates passed successfully. No architecture or technology violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/001-foundation-setup/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── health-check.json
└── checklists/          # Specification quality checklist
    └── requirements.md
```

### Source Code (repository root)

The repository uses a multi-project monorepo layout:

```text
/home/mahmoud/Desktop/MoreClientQ/
├── backend/                  # FastAPI App
│   ├── alembic/              # Migration configurations
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py # Health checks
│   │   │       └── router.py
│   │   ├── core/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                 # Next.js App
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   ├── Dockerfile
│   └── package.json
│
├── nginx/                    # Local reverse proxy
│   └── nginx.conf
│
├── docker-compose.yml        # Development environment orchestrator
├── .env.example              # Centralized environment template
└── AGENTS.md                 # Agent context reference
```

**Structure Decision**: Option 2: Web application (frontend + backend structure) selected as mandated by the SaaS architecture.

## Complexity Tracking

*No violations detected. No complexity tracking necessary.*
