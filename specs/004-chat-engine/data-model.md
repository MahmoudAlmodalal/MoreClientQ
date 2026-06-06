# Data Model: Chat Engine

**Branch**: `004-chat-engine` | **Date**: 2026-06-06

---

## Entities

### Conversation

Represents a single chat thread between a visitor/user and an assistant within a tenant.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | |
| `tenant_id` | UUID | NOT NULL, FK → tenants.id | RLS column — set by `TenantMixin` |
| `assistant_id` | UUID | NOT NULL, FK → assistants.id, ON DELETE CASCADE | |
| `session_token` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | Identifies anonymous widget sessions |
| `visitor_name` | VARCHAR(255) | nullable | |
| `visitor_email` | VARCHAR(255) | nullable | |
| `title` | VARCHAR(255) | nullable | **NEW** — auto-generated from first message |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT `'bot'`, CHECK (`bot`, `handoff`, `closed`) | **MODIFIED** — was `active` |
| `channel` | VARCHAR(50) | NOT NULL, DEFAULT `'web'` | e.g., `web`, `widget`, `api` |
| `conv_metadata` | JSONB | NOT NULL, DEFAULT `{}` | Maps to DB column `metadata` |
| `started_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | |
| `ended_at` | TIMESTAMPTZ | nullable | |

**Indexes**:
- `idx_conversations_tenant` on `(tenant_id)`
- `idx_conversations_status` on `(tenant_id, status)` — **NEW**

**RLS Policy** (already inherited from prior migration or added in this migration):
```sql
CREATE POLICY tenant_isolation ON conversations
  FOR ALL
  USING (tenant_id::text = current_setting('app.current_tenant_id'));
```

**State Transitions**:
```
bot ──[keyword match]──► handoff
bot ──[user ends]──────► closed
handoff ──[agent closes]──► closed
```

---

### Message

Represents a single message within a conversation.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | |
| `tenant_id` | UUID | NOT NULL | RLS column |
| `conversation_id` | UUID | NOT NULL, FK → conversations.id, ON DELETE CASCADE | |
| `role` | VARCHAR(20) | NOT NULL, CHECK (`user`, `assistant`, `system`) | |
| `content` | TEXT | NOT NULL | Partial responses marked with `[response truncated]` |
| `tokens_used` | INTEGER | nullable, DEFAULT 0 | Sum of prompt + completion tokens |
| `latency_ms` | INTEGER | nullable | End-to-end response latency |
| `sources` | JSONB | nullable, DEFAULT `[]` | Array of retrieved chunk references for grounding |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | |

**Indexes**:
- `idx_messages_conversation` on `(conversation_id)`
- `idx_messages_tenant_created` on `(tenant_id, created_at DESC)`

**RLS Policy**:
```sql
CREATE POLICY tenant_isolation ON messages
  FOR ALL
  USING (tenant_id::text = current_setting('app.current_tenant_id'));
```

---

### QuotaLog

Tracks per-tenant token consumption for hourly rollups and billing.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, `gen_random_uuid()` | |
| `tenant_id` | UUID | NOT NULL | RLS column |
| `tokens_consumed` | INTEGER | NOT NULL | |
| `action_type` | VARCHAR(50) | NOT NULL | e.g., `chat_completion`, `embedding` |
| `conversation_id` | UUID | nullable | Reference for audit trail |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT `now()` | |

**Indexes**:
- `idx_quota_logs_tenant_hour` on `(tenant_id, created_at)` — supports hourly rollup queries

---

## Redis Data Structures

### Token Quota Bucket

```
Key:   quota:{tenant_id}:{YYYYMMDDHH}
Type:  STRING (integer counter)
TTL:   2 hours (rolling; reset on each INCRBY)
Value: running sum of tokens consumed in this hour
```

### Rate Limit Bucket

```
Key:   rate:{tenant_id}
Type:  STRING (integer counter, or sorted set for sliding window)
TTL:   60 seconds
Value: request count in the current window
```

### Handoff Pub/Sub Channel

```
Channel: handoff:{tenant_id}
Payload: {
  "conversation_id": "<uuid>",
  "event": "handoff_requested",
  "assistant_id": "<uuid>",
  "ts": "<ISO-8601 UTC timestamp>"
}
```

---

## Alembic Migration: `xxxx_add_chat_engine_schema.py`

Changes required:

1. **`conversations` table**:
   - Add column `title VARCHAR(255) NULL`
   - Alter `status` column: change default to `'bot'` and add `CHECK (status IN ('bot', 'handoff', 'closed'))`
   - Add index `idx_conversations_status` on `(tenant_id, status)`

2. **RLS**:
   - `ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;`
   - `ALTER TABLE messages ENABLE ROW LEVEL SECURITY;`
   - Create `tenant_isolation` policy on both tables (if not already present)

3. **No new tables** — `messages` and `quota_logs` already exist in prior migrations.

---

## Validation Rules

| Entity | Field | Rule |
|---|---|---|
| Conversation | `status` | Must be one of `bot`, `handoff`, `closed` |
| Conversation | `assistant_id` | Must reference an assistant owned by the same `tenant_id` |
| Message | `role` | Must be one of `user`, `assistant`, `system` |
| Message | `content` | Must not be empty |
| Message | `tokens_used` | Must be ≥ 0 |
| QuotaLog | `tokens_consumed` | Must be > 0 |
