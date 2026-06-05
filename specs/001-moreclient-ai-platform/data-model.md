# Data Model Specification: MoreClient AI Enterprise Platform

This document describes the schema, relationships, and constraints for all entities in the MoreClient AI platform, with Postgres Row Level Security (RLS) policies.

## 1. Relational Database Schema (PostgreSQL)

### Tenant Table
Represents an isolated customer organization.
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    region VARCHAR(20) NOT NULL, -- 'GCC' or 'GLOBAL'
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'suspended', 'cancelled'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### Workspace Table
Configuration container for a tenant.
```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_info JSONB, -- name, website, country, timezone
    branding JSONB, -- logo_url, primary_color, secondary_color, favicon_url
    timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
    country VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- RLS Policy:
-- CREATE POLICY tenant_isolation ON workspaces FOR ALL TO application_user 
-- USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Assistant Table
Configurations for the AI Assistant widget.
```sql
CREATE TABLE assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(512),
    personality VARCHAR(50) NOT NULL DEFAULT 'professional', -- 'friendly', 'professional', 'formal', 'sales', 'technical'
    language_mode VARCHAR(20) NOT NULL DEFAULT 'bilingual', -- 'arabic', 'english', 'bilingual'
    guardrails JSONB NOT NULL DEFAULT '{}'::jsonb, -- restrict_external, competitor_blocking, escalation_threshold
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Indexes:
CREATE INDEX idx_assistants_tenant ON assistants(tenant_id);
```

### KnowledgeSource Table
Stores files, URLs, or manual QA entries.
```sql
CREATE TABLE knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'document', 'url', 'qa'
    status VARCHAR(50) NOT NULL DEFAULT 'processing', -- 'processing', 'ready', 'failed'
    file_metadata JSONB, -- original_filename, size, file_type, s3_key, version
    content_hash VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX idx_knowledge_sources_tenant ON knowledge_sources(tenant_id);
```

### KnowledgeVersion Table
For knowledge base versioning and rollback.
```sql
CREATE TABLE knowledge_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    version_number VARCHAR(50) NOT NULL, -- e.g., 'v1.0'
    change_log TEXT,
    is_active BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX idx_knowledge_versions_tenant ON knowledge_versions(tenant_id);
```

### Conversation Table
A customer support thread.
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    customer_id VARCHAR(100) NOT NULL, -- session id or user identifier
    channel VARCHAR(50) NOT NULL DEFAULT 'web', -- 'web', 'whatsapp', 'email'
    status VARCHAR(50) NOT NULL DEFAULT 'ai', -- 'ai', 'escalated', 'agent', 'resolved'
    intent VARCHAR(100),
    sentiment_score INTEGER, -- 0-100 score
    urgency VARCHAR(20) DEFAULT 'low' NOT NULL, -- 'low', 'medium', 'high', 'critical'
    assigned_agent_id UUID, -- References human_agents(id)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX idx_conversations_status ON conversations(status);
```

### Message Table
Single messages inside a conversation.
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'agent'
    content TEXT NOT NULL,
    confidence_score NUMERIC(5, 4), -- NULL for user/agent messages
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
```

### Lead Table
A sales lead created by AI purchase intent detection.
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    estimated_value NUMERIC(12, 2),
    pipeline_stage VARCHAR(50) NOT NULL DEFAULT 'new', -- 'new', 'contacted', 'qualified', 'proposal', 'won', 'lost'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX idx_leads_tenant ON leads(tenant_id);
```

### HumanAgent Table
Support operators.
```sql
CREATE TABLE human_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    skills VARCHAR(50)[] DEFAULT '{}'::varchar[] NOT NULL,
    availability_status VARCHAR(50) NOT NULL DEFAULT 'offline', -- 'online', 'busy', 'offline'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX idx_agents_email ON human_agents(email);
CREATE INDEX idx_agents_tenant ON human_agents(tenant_id);
```

### Subscription Table
Stripe subscription details.
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly', -- 'monthly', 'annual'
    limits JSONB NOT NULL, -- message_limit, token_limit, storage_limit
    current_usage JSONB NOT NULL, -- messages_sent, tokens_used, storage_bytes
    stripe_subscription_id VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

### AuditLog Table
Immutable audit logs.
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL,
    actor_role VARCHAR(50) NOT NULL, -- 'super_admin', 'tenant_admin', 'agent'
    action_type VARCHAR(100) NOT NULL, -- 'login', 'upload', 'billing', 'delete'
    resource VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Prevent updates and deletes via trigger
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be updated or deleted.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
```

---

## 2. Row Level Security (RLS) Policy Pattern

To enforce multi-tenant isolation, every table (except `tenants` itself) must have RLS enabled. The database session must configure `app.current_tenant_id` on each transaction.

### Example configuration:
```sql
-- Enable Row Level Security
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Apply Tenant Isolation Policy
CREATE POLICY tenant_isolation_policy ON workspaces
    FOR ALL TO application_user
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- (Repeat for other tables)
```

In the FastAPI SQLAlchemy database adapter, we set this variable on checkout:
```python
@event.listens_for(Engine, "connect")
def set_tenant_id_in_session(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Execute setting inside current session connection
    cursor.execute("SET app.current_tenant_id TO %s;", (current_tenant_context.get(),))
    cursor.close()
```

---

## 3. Vector Database Schema (Qdrant)

Qdrant utilizes partitioned collections to segregate client vectors securely.

### Collection configuration:
- **Collection Name**: `moreclient_vectors_<region>` (e.g. `moreclient_vectors_gcc` or `moreclient_vectors_global`).
- **Vector Dimensions**: `1536` (standard for OpenAI `text-embedding-3-small` / text-embedding-ada-002 models).
- **Metric**: `Cosine`
- **Payload Schema**:
```json
{
  "tenant_id": "uuid",
  "source_id": "uuid",
  "document_version": "string",
  "text": "The raw text chunk extracted from document",
  "metadata": {
    "filename": "string",
    "page_number": 12
  }
}
```

### Search Filtering:
Every vector retrieval query must include a strict payload filter for the `tenant_id` payload attribute:
```json
{
  "filter": {
    "must": [
      {
        "key": "tenant_id",
        "match": {
          "value": "7a3b-4889..."
        }
      }
    ]
  }
}
```
This query ensures that even if vectors are stored in a shared collection, the vector search engine will strictly query matches belonging to the designated tenant.
