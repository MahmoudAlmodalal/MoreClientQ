# Data Model Specification: Auth & Tenancy

This document specifies the database schemas, entity definitions, constraints, and Row-Level Security (RLS) configurations.

## 1. Entity Diagrams & Schema Definitions

The storage layer utilizes **PostgreSQL 16**.

### 1.1 Tenant Entity (`tenants`)
Represents the top-level SaaS tenant (workspace/company boundary).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, Default: `gen_random_uuid()` | Unique tenant identifier |
| `slug` | VARCHAR(63) | UNIQUE, NOT NULL | Tenant subdomain slug (lowercase, alphanumeric, max 63 chars) |
| `name` | VARCHAR(255) | NOT NULL | Customer/Company name |
| `plan` | VARCHAR(50) | NOT NULL, Default: `'free'` | Subscription tier (free, growth, enterprise) |
| `is_active` | BOOLEAN | NOT NULL, Default: `true` | Administrative status |
| `settings` | JSONB | NOT NULL, Default: `'{}'` | Custom workspace settings and config |
| `created_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Audit timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Audit timestamp |

* **Indices**:
  * `idx_tenants_slug` ON `tenants(slug)` (Hash/B-tree for fast subdomain lookups)

### 1.2 User Entity (`users`)
Represents user accounts within a tenant.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, Default: `gen_random_uuid()` | Unique user identifier |
| `tenant_id` | UUID | FOREIGN KEY -> `tenants(id)` ON DELETE CASCADE, NOT NULL | Associated tenant context |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address (globally unique) |
| `hashed_password` | VARCHAR(255) | NOT NULL | Secure salted password hash (Argon2id/Bcrypt) |
| `role` | VARCHAR(50) | NOT NULL | Static enum: `owner`, `admin`, `member`, `viewer` |
| `is_active` | BOOLEAN | NOT NULL, Default: `true` | Active state of the user |
| `created_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Audit timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Audit timestamp |

* **Indices**:
  * `idx_users_email` ON `users(email)` (Unique b-tree)
  * `idx_users_tenant` ON `users(tenant_id)` (B-tree foreign key index)

### 1.3 Invitation Entity (`invitations`)
Handles invite-driven team additions.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, Default: `gen_random_uuid()` | Unique identifier |
| `tenant_id` | UUID | FOREIGN KEY -> `tenants(id)` ON DELETE CASCADE, NOT NULL | Originating tenant |
| `email` | VARCHAR(255) | NOT NULL | Invited user email |
| `role` | VARCHAR(50) | NOT NULL | Target role: `admin`, `member`, `viewer` |
| `token` | VARCHAR(255) | UNIQUE, NOT NULL | Cryptographically secure token |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Token expiration date |
| `accepted_at` | TIMESTAMPTZ | NULLABLE | When the user accepted the invite |
| `created_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Creation audit timestamp |

* **Indices**:
  * `idx_invitations_token` ON `invitations(token)` (Unique hash/b-tree)
  * `idx_invitations_tenant_email` ON `invitations(tenant_id, email)` (Prevent duplicate active invites)

### 1.4 QuotaLog Entity (`quota_logs`)
Tracks resource usage logs (e.g. LLM tokens, messages) per tenant.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, Default: `gen_random_uuid()` | Unique identifier |
| `tenant_id` | UUID | FOREIGN KEY -> `tenants(id)` ON DELETE CASCADE, NOT NULL | Associated tenant |
| `resource` | VARCHAR(50) | NOT NULL | Target resource type (e.g. `llm_tokens`, `messages`) |
| `amount` | INTEGER | NOT NULL | Amount consumed (can be negative for refunds) |
| `created_at` | TIMESTAMPTZ | NOT NULL, Default: `NOW()` | Creation timestamp |

* **Indices**:
  * `idx_quota_logs_tenant_created` ON `quota_logs(tenant_id, created_at DESC)` (Composite b-tree for fast usage rollup)

---

## 2. Row-Level Security (RLS) Policies

Every tenant-specific table (`users`, `invitations`, `quota_logs`) MUST have Postgres Row-Level Security enabled. The RLS policies prevent a session bound to one tenant from querying or updating rows belonging to another.

### 2.1 Database Tenant Session Setting
Middleware sets a local transaction-scoped parameter prior to execution:
```sql
SET LOCAL app.current_tenant_id = '<uuid>';
```

### 2.2 RLS Setup Scripts
```sql
-- Enable RLS on tables
ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

ALTER TABLE invitations FORCE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;

ALTER TABLE quota_logs FORCE ROW LEVEL SECURITY;
ALTER TABLE quota_logs ENABLE ROW LEVEL SECURITY;

-- Define RLS Policies
CREATE POLICY user_tenant_isolation_policy ON users
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY invitation_tenant_isolation_policy ON invitations
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY quota_logs_tenant_isolation_policy ON quota_logs
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```
*(Note: Using `current_setting('app.current_tenant_id', true)` with the optional `missing_ok` flag set to true prevents syntax errors when the setting is missing, returning NULL instead.)*
