# Research: Project Foundation Setup

This document outlines the research, technical decisions, and best practices for establishing the monorepo structure, Docker Compose configuration, Alembic migrations, and backend/frontend skeletons for the Multi-Tenant AI Assistant Platform.

---

## 1. Monorepo Directory Layout

### Decision
Establish a multi-project monorepo at the repository root with distinct directories for the backend application, frontend application, reverse proxy configuration, and deployment orchestration.

```text
/home/mahmoud/Desktop/MoreClientQ/
├── backend/                  # FastAPI app and Celery tasks
├── frontend/                 # Next.js frontend application
├── nginx/                    # Reverse proxy configs
├── specs/                    # Specifications and plans
├── docker-compose.yml        # Development environment orchestration
└── .env.example              # Shared environment variables template
```

### Rationale
A monorepo structure makes it simple to version-control both frontend and backend in lockstep, simplifies local development configuration, and makes it easy to run all services using a single `docker-compose.yml` file.

### Alternatives Considered
- **Polyrepo (Separate Repositories)**: Rejected because it introduces complexity in managing schemas, API contracts, environment variables, and Docker Compose across repository boundaries for a small dev team.

---

## 2. Docker Compose Dev Environment & Orchestration

### Decision
Orchestrate 8 services locally: `frontend`, `backend`, `postgres`, `redis`, `chromadb`, `minio`, `celery_worker`, and `celery_beat`. Enforce container startup order using healthcheck-based `depends_on` rules.

- **PostgreSQL**: Standard Relational DB.
- **Redis**: Caching, rate limiting, and Celery broker.
- **ChromaDB**: HTTP client mode connecting to a separate ChromaDB container.
- **MinIO**: S3-compatible local object storage.
- **Backend**: FastAPI web framework running ASGI via Uvicorn.
- **Celery Worker**: Processing tasks from the ingestion queue.
- **Celery Beat**: Triggering periodic cleanup/maintenance tasks.
- **Frontend**: Next.js 14 in development mode.

### Rationale
Having separate containers for database and cache services matches production topology, minimizing "it works on my machine" issues. Controlling startup order with healthchecks prevents backend startup failures due to unavailable database or vector store ports.

### Alternatives Considered
- **Local installation of Postgres/Redis/ChromaDB**: Rejected because it requires manual software installation per developer machine, leading to configuration drift.
- **In-memory ChromaDB / SQLite**: Rejected because we need to test ChromaDB's HTTP client mode and Postgres RLS features from the beginning.

---

## 3. Alembic Migration Setup in Monorepo

### Decision
Initialize Alembic inside the `backend/` directory, rather than the root directory. All migration scripts and database models are co-located in the backend codebase.

### Rationale
Colocating migrations with the backend keeps Python code dependencies self-contained. The database session factory and ORM models are directly imported by Alembic scripts to inspect metadata.

### Alternatives Considered
- **Root-level Alembic Configuration**: Rejected because the root repository lacks python packages and environment setup, requiring duplicate configurations and cross-directory package paths.

---

## 4. FastAPI Health Check Implementation

### Decision
Implement a stateless `/health` endpoint that asynchronously verifies connection health for:
- PostgreSQL via `db.execute("SELECT 1")`
- Redis via `redis.ping()`
- ChromaDB via `chroma_client.heartbeat()`

If all checks pass, returns HTTP 200 OK. If any check fails, returns HTTP 503 Service Unavailable (or HTTP 500) with detailed status.

### Rationale
Checking individual service dependencies provides early warning of configuration issues or infrastructure failure. A simple HTTP response check serves as the perfect target for Docker container healthchecks and load balancer probes.

### Alternatives Considered
- **Simple Static JSON Response**: Rejected because it only verifies that the web server is running, not that it can perform queries or read/write settings.

---

## 5. Next.js 14 Skeleton with shadcn/ui

### Decision
Initialize the frontend project with Next.js 14 using the App Router, TypeScript, and TailwindCSS. Add and configure the `shadcn/ui` component library.

### Rationale
Next.js App Router provides modern SSR capabilities and route optimization. `shadcn/ui` provides high-quality, fully customizable TailwindCSS-styled primitive components that avoid bulky third-party dependencies while allowing us to build premium interfaces.

### Alternatives Considered
- **Vite SPA**: Rejected because Next.js offers built-in middleware for tenant subdomain routing and server-side authentication (NextAuth.js) which are critical for later phases.
