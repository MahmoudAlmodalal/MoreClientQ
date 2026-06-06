# Quickstart Guide: Project Foundation Setup

This guide helps developers launch the local development environment and run verification checks on the newly established foundations.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Git**
- **Docker Desktop** (v24.0+) or **Docker Engine** with **Docker Compose** (v2.0+)

---

## 2. Setting Up the Environment

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
   *Note: Open `.env` and verify database/cache connection variables align with your docker compose config.*

3. **Start All Services**:
   Launch the containers in detached mode:
   ```bash
   docker compose up -d --build
   ```
   This pulls and builds the necessary images for Next.js, FastAPI, PostgreSQL, Redis, ChromaDB, MinIO, and Celery workers/beat.

4. **Verify Container Status**:
   Ensure all 8 containers are running:
   ```bash
   docker compose ps
   ```

---

## 3. Database Schema & Migration Initialization

1. **Run Alembic Migrations**:
   Run the migration command inside the backend container to build the schema:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. **Verify Database Tables**:
   Confirm that all 7 core tables are present:
   ```bash
   docker compose exec postgres psql -U user -d platform -c "\dt"
   ```

---

## 4. Verifying Health Check Endpoint

1. **Trigger health check**:
   Send a GET request to the FastAPI backend health service:
   ```bash
   curl -i http://localhost:8000/api/v1/health
   ```

2. **Expected Response (HTTP 200 OK)**:
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
