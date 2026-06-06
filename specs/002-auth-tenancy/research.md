# Research Findings: Auth & Tenancy Architecture

This document outlines the core architectural and design decisions established for the Auth & Tenancy system in Phase 1.

## 1. User Email Uniqueness Constraint

* **Decision**: Global Uniqueness.
* **Rationale**: Establishing a unique constraint on the `email` column globally across the `users` table simplifies authentication. During login (`POST /api/v1/auth/login`), the user can be authenticated using email and password alone. This avoids the complexity of requiring users to specify their tenant slug or routing a single email registered across multiple tenants to a selector interface.
* **Alternatives Considered**: 
  * *Tenant-Scoped Uniqueness*: Allowing the same email to exist in different tenants (e.g., `user@company.com` in Tenant A and Tenant B). While standard for enterprise SaaS, it requires routing mechanisms (like subdomain resolution prior to login or tenant selector screens) which are deferred to future phases to keep the Phase 1 login flow straightforward.

## 2. User Invitation Flow in Phase 1

* **Decision**: Simulated Email Ingestion.
* **Rationale**: When a tenant administrator/owner invites a team member via `POST /api/v1/users/invite`, the backend creates an invitation record with a secure token. Rather than attempting to transmit this via SMTP/SES (which requires external server configuration and credentials), the backend will log the invitation link to the console and return it directly in the API response. This allows local testing of the invite accept and registration flow.
* **Alternatives Considered**:
  * *Direct Creation*: Allowing administrators to directly create users with passwords. This was rejected because it does not test the token-based invitation acceptance and signup flow.
  * *Full SMTP Integration*: Rejected to avoid introducing external network dependencies and SMTP setup tasks during the initial authentication phase.

## 3. Tenant Offboarding & Data Purge

* **Decision**: Deferred/Partial Purge.
* **Rationale**: In Phase 1, only PostgreSQL database tables (`users`, `tenants`, `quota_logs`) and Redis cache are present. Therefore, tenant offboarding will perform a PostgreSQL cascade delete (removing the tenant record and all dependent user and log records) and revoke active tenant JWTs in the Redis blocklist. Purges of object storage (MinIO) and ChromaDB collections are deferred until those systems are integrated.
* **Alternatives Considered**:
  * *Stubbed Purge*: Creating mock/placeholder functions for ChromaDB/MinIO. Rejected as it introduces code clutter that will be replaced during those specific integrations.
  * *Deactivation Only*: Restricting offboarding to setting `is_active=False`. Rejected because verifying database cascade deletes and JWT revocation is a critical security step for Phase 1.

## 4. Token Revocation Mechanism

* **Decision**: Redis-backed Token Blocklist.
* **Rationale**: Stateless JWTs are validated cryptographically by the FastAPI auth middleware. To support instant revocation (logout, tenant deactivation, or user suspension within 1 second), the backend will maintain a blocklist in Redis. Revoked token identifiers (`jti`) are stored in Redis with an expiration time equal to the token's remaining time-to-live (TTL). The middleware will perform a fast Redis lookup on every authenticated request.
* **Alternatives Considered**:
  * *Short-lived Tokens Only*: Relying purely on a short JWT expiration (e.g., 5 minutes) without blocklisting. Rejected because it does not meet the 1-second cluster-wide revocation constraint.
  * *Stateful Database Checks*: Checking the PostgreSQL database on every request to see if the session is revoked. Rejected due to the high database read overhead.

## 5. Role-Based Access Control (RBAC) Architecture

* **Decision**: Static, Enum-Based Roles.
* **Rationale**: Storing roles as a static Postgres Enum type (`owner`, `admin`, `member`, `viewer`) on the `users` table is sufficient for Phase 1. Access control is enforced using FastAPI dependencies and decorators mapped directly to these roles in code. This provides robust security with minimal database schema overhead.
* **Alternatives Considered**:
  * *Dynamic DB-Driven RBAC*: Creating separate tables for roles, permissions, and mappings. Rejected because Phase 1 has a fixed set of business roles and permissions, making dynamic schema overhead unnecessary.

## 6. Row-Level Security (RLS) Implementation

* **Decision**: PostgreSQL Native Row-Level Security.
* **Rationale**: PostgreSQL 16 native RLS policies ensure that data boundaries are strictly enforced. The FastAPI `TenantMiddleware` extracts the tenant context and runs `SET LOCAL app.current_tenant_id = '<uuid>'` inside the database transaction session. Postgres RLS policies check this local variable against the `tenant_id` column of each row. This mathematical guarantee prevents accidental cross-tenant data leaks.
* **Alternatives Considered**:
  * *Application-Level Filtering*: Adding `WHERE tenant_id = :tenant_id` to all SQLAlchemy queries manually. Rejected because it is highly error-prone and insecure; any developer oversight could lead to data leakage.
