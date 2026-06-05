<!--
SYNC IMPACT REPORT
- Version Change: None -> 1.0.0 (Initial Ratification)
- Principles Defined:
  * Principle 1: I. Multi-Tenancy Row-Level Security (RLS) Isolation
  * Principle 2: II. Per-Tenant Vector Store Isolation
  * Principle 3: III. Subdomain-Based Resolution & JWT Token Validation
  * Principle 4: IV. Resource Quota Enforcement & Rate Limiting
  * Principle 5: V. Decoupled Asynchronous Processing (Celery + Redis)
- Added Sections:
  * Core Technology Stack and Architecture Constraints
  * Compliance, Security, and Tenant Offboarding
- Templates requiring updates:
  * .specify/templates/plan-template.md (✅ updated)
  * .specify/templates/spec-template.md (✅ updated)
  * .specify/templates/tasks-template.md (✅ updated)
- Follow-up TODOs: None
-->

# Multi-Tenant AI Assistant Platform Constitution

## Core Principles

### I. Multi-Tenancy Row-Level Security (RLS) Isolation
Data isolation must be strictly enforced at the database layer. Every tenant-specific table MUST carry a mandatory `tenant_id` (UUID) column. Row-Level Security (RLS) policies MUST be enabled and defined on all tenant-specific tables (including `users`, `assistants`, `documents`, `conversations`, `messages`, and `quota_logs`). Every backend database transaction MUST set the current tenant context using `SET LOCAL app.current_tenant_id = '<uuid>'` in the middleware. Queries executed without this context must fail at the database level.
*Rationale: Secure tenant isolation is a non-negotiable requirement of the SaaS model. Application-level filtering is error-prone and insecure; database-enforced RLS ensures strict data boundaries.*

### II. Per-Tenant Vector Store Isolation
ChromaDB collections must be strictly isolated per tenant. Each tenant MUST have a dedicated ChromaDB collection named `tenant_{uuid}` where `uuid` is the tenant's UUID. All queries and upserts to ChromaDB MUST embed `tenant_id` in document metadata for validation and cross-verification at query time. During tenant offboarding, the tenant's collection MUST be deleted completely.
*Rationale: Shared vector collections risk semantic search leakages across tenants if filters are incorrectly applied. Dedicated collections ensure complete partition boundaries.*

### III. Subdomain-Based Resolution & JWT Token Validation
Tenant resolution is centralized and resolved before routing to core application logic. Subdomain hostnames (e.g. `client.platform.com`) MUST be resolved in the Next.js frontend middleware. The resolved tenant slug MUST be validated against the registry (using a Redis cache layer for speed) and forwarded to the backend via the `X-Tenant-ID` header. The backend MUST authenticate requests using JWT tokens containing the `tenant_id` and RBAC roles (`owner`, `admin`, `member`, `viewer`), validating that the header `X-Tenant-ID` matches the JWT payload `tenant_id`.
*Rationale: Centralized routing and token validation ensure uniform tenant propagation and block unauthorized entry points.*

### IV. Resource Quota Enforcement & Rate Limiting
The platform must protect its shared compute resources and enforce usage limits per pricing tier. Redis token buckets MUST be used to enforce API rate limits (default: 100 req/min per tenant) at both the Nginx and FastAPI middleware layers. Real-time message/token quotas MUST be tracked per tenant, with hourly rollups stored in `quota_logs` and cached in Redis. Requests exceeding quotas or rate limits must be rejected with HTTP 429 or appropriate error codes.
*Rationale: High-cost AI/LLM tokens and compute resources must be protected from abuse, system degradation, or runaway costs.*

### V. Decoupled Asynchronous Processing (Celery + Redis)
Long-running operations such as document text extraction, text chunking, embedding, and vector upserting must be decoupled from the API request-response cycle. All file processing and vector store synchronization MUST be handled as asynchronous background tasks using Celery workers with Redis as the broker/backend. Heavy tasks MUST run on dedicated task queues (`ingestion` for files, `maintenance` for rollups/cleanups) to prevent API latency spikes.
*Rationale: Text parsing (e.g., PyMuPDF, docx2txt) and embedding generation are slow, blocking operations. Decoupling them keeps the API responsive and ensures resilience via automatic task retries.*

## Core Technology Stack and Architecture Constraints
The application is structured as a Monolithic RAG SaaS:
* **Frontend**: Next.js 14+ (App Router), NextAuth.js.
* **Backend**: FastAPI (Python 3.11+), Celery 5.
* **Databases**: PostgreSQL 16, ChromaDB (Vector Store), Redis 7 (Cache, Broker, Rate Limiting).
* **Storage**: MinIO (self-hosted S3-compatible object storage).
* **Reverse Proxy**: Nginx (SSL termination and subdomain routing).
* **Deployment**: All deployments must target Docker and Docker Compose for development and production parity.

## Compliance, Security, and Tenant Offboarding
* **HTTPS Enforcement**: All web and API traffic must use HTTPS with HSTS headers. All session and auth cookies must be configured with `Secure; HttpOnly; SameSite=Strict`.
* **Outbound Webhook Security**: All outgoing webhooks must be signed with HMAC-SHA256 using a tenant-specific secret to verify authenticity.
* **Tenant Data Purge (GDPR Compliance)**: Upon tenant deletion or offboarding, a complete purge must be executed in sequence:
  1. Cascade delete all PostgreSQL records associated with the tenant.
  2. Drop the ChromaDB collection `tenant_{uuid}`.
  3. Delete all object storage files under `tenant/{uuid}/`.
  4. Revoke all active JWTs by adding them to the Redis blocklist.

## Governance
* The constitution represents the non-negotiable guidelines of the Multi-Tenant AI Assistant Platform.
* All code contributions, PR reviews, and design specifications must be verified against these core principles.
* Changes to the database schema must include Alembic migrations and explicitly enable and define RLS policies for any new tenant-specific table.
* Development and implementation tasks should refer to [AGENTS.md](file:///home/mahmoud/Desktop/MoreClientQ/AGENTS.md) and [plan.md](file:///home/mahmoud/Desktop/MoreClientQ/plan.md) for execution details.

**Version**: 1.0.0 | **Ratified**: 2026-06-05 | **Last Amended**: 2026-06-05
