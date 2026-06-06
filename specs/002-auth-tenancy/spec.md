# Feature Specification: Auth & Tenancy

**Feature Branch**: `002-auth-tenancy`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "specify for Phase 1 — Auth & Tenancy (Week 2) only in plan.md"

## Clarifications

### Session 2026-06-06

- Q: How should the system enforce user email uniqueness across different tenants? → A: Global Uniqueness: An email address can only be registered once across the entire platform.
- Q: How should the user invitation flow be handled in Phase 1 (without SMTP configured)? → A: Simulated Email: Generate an invitation token and return the URL in the API response or log it in the console for local development.
- Q: What is the scope of Tenant Offboarding (Data Purge) for Phase 1? → A: Deferred/Partial Purge: Implement PostgreSQL cascade delete and JWT blocklisting in Phase 1; defer ChromaDB and MinIO purges to future phases.
- Q: How should token revocation (instant logout / deactivation) be implemented for stateless JWTs? → A: Redis Blocklist: Store revoked token identifiers (jti) in Redis. The FastAPI auth middleware checks the blocklist on every authenticated request.
- Q: Should RBAC roles and permissions be static (hardcoded) or dynamic (database-driven) in Phase 1? → A: Static Roles: Hardcode roles and their specific permissions in code (decorators/middleware) using a simple Enum database type on the User table.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tenant Registration and First User (Owner) Setup (Priority: P1)

As a new SaaS customer (tenant owner), I want to register my company/tenant and create my own owner user account in a single step, so that I can log in and start configuring my AI assistant platform workspace.

**Why this priority**: It is the entry point for all tenants and users. Without registration, we cannot have tenants or users.

**Independent Test**: Can be tested by sending a POST request to `/api/v1/auth/register` with tenant slug, name, and owner user details, and verifying the tenant and user records are created in the database and the slug is unique.

**Acceptance Scenarios**:

1. **Given** a unique tenant slug (e.g. `acme`), **When** I POST to `/api/v1/auth/register` with name `"Acme Corp"`, email `"owner@acme.com"`, and a secure password, **Then** a new tenant record is created in the `tenants` table with `slug='acme'` and a new user is created in the `users` table with `role='owner'`.
2. **Given** an existing tenant with slug `acme`, **When** I POST to `/api/v1/auth/register` with the same slug `acme`, **Then** the system rejects the request with HTTP 400 Bad Request indicating the slug is already taken.

---

### User Story 2 - Secure JWT Authentication and Token Lifecycle (Priority: P1)

As a registered tenant user, I want to authenticate securely with my email and password, receive a JSON Web Token (JWT) containing my identity, tenant association, and RBAC role, and refresh my session when the token expires, so that I can access protected API endpoints securely.

**Why this priority**: Core security mechanism for all API calls. Protects tenant data from unauthorized access.

**Independent Test**: Can be tested by posting credentials to `/api/v1/auth/login`, verifying that a valid JWT containing the claims (`sub`, `tenant_id`, `role`, etc.) is returned, and verifying that the refresh token endpoint can generate a new access token.

**Acceptance Scenarios**:

1. **Given** a registered user `owner@acme.com` with password `password123`, **When** I POST to `/api/v1/auth/login` with these credentials, **Then** the system returns a 200 OK with an access token (JWT) and a refresh token, and the JWT payload contains `tenant_id`, `tenant_slug`, and `role='owner'`.
2. **Given** a valid refresh token, **When** I POST to `/api/v1/auth/refresh`, **Then** the system returns a new access token.
3. **Given** an invalid or expired JWT, **When** I make a request to a protected endpoint, **Then** the system rejects the request with HTTP 401 Unauthorized.

---

### User Story 3 - Subdomain-Based Tenant Resolution (Priority: P1)

As a visitor or user navigating to a custom tenant URL (e.g. `http://acme.platform.com`), I want the platform to automatically resolve the subdomain to the correct tenant context and forward the validated tenant identity to the backend, so that my request is routed to my isolated tenant workspace.

**Why this priority**: Ensures seamless, brand-customized entry points for each tenant and forms the basis for frontend multi-tenancy.

**Independent Test**: Can be tested by making a request to the Next.js frontend on a specific subdomain (e.g. `acme.localhost`), verifying that the middleware resolves the tenant ID and slug, and verifies it with the backend database/cache.

**Acceptance Scenarios**:

1. **Given** a tenant with slug `acme` exists, **When** a request is made to `http://acme.platform.com/dashboard`, **Then** the Next.js middleware resolves the slug `acme` to its UUID, sets the `X-Tenant-ID` header, and passes the request.
2. **Given** no tenant exists with slug `invalid-slug`, **When** a request is made to `http://invalid-slug.platform.com/dashboard`, **Then** the middleware redirects the user to a 404 page.
3. **Given** a request to the main platform landing page `http://platform.com`, **When** processed by the middleware, **Then** it bypasses tenant resolution and loads the marketing pages successfully.

---

### User Story 4 - Row-Level Security (RLS) and Tenant Middleware (Priority: P1)

As a tenant, I want all database queries to be automatically constrained to my `tenant_id` at the database level using Row-Level Security (RLS), so that it is mathematically impossible for my users to see or modify data belonging to other tenants.

**Why this priority**: Non-negotiable security principle of the platform constitution. Prevents catastrophic cross-tenant data leaks.

**Independent Test**: Can be tested by logging in as a user from Tenant A, making a query that doesn't explicitly filter by tenant, and verifying that the database context (via TenantMiddleware and RLS) restricts the returned records only to Tenant A.

**Acceptance Scenarios**:

1. **Given** two tenants `Acme` (ID 1) and `Beta` (ID 2), **When** a request from `Acme` is processed, **Then** the FastAPI `TenantMiddleware` sets the session local variable `app.current_tenant_id = 1` and any SQL query on `users` or other tenant tables only returns rows where `tenant_id = 1`.
2. **Given** a backend request missing the `X-Tenant-ID` header to a protected route, **When** processed by the `TenantMiddleware`, **Then** the system aborts the request with HTTP 400 Bad Request ("Missing tenant context").

---

### User Story 5 - Role-Based Access Control (RBAC) Enforcement (Priority: P2)

As a tenant owner or administrator, I want to assign roles (`owner`, `admin`, `member`, `viewer`) to users and have the platform restrict API actions based on these roles, so that sensitive actions (like inviting users or updating billing) are restricted to authorized personnel.

**Why this priority**: Standard internal security for tenants. Prevents low-privilege users from performing administrative actions.

**Independent Test**: Can be tested by attempting to invite a user or delete a user using different roles, and verifying that only `owner` (and `admin` where applicable) can succeed, while `member` and `viewer` receive HTTP 403 Forbidden.

**Acceptance Scenarios**:

1. **Given** a logged-in user with role `member`, **When** they make a POST request to `/api/v1/users/invite`, **Then** the API rejects the request with HTTP 403 Forbidden.
2. **Given** a logged-in user with role `owner`, **When** they make a POST request to `/api/v1/users/invite` with a valid email, **Then** the system creates the user invite and returns HTTP 201 Created.

---

### User Story 6 - User Invites & Team Management (Priority: P2)

As a tenant administrator or owner, I want to invite team members by their email addresses and assign them roles, and list or remove members of my team, so that we can collaborate on building and monitoring our AI assistants.

**Why this priority**: Essential for team collaboration inside a tenant workspace.

**Independent Test**: Can be tested by using the team management endpoints to invite, list, and delete users under a tenant context.

**Acceptance Scenarios**:

1. **Given** a tenant owner is logged in, **When** they request `GET /api/v1/users`, **Then** the system returns a list of all users associated with their specific tenant.
2. **Given** a tenant user with ID `user-123` exists, **When** the tenant owner sends `DELETE /api/v1/users/user-123`, **Then** the user is deleted and cannot log in anymore.

---

### Edge Cases

- **Duplicate Subdomain Slug Registration**: Two different registration requests sent concurrently with the same slug. The database unique constraint on `tenants.slug` must fail the second request gracefully with a user-friendly error.
- **Tenant Deactivation**: If a tenant has `is_active=False`, any authentication or API access attempts by its users must be immediately rejected (e.g. HTTP 403 Forbidden - "Tenant is inactive").
- **Subdomain Middleware Caching & Sync**: Next.js middleware queries the backend via Redis cache. If a tenant is deactivated or deleted, the Redis cache must be invalidated immediately so that subsequent requests to that subdomain are rejected instantly rather than waiting for cache TTL.
- **Header Spoofing**: An attacker tries to send a direct request to the backend with a spoofed `X-Tenant-ID` header. The backend must verify that the `X-Tenant-ID` header matches the `tenant_id` claim in the signed JWT token. For internal service-to-service calls (like Next.js middleware verifying a slug), a secure `X-Internal-Secret` must be verified.
- **Tenant Offboarding & Data Purge (Phase 1)**: When a tenant is deleted or offboarded, the system MUST execute PostgreSQL cascade deletes (removing all tenant users, settings, and logs) and immediately revoke active JWTs by blocklisting them in Redis. The purging of external assets (e.g. ChromaDB collections, MinIO files) is deferred to later phases when those technologies are integrated.
- **Token Revocation (Instant Logout/Deactivation)**: When a user logs out or a tenant is deactivated, all associated JWTs (or specifically their `jti` identifiers) are added to a Redis blocklist with a TTL matching the token's lifetime. The FastAPI authentication middleware checks this blocklist on every request, ensuring instant revocation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Tenant Registration: The system MUST expose a public endpoint `POST /api/v1/auth/register` to register a new tenant with a unique slug and create the initial user with the role of `owner`.
- **FR-002**: Slug Uniqueness: Tenant slugs MUST be validated for format (alphanumeric, lowercase, max 63 characters) and uniqueness at both the API level and the database schema layer.
- **FR-003**: JWT Authentication: The system MUST authenticate users via username/password and return a JWT access token and a refresh token (`POST /api/v1/auth/login`).
- **FR-004**: JWT Claims: The generated JWT MUST include claims for `sub` (user ID), `tenant_id` (tenant UUID), `tenant_slug` (tenant subdomain key), and `role` (RBAC role).
- **FR-005**: Next.js Subdomain Middleware: The Next.js middleware MUST resolve the tenant slug from the hostname, validate it against the backend, and inject the resolved tenant ID into the `X-Tenant-ID` header.
- **FR-006**: FastAPI Tenant Middleware: The backend MUST run a `TenantMiddleware` that extracts `X-Tenant-ID` from headers, validates it against a Redis cache (or database fallback), and binds the tenant context to the current request state.
- **FR-007**: Database RLS Enforcement: PostgreSQL Row-Level Security policies MUST be enabled on the `users` table (and all other tenant tables) such that all queries are restricted to the tenant ID set via `SET LOCAL app.current_tenant_id` in the transaction context.
- **FR-008**: RBAC Routing: The backend MUST enforce static Role-Based Access Control (RBAC) with hardcoded role-to-permission mappings in FastAPI middleware/decorators, verifying the user's role (`owner`, `admin`, `member`, `viewer`) matches the required permissions:
  - `owner`: invite users, delete users, update roles, update tenant settings, read analytics.
  - `admin`: update tenant settings (excluding plan/delete), read analytics.
  - `member`: view users, read-only dashboard.
  - `viewer`: read-only dashboard.
- **FR-009**: User Invitation: The system MUST support inviting team members via `POST /api/v1/users/invite` by specifying an email and role. In Phase 1, since SMTP is not configured, the system MUST generate an invitation token and return the invitation link in the API response (and/or log it to the console) to simulate email sending.
- **FR-010**: User Management: The system MUST provide endpoints to list team members (`GET /api/v1/users`), update roles (`PATCH /api/v1/users/{id}`), and delete team members (`DELETE /api/v1/users/{id}`).

### Key Entities *(include if feature involves data)*

- **Tenant**: Represents a company or SaaS client. Key attributes include: `id` (UUID), `slug` (subdomain string), `name`, `plan` (pricing tier), `is_active` (boolean status), and `settings` (JSONB configuration).
- **User**: Represents a team member within a tenant. Key attributes include: `id` (UUID), `tenant_id` (UUID foreign key referencing Tenant), `email` (globally unique string), `hashed_password`, `role` (static enum: owner|admin|member|viewer), and `is_active` (boolean status).
- **Auth Session**: Represents a valid authenticated state, encapsulated in a signed JWT access token and an associated refresh token.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tenant Resolution Latency: Next.js middleware resolves and validates tenant slugs via Redis in under 15ms per request.
- **SC-002**: Verification of Security Boundary: 100% of queries to tenant-specific database tables fail if the tenant context is not set, and return exactly 0 records for other tenants.
- **SC-003**: JWT Verification Overhead: The cryptographic validation and extraction of tenant context from the JWT on the backend adds less than 5ms of response latency.
- **SC-004**: Token Expiration & Revocation: Revoking a session (via logout or blocklist) takes effect cluster-wide within 1 second.

## Assumptions

- **Subdomain-only local dev resolution**: We assume local development will use subdomains like `acme.localhost` which route correctly to the Next.js development server.
- **Redis Cache Availability**: We assume Redis is available and configured as a cache for fast tenant slug resolution and JWT blocklist validation.
- **Owner Role Assignment**: We assume that the user registering the tenant is automatically assigned the `owner` role, and there can only be one active `owner` role per tenant or that the primary billing contact is this user.
