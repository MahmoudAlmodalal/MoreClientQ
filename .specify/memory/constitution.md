# MoreClientQ Project Constitution

## Core Principles

### I. Tenant Isolation & Data Residency (NON-NEGOTIABLE)
All tenant data must be strictly isolated. Row Level Security (RLS) is mandatory in PostgreSQL. Vector embeddings must use separate Qdrant collections. S3 storage and Redis cache must use tenant-prefixed namespaces. Data residency (GCC vs Global) chosen at signup must be strictly enforced at the infrastructure/routing level.

### II. API-First & Standalone Libraries
Core business logic (RAG engine, billing adapter, audit logging) must be written as standalone, modular packages that can be run independently of the web server. Expose all administrative operations via a CLI interface.

### III. Test-Driven Development (TDD)
Write unit and integration tests before writing feature code. All API endpoints must have corresponding contract tests that validate input/output schemas. Ensure test coverage is monitored and code cannot merge without tests passing.

### IV. Hybrid Search & Vector RAG Accuracy
The search pipeline must implement hybrid search (sparse keyword + dense vector) followed by cross-encoder re-ranking. Retrieval accuracy and LLM prompt context length must be optimized to stay within token limits and maintain response latency under 5 seconds.

### V. Full Internationalization & RTL-First
The admin and agent user interfaces must treat LTR (English) and RTL (Arabic) as first-class layouts. Layout mirroring, RTL-compliant typography (Outfit/Cairo fonts), and direction-aware CSS attributes must be verified for all components during UI development.

## Additional Constraints
- **Database**: PostgreSQL with Row-Level Security (RLS).
- **Backend Framework**: Python 3.11 with FastAPI.
- **Frontend Framework**: React with TypeScript and Vite.
- **Styling**: Vanilla CSS (no Tailwind CSS unless requested).
- **Security**: JWT-based authentication with refresh token rotation. Immutable audit logs with 365-day retention.

## Governance
This constitution governs all development on MoreClientQ. Complexity must be justified. All pull requests must verify compliance with these core principles.

**Version**: 1.0.0 | **Ratified**: 2026-06-05 | **Last Amended**: 2026-06-05
