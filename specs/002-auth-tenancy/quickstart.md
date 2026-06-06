# Quickstart Guide: Auth & Tenancy

This guide walks you through setting up and verifying the Auth & Tenancy system in your local development environment.

---

## 1. Prerequisites & Environment Setup

Ensure you have Docker and Docker Compose installed.

### 1.1 Docker Compose Services
Start the PostgreSQL database and Redis services:
```bash
docker compose up -d postgres redis
```

### 1.2 Configuration Files
Verify that `.env` files exist in both `backend/` and `frontend/` folders. They should configure the following values:
* **Backend (`backend/.env`)**:
  ```ini
  DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/platform
  REDIS_URL=redis://localhost:6379/0
  JWT_SECRET=super-secure-key-change-in-production
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=60
  ```
* **Frontend (`frontend/.env.local`)**:
  ```ini
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  NEXTAUTH_SECRET=another-super-secure-session-secret
  ```

---

## 2. Database Initialization & Migrations

Run database migrations via Alembic to create tables and activate RLS policies:
```bash
# From repository root
cd backend
pip install -r requirements.txt
alembic upgrade head
```

Verify that Row-Level Security is enabled in PostgreSQL:
```bash
docker compose exec postgres psql -U postgres -d platform -c "\d users"
```
Ensure that the output includes:
`Row Level Security: Enabled`

---

## 3. Running Services locally

### 3.1 Run backend (FastAPI)
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Run frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Subdomain Routing Configuration

The platform resolves tenants using subdomains (e.g., `http://acme.localhost:3000`). Modern browsers resolve `*.localhost` to `127.0.0.1` automatically. If your local system does not, append the mapping to your hosts file:

* **Linux / macOS (`/etc/hosts`)**:
  ```text
  127.0.0.1       platform.localhost
  127.0.0.1       acme.platform.localhost
  127.0.0.1       beta.platform.localhost
  ```

---

## 5. End-to-End API Verification Flow

You can test the core registration, authentication, and RLS mechanisms using the following cURL commands.

### 5.1 Register a Tenant & Owner Account
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "acme",
    "tenant_name": "Acme Corp",
    "email": "owner@acme.com",
    "password": "Password123!"
  }'
```

### 5.2 Authenticate & Retrieve Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@acme.com",
    "password": "Password123!"
  }'
```
*Save the returned `access_token` as `$ACCESS_TOKEN` and the tenant ID from registration as `$TENANT_ID`.*

### 5.3 Send user invitation (Simulated Email)
```bash
curl -X POST http://localhost:8000/api/v1/users/invite \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@acme.com",
    "role": "member"
  }'
```
The response returns a token. Use that invitation token value to register the member user.

### 5.4 Test RLS Enforcement
To check if cross-tenant leakage is blocked:
1. Log in to a separate tenant `beta` (register tenant `beta` first).
2. Attempt to read the users table using `GET /api/v1/users` with the `X-Tenant-ID` header set to `beta`'s ID, but utilizing the authentication token from `owner@acme.com`.
3. The API must reject the request with `403 Forbidden` or return empty context records due to mismatching claims.
