# Data Model: Assistant & Knowledge Base

**Branch**: `003-assistant-knowledge-base` | **Date**: 2026-06-06

---

## 1. Entity Overview

```
tenants
  └──< assistants           (tenant_id FK + RLS)
         └──< documents     (tenant_id FK + RLS, assistant_id FK CASCADE)
               └── [ChromaDB chunks stored in tenant_{uuid} collection]
```

---

## 2. Assistant Entity

**Table**: `assistants` (already exists — Phase 1 Auth confirmed the model is in place)

**Model file**: `backend/app/models/assistant.py`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `tenant_id` | `UUID` | NOT NULL, FK → `tenants.id` ON DELETE CASCADE | Injected by `TenantMixin`; RLS enforced |
| `name` | `VARCHAR(255)` | NOT NULL | |
| `system_prompt` | `TEXT` | NOT NULL, default `''` | |
| `model` | `VARCHAR(100)` | NOT NULL, default `'gpt-4o-mini'` | |
| `temperature` | `FLOAT` | NOT NULL, default `0.7` | Valid range: 0.0–2.0 |
| `max_tokens` | `INTEGER` | NOT NULL, default `1024` | Valid range: 1–8192 |
| `is_active` | `BOOLEAN` | NOT NULL, default `TRUE` | |
| `widget_config` | `JSONB` | NOT NULL, default `{}` | Phase 5 use |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

**Changes needed (Alembic migration required)**:
- Add `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` column — needed to surface "last modified" in FR-004 list view.

**Indexes** (existing):
- PK on `id`
- `idx_assistants_tenant` on `(tenant_id)` — to be added in migration

**RLS policy** (existing, from Phase 1):
```sql
ALTER TABLE assistants ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON assistants
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**State machine**: `is_active` flag — no formal state transitions. Assistants are either active or inactive (soft-deleted is out of scope; hard delete is the Phase 2 behavior).

**Deletion guard** (FR-018): Before deleting an assistant, the API MUST check `COUNT(*) FROM conversations WHERE assistant_id = {id} AND status = 'active'`. If count > 0, return HTTP 409 with message `"This assistant has {N} active conversations. Resolve or end them before deleting."`.

---

## 3. Document Entity

**Table**: `documents` (already exists — model partially implemented)

**Model file**: `backend/app/models/document.py`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `tenant_id` | `UUID` | NOT NULL, FK → `tenants.id` ON DELETE CASCADE | Injected by `TenantMixin`; RLS enforced |
| `assistant_id` | `UUID` | NOT NULL, FK → `assistants.id` **ON DELETE CASCADE** | ⚠️ Change from `SET NULL` → `CASCADE` |
| `filename` | `VARCHAR(512)` | NOT NULL | Filename for files; normalized URL string for URL-type docs |
| `storage_key` | `VARCHAR(1024)` | NOT NULL | MinIO object key: `tenant/{tenant_id}/docs/{document_id}/{filename}` |
| `file_type` | `VARCHAR(50)` | NOT NULL | Enum: `pdf`, `docx`, `txt`, `url` |
| `status` | `VARCHAR(50)` | NOT NULL, default `'pending'` | State machine (see below) |
| `chunk_count` | `INTEGER` | nullable | Set to count of ChromaDB chunks on success |
| `error_message` | `TEXT` | nullable | Populated on `status = 'failed'` |
| `doc_metadata` | `JSONB` (col: `metadata`) | NOT NULL, default `{}` | Ingestion metadata; retry count tracked here |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

**Changes needed (Alembic migration required)**:
1. **FK change**: `assistant_id` ON DELETE `SET NULL` → `CASCADE` (assistant deletion must cascade)
2. **Unique constraint**: `UNIQUE (assistant_id, filename)` — enforces FR-017 (no duplicate filenames per assistant)
3. **NOT NULL on assistant_id**: Change `nullable=True` → `nullable=False` (Phase 2 documents always belong to an assistant)

**Indexes** (existing + additions):
- `idx_documents_tenant_status` on `(tenant_id, status)` — existing
- Add: `idx_documents_assistant` on `(assistant_id)` — for efficient assistant → documents listing

**Status State Machine**:

```
[Upload/URL submitted]
        │
        ▼
    pending  ──► [Celery task picked up]
        │
        ▼
   processing ──► [Text extracted + chunked + embedded + ChromaDB upserted]
        │                               │
        ▼                               ▼
      ready                           failed
                                  (after 4 attempts)
```

| Status | Meaning | UI display |
|---|---|---|
| `pending` | Task queued, not yet started | Spinner / "Queued" badge |
| `processing` | Task actively running | Animated progress badge |
| `ready` | Ingestion complete, searchable | Green "Ready" badge |
| `failed` | All retries exhausted | Red "Failed" badge + error message |

**RLS policy** (to add in migration):
```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

## 4. Knowledge Index (ChromaDB — no PostgreSQL table)

ChromaDB is not represented as a PostgreSQL entity. It is an external vector store accessed via the ChromaDB HTTP client.

| Concept | Value |
|---|---|
| Collection naming | `tenant_{tenant_uuid}` — one collection per tenant (constitution mandate) |
| Chunk document ID | `{document_id}_{chunk_index}` — stable, idempotent, upsert-safe |
| Chunk metadata | `{tenant_id, document_id, filename, file_type, chunk_index}` |
| n_results per query | 5 (plan.md default) |
| Deletion | On document delete: filter by `document_id` metadata and delete all matching vectors |

**Chunk deletion strategy**: ChromaDB `collection.delete(where={"document_id": str(document_id)})` — removes all chunks for a document without needing to enumerate IDs. The collection itself is only dropped on full tenant offboarding.

---

## 5. Pydantic Schema Contracts (Backend)

### AssistantCreate
```python
class AssistantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    system_prompt: str = Field(default="")
    model: str = Field(default="gpt-4o-mini", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
```

### AssistantUpdate
```python
class AssistantUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    system_prompt: str | None = None
    model: str | None = Field(None, max_length=100)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=8192)
    is_active: bool | None = None
```

### AssistantResponse
```python
class AssistantResponse(BaseModel):
    id: UUID
    name: str
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    is_active: bool
    widget_config: dict
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### DocumentResponse
```python
class DocumentResponse(BaseModel):
    id: UUID
    assistant_id: UUID
    filename: str
    file_type: str
    status: str
    chunk_count: int | None
    error_message: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### DocumentStatusResponse
```python
class DocumentStatusResponse(BaseModel):
    id: UUID
    status: str
    chunk_count: int | None
    error_message: str | None
```

### URLIngestRequest
```python
class URLIngestRequest(BaseModel):
    url: HttpUrl
    assistant_id: UUID
```

---

## 6. Plan-Based Quota Limits (FR-016)

Limits are enforced at the API layer by querying current counts before creation:

| Plan | Max Assistants | Max Documents |
|---|---|---|
| `starter` | 1 | 5 |
| `pro` | 5 | 100 |
| `business` | unlimited | unlimited |
| `enterprise` | unlimited | unlimited |

These limits are defined as constants in a new `app/core/quotas.py` module and checked in the assistant and document creation endpoints.

---

## 7. MinIO Object Key Convention

All uploaded files are stored under a deterministic key scheme:

```
tenant/{tenant_id}/docs/{document_id}/{filename}
```

- **Example**: `tenant/abc-123/docs/def-456/product-manual.pdf`
- Bucket name: `platform-documents` (single bucket, tenant-isolated by key prefix)
- Enforces tenant isolation at the object store level in addition to DB-level RLS
