# Multi-Tenant AI Assistant Platform

This repository contains the foundation setup for the **Multi-Tenant AI Assistant Platform**. It is structured as a multi-project monorepo utilizing a modern, decoupled service architecture to enable highly isolated, scalable tenant workloads.

---

## 1. Directory Structure

The project is organized as a monorepo to co-locate services, schemas, and configurations:

```text
.
├── backend/                  # FastAPI Application, Celery tasks & database migrations
├── frontend/                 # Next.js 14 Application (App Router + shadcn/ui)
├── nginx/                    # Reverse proxy configuration (routing & subdomain mapping)
├── specs/                    # Project specifications, plans, and developer guides
├── docker-compose.yml        # Development environment orchestrator (8 services)
├── .env.example              # Shared environment variables template
└── README.md                 # Project entry point and quickstart (this file)
```

---

## 2. Quickstart Guide

This guide helps developers launch the local development environment and run verification checks on the newly established foundations.

### Step 1: Prerequisites

Ensure you have the following installed on your machine:
- **Git**
- **Docker Desktop** (v24.0+) or **Docker Engine** with **Docker Compose** (v2.0+)

### Step 2: Environment Configuration

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd MoreClientQ
   ```

2. **Configure Environment Variables**:
   Copy the example environment template to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
   *Note: Open `.env` and verify database/cache connection variables align with your docker-compose config.*

### Step 3: Start Services

Launch the containers in detached mode:
```bash
docker compose up -d --build
```
This builds and starts the 8 core services:
- **nginx**: Local reverse proxy (Port `80`, `443`)
- **frontend**: Next.js 14 Web UI (Port `3000`)
- **backend**: FastAPI application server (Port `8000`)
- **celery_worker**: Ingestion task queue worker
- **celery_beat**: Scheduled task coordinator
- **postgres**: PostgreSQL 16 database (Port `5432`)
- **redis**: Redis 7 cache/broker (Port `6379`)
- **chromadb**: Chroma vector database (Port `8002`)
- **minio**: Local object storage (Port `9000`/`9001`)

Verify all containers are active:
```bash
docker compose ps
```

### Step 4: Run Database Migrations

Run the migration command inside the backend container to build the schema:
```bash
docker compose exec backend alembic upgrade head
```

Confirm that the core tables are present in PostgreSQL:
```bash
docker compose exec postgres psql -U user -d platform -c "\dt"
```

### Step 5: Verification & Health Check

You can query the backend health endpoint directly to verify connection integrity across the relational database, cache, and vector database:

```bash
curl -i http://localhost:8000/api/v1/health
```

**Expected Response (HTTP 200 OK)**:
```json
{
  "status": "ok",
  "timestamp": "2026-06-05T17:15:00.000Z",
  "services": {
    "database": { "status": "healthy", "latency_ms": 12 },
    "redis": { "status": "healthy", "latency_ms": 3 },
    "chromadb": { "status": "healthy", "latency_ms": 8 }
  }
}
```

---

## 3. Development Commands Cheat Sheet

Here are common commands used during development:

| Action | Command |
|--------|---------|
| Start Dev Services | `docker compose up -d` |
| Rebuild & Start | `docker compose up -d --build` |
| Stop Dev Services | `docker compose down` |
| Stop & Clear Volumes | `docker compose down -v` |
| View Logs | `docker compose logs -f` |
| Run Backend Tests | `docker compose exec backend pytest` |
| Generate Migration | `docker compose exec backend alembic revision --autogenerate -m "description"` |
| Apply Migrations | `docker compose exec backend alembic upgrade head` |

---

## 4. API Endpoints: Auth & Tenancy

All endpoints are prefixed with `/api/v1/auth` unless otherwise noted.

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/auth/register` | Register a new tenant and primary owner | No |
| POST | `/auth/login` | Authenticate and receive JWT tokens | No |
| POST | `/auth/refresh` | Generate new access token from refresh token | No |
| POST | `/auth/logout` | Invalidate current JWT via Redis blocklist | Yes (Bearer) |
| POST | `/auth/invite/accept` | Accept an invitation with token | No |
| GET | `/auth/me` | Return verified JWT claims | Yes (Bearer) |
| POST | `/users/invite` | Send a team invitation | Yes (Owner/Admin) |
| GET | `/users` | List users in current tenant | Yes (Bearer) |
| PATCH | `/users/{user_id}/role` | Update user role | Yes (Owner/Admin) |
| DELETE | `/users/{user_id}` | Remove user from tenant | Yes (Owner/Admin) |
| GET | `/tenants/resolve/{slug}` | Resolve tenant slug to ID | No |
| DELETE | `/tenants/self` | Offboard tenant (cascade purge) | Yes (Owner) |

### Authentication

All protected endpoints require an `Authorization: Bearer <access_token>` header. Tenancy context is passed via the `X-Tenant-ID` header, which is validated against the JWT's `tenant_id` claim.

### Environment Setup

Create `backend/.env` with the following:

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/platform
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=super-secure-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Create `frontend/.env.local` with:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_SECRET=another-super-secure-session-secret
```
