# Research: Assistant & Knowledge Base — Phase 0

**Branch**: `003-assistant-knowledge-base` | **Date**: 2026-06-06

---

## 1. Technical Stack (Resolved from codebase)

| Area | Decision | Source |
|---|---|---|
| Language / Runtime | Python 3.11 (backend), TypeScript / Next.js 14 App Router (frontend) | `requirements.txt`, `package.json` |
| Backend Framework | FastAPI 0.110.0 + Uvicorn | `requirements.txt` |
| ORM | SQLAlchemy 2.0 async (`asyncpg`) | `requirements.txt`, existing models |
| Database | PostgreSQL 16 with RLS via `app.current_tenant_id` session variable | `constitution.md`, existing models |
| Vector Store | ChromaDB 0.4.24 — per-tenant collection `tenant_{uuid}` | `requirements.txt`, `constitution.md` |
| Object Storage | MinIO (self-hosted S3-compatible) via `minio` Python SDK | `plan.md`, `docker-compose.yml` |
| Background Queue | Celery 5.3.6 + Redis broker | `requirements.txt`, `tasks/celery_app.py` |
| Auth / RBAC | JWT via `PyJWT`, roles enforced by `require_roles()` dep in `security.py` | `app/core/security.py` |
| File Parsing | PyMuPDF 1.23.26 (PDF), docx2txt 0.8 (DOCX), built-in (TXT) | `requirements.txt` |
| HTTP Client | httpx 0.27.0 — used for URL pre-flight validation (synchronous HEAD) | `requirements.txt` |
| Frontend Testing | Jest + React Testing Library | `jest.config.ts` |
| Backend Testing | pytest + pytest-asyncio | `requirements.txt`, `pytest.ini` |

---

## 2. Dependency Gap: MinIO SDK

**Finding**: `minio` Python SDK is **not** in `requirements.txt`. The existing services reference MinIO (plan.md, docker-compose.yml) but no client is installed.

- **Decision**: Add `minio>=7.2.0` to `requirements.txt`.
- **Rationale**: The official MinIO Python SDK supports `put_object`, `get_object`, `remove_object`, and presigned URLs. It is the standard client for self-hosted MinIO. `boto3` (S3-compatible) is an alternative but adds heavier AWS dependencies.
- **Alternatives considered**: `boto3` — rejected for weight; `httpx` raw calls — rejected as fragile without SDK abstractions.

---

## 3. Text Chunking Strategy

**Finding**: No LangChain or chunking library is installed. The plan.md references `RecursiveCharacterTextSplitter` from LangChain.

- **Decision**: Implement a **lightweight custom chunker** in `app/services/rag/chunker.py` rather than adding LangChain as a dependency.
- **Rationale**: LangChain adds ~150MB of transitive dependencies for a single utility. A recursive character splitter with `chunk_size=512, overlap=64` is trivial to implement in ~30 lines of Python. This avoids dependency bloat while meeting the spec's chunking requirements.
- **Alternatives considered**: LangChain `RecursiveCharacterTextSplitter` — rejected (dependency overhead); `nltk` — rejected (sentence-level splitting not needed for RAG).

---

## 4. URL Pre-flight Validation

**Finding**: httpx 0.27.0 is already installed. Clarification Q4 resolved that URLs must be validated synchronously before queuing.

- **Decision**: Issue a synchronous `httpx.head(url, follow_redirects=True, timeout=10)` call in the API handler before dispatching the Celery task. Reject if:
  - Connection error / timeout
  - Status code is not 2xx
  - Final URL (after redirects) contains login/auth path heuristics (`/login`, `/auth`, `/signin`, `?redirect=`)
- **Rationale**: HEAD request is cheap (no body download), fast, and gives reliable reachability signal. The 10-second timeout balances responsiveness with slow servers.
- **Alternatives considered**: Full GET request — rejected (downloads full body at submission time); deferred validation in Celery — rejected (Clarification Q4 mandates immediate rejection).

---

## 5. Document Uniqueness Constraint

**Finding**: The existing `Document` model has no unique constraint on `(assistant_id, filename)`. Clarification Q1 requires duplicate filenames to be rejected.

- **Decision**: Add a `UniqueConstraint("assistant_id", "filename")` to the `Document` model and a corresponding Alembic migration.
- **Rationale**: Enforcing uniqueness at the DB layer guarantees the constraint regardless of race conditions or direct DB access.
- **Alternatives considered**: Application-level check only — rejected (subject to TOCTOU race on concurrent uploads).

---

## 6. Document FK: SET NULL → CASCADE

**Finding**: The existing `Document.assistant_id` FK uses `ondelete="SET NULL"`. However, FR-003 and the spec require that deleting an assistant **cascades** to remove all its documents from both storage and the vector index.

- **Decision**: Change `Document.assistant_id` FK to `ondelete="CASCADE"` and add an Alembic migration. The cascade delete of ChromaDB chunks and MinIO objects must be handled in the API layer (background task triggered on assistant delete) since the DB cascade alone only removes the PostgreSQL rows.
- **Rationale**: `SET NULL` orphans documents; `CASCADE` at DB level plus an API-layer cleanup task ensures complete removal.
- **Alternatives considered**: Keep `SET NULL`, handle everything at app level — rejected (inconsistent if app-layer logic fails).

---

## 7. Document Status Polling (FR-009)

**Finding**: The spec assumes client-side polling (every 5 seconds) as the Phase 2 default. No SSE or WebSocket infrastructure is needed for Phase 2.

- **Decision**: Expose a dedicated `GET /api/v1/documents/{id}/status` endpoint returning `{id, status, chunk_count, error_message}`. The frontend polls this endpoint.
- **Rationale**: Simplest implementation consistent with Phase 2 scope. SSE is deferred to a later phase per Assumption in spec.
- **Alternatives considered**: Server-Sent Events — deferred; WebSocket — deferred.

---

## 8. Ingestion Task Retry Policy

**Finding**: Clarification Q2 set 3 retries with 30-second delays (4 total attempts).

- **Decision**: Configure Celery task with `max_retries=3, default_retry_delay=30`. Use `self.retry(exc=exc, countdown=30)` on transient failures.
- **Rationale**: Matches Q2 answer exactly. Aligns with existing `celery_app.py` configuration pattern.

---

## 9. Structured Ingestion Failure Logging (FR-019)

**Finding**: Clarification Q5 requires structured log entries per failure.

- **Decision**: Use Python's `structlog`-compatible `logging` (already available via `logging.getLogger`) with a structured dict payload: `{event: "ingestion_failed", tenant_id, document_id, filename, reason, attempt, timestamp}`. Log at `ERROR` level.
- **Rationale**: `structlog` is referenced in plan.md section 12 for production. Using `logging` with structured dict messages is compatible with the planned Loki sink.

---

## 10. Frontend: Assistant & Document Pages

**Finding**: The frontend `app/` directory only has `(auth)` routes and the root page. No `(dashboard)` route group exists yet.

- **Decision**: Create the `(dashboard)` route group under `frontend/app/` with nested routes for `/assistants` and `/assistants/[id]/knowledge-base`. Reuse the existing shadcn/ui component library (confirmed via `components.json`).
- **Rationale**: The dashboard route group is the correct App Router pattern for protected pages. shadcn/ui is already installed — no new UI library needed.

---

## 11. Widget Embed Code Format

**Finding**: FR-014 requires a copy-pasteable embed code snippet per assistant.

- **Decision**: Generate a static snippet at `GET /api/v1/assistants/{id}/embed` response time:
  ```html
  <script src="https://{ROOT_DOMAIN}/widget.js" data-assistant="{assistant_id}" data-theme="light" data-position="bottom-right"></script>
  ```
- **Rationale**: Simple, deterministic, no state needed. The widget bundle itself is a Phase 5 deliverable; Phase 2 only generates the embed code.

---

## Summary of New Dependencies to Add

| Package | Version | Reason |
|---|---|---|
| `minio` | `>=7.2.0` | MinIO object storage SDK |

No other new packages required — all other needs are covered by existing dependencies.
