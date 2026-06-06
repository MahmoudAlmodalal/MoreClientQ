# Data Model: Initial Database Schema (Phase 0)

This document defines the database tables, fields, constraints, and relationships that will be initialized via Alembic migrations in Phase 0. 

In accordance with the **Platform Constitution**, all tenant-specific tables carry a mandatory `tenant_id` column to support Row-Level Security (RLS) isolation.

---

## 1. Relational Database Schema (PostgreSQL)

### 1.1 Tenants Table
Stores organization-level tenant records.
- **Table Name**: `tenants`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `slug`: `VARCHAR(63)` (Unique, Indexed, non-null) — Subdomain identifier.
  - `name`: `VARCHAR(255)` (non-null)
  - `plan`: `VARCHAR(50)` (non-null, default: `'starter'`)
  - `is_active`: `BOOLEAN` (non-null, default: `true`)
  - `settings`: `JSONB` (non-null, default: `'{}'`)
  - `monthly_quota`: `INT` (non-null, default: `1000`)
  - `used_quota`: `INT` (non-null, default: `0`)
  - `created_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
  - `updated_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)

---

### 1.2 Users Table
Stores tenant users/members.
- **Table Name**: `users`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `email`: `VARCHAR(255)` (non-null)
  - `hashed_password`: `VARCHAR(255)` (nullable for OAuth users)
  - `full_name`: `VARCHAR(255)` (nullable)
  - `role`: `VARCHAR(50)` (non-null, default: `'member'`) — owner, admin, member, viewer.
  - `is_active`: `BOOLEAN` (non-null, default: `true`)
  - `last_login`: `TIMESTAMPTZ` (nullable)
  - `created_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
- **Constraints**:
  - Unique constraint on `(tenant_id, email)`
- **Indexes**:
  - Index on `tenant_id`

---

### 1.3 Assistants Table
Stores bot configuration profiles.
- **Table Name**: `assistants`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `name`: `VARCHAR(255)` (non-null)
  - `system_prompt`: `TEXT` (non-null, default: `''`)
  - `model`: `VARCHAR(100)` (non-null, default: `'gpt-4o-mini'`)
  - `temperature`: `FLOAT` (non-null, default: `0.7`)
  - `max_tokens`: `INT` (non-null, default: `1024`)
  - `is_active`: `BOOLEAN` (non-null, default: `true`)
  - `widget_config`: `JSONB` (non-null, default: `'{}'`)
  - `created_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
- **Indexes**:
  - Index on `tenant_id`

---

### 1.4 Documents Table
Stores records of uploaded knowledge files.
- **Table Name**: `documents`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `assistant_id`: `UUID` (Foreign Key -> `assistants(id)` on delete set null, nullable)
  - `filename`: `VARCHAR(512)` (non-null)
  - `storage_key`: `VARCHAR(1024)` (non-null)
  - `file_type`: `VARCHAR(50)` (non-null)
  - `status`: `VARCHAR(50)` (non-null, default: `'pending'`) — pending, processing, ready, failed.
  - `chunk_count`: `INT` (nullable)
  - `error_message`: `TEXT` (nullable)
  - `metadata`: `JSONB` (non-null, default: `'{}'`)
  - `created_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
- **Indexes**:
  - Index on `(tenant_id, status)`

---

### 1.5 Conversations Table
Stores visitor-to-bot chat threads.
- **Table Name**: `conversations`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `assistant_id`: `UUID` (Foreign Key -> `assistants(id)` on delete cascade, non-null)
  - `session_token`: `VARCHAR(255)` (Unique, non-null)
  - `visitor_name`: `VARCHAR(255)` (nullable)
  - `visitor_email`: `VARCHAR(255)` (nullable)
  - `status`: `VARCHAR(50)` (non-null, default: `'active'`) — active, resolved, handed_off.
  - `channel`: `VARCHAR(50)` (non-null, default: `'web'`)
  - `metadata`: `JSONB` (non-null, default: `'{}'`)
  - `started_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
  - `ended_at`: `TIMESTAMPTZ` (nullable)
- **Indexes**:
  - Index on `tenant_id`
  - Index on `session_token`

---

### 1.6 Messages Table
Stores individual messages in a conversation.
- **Table Name**: `messages`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `conversation_id`: `UUID` (Foreign Key -> `conversations(id)` on delete cascade, non-null)
  - `role`: `VARCHAR(20)` (non-null) — user, assistant, system.
  - `content`: `TEXT` (non-null)
  - `tokens_used`: `INT` (nullable, default: `0`)
  - `latency_ms`: `INT` (nullable)
  - `sources`: `JSONB` (nullable, default: `'[]'`)
  - `created_at`: `TIMESTAMPTZ` (non-null, default: `NOW()`)
- **Indexes**:
  - Index on `conversation_id`
  - Index on `(tenant_id, created_at DESC)`

---

### 1.7 Quota Logs Table
Stores hourly rollup usage counts.
- **Table Name**: `quota_logs`
- **Columns**:
  - `id`: `UUID` (Primary Key, default: `gen_random_uuid()`)
  - `tenant_id`: `UUID` (Foreign Key -> `tenants(id)` on delete cascade, non-null)
  - `period`: `TIMESTAMPTZ` (non-null) — Truncated to the hour.
  - `message_count`: `INT` (non-null, default: `0`)
  - `token_count`: `INT` (non-null, default: `0`)

---

## 2. Row-Level Security (RLS) Strategy

Row-Level Security must be enabled on every table listed above (except `tenants`). The default RLS policy is:
```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON <table>
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```
All database queries run within transactional contexts where the connection pool issues a `SET LOCAL app.current_tenant_id = '<uuid>'` statement.
