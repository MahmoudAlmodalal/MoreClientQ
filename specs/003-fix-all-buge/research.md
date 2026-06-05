# Research & Architecture Decisions: MoreClient AI Enterprise Platform

This document outlines the technical research, architectural decisions, and justifications for the key components of the MoreClient AI platform. Sections 1–7 carry forward the decisions established in `001-moreclient-ai-platform/research.md`. Section 8 is new, reflecting the `003` spec clarification on RAG context compression.

## 1. Database Multi-Tenant Isolation & RLS

### Decision
Implement **PostgreSQL Row Level Security (RLS)** in a single shared database instance, utilizing tenant ID scopes on all tenant-facing tables.

### Rationale
- **Security**: RLS enforces security at the database engine level. Even if application code has a bug where it fails to include a `WHERE tenant_id = :tenant_id` clause, the database will refuse to return or update rows from other tenants.
- **Maintenance**: Schema migrations are simplified since there is only one database schema to manage, rather than spinning up separate schemas or databases per tenant.
- **Resource Efficiency**: A single database instance optimizes connection pooling and memory consumption.

### Alternatives Considered
- *Database-per-tenant*: Rejected due to high overhead, complexity of running migrations across thousands of databases, and increased cost.
- *Schema-per-tenant*: Rejected because connection pooling becomes complex and table/index caching at the Postgres level gets diluted as schema counts grow.

---

## 2. GCC Region & Data Residency Isolation

### Decision
Establish two independent deployment clusters (GCC region in Dubai/Bahrain and Global region in Frankfurt/Ireland). The frontend router routes users to the correct region based on their tenant configuration. Cross-region database replication is strictly disabled.

### Rationale
- Compliance with local data regulations (e.g., PDPL in Saudi Arabia, UAE data protection laws) requires that citizen data does not leave local servers.
- Complete network and data isolation ensures no leaking of sensitive PII or training data across regulatory borders.

### Alternatives Considered
- *Single multi-region Postgres cluster*: Rejected because data residency laws require strict physical storage isolation, preventing replication of GCC tenant data to servers outside the region.

---

## 3. Qdrant Vector DB Tenant Isolation

### Decision
Use **separate Qdrant collections** per tenant for large enterprise tiers, and **collection partitioning with payload filtering** (namespace metadata field `tenant_id`) for standard tiers.

### Rationale
- *Performance & Isolation*: Large enterprise tenants with massive knowledge documents benefit from their own collections, which prevents index dilution and improves vector search speed.
- *Cost efficiency*: For smaller tenants, creating separate collections carries a high memory overhead in Qdrant (since each collection maintains its own index). Using a single partitioned collection with a `tenant_id` payload filter is memory-efficient and secure when combined with client-side query validation.

### Alternatives Considered
- *Always separate collections*: Rejected because it would exceed system memory limits when scaling to 10,000+ tenants.

---

## 4. Hybrid Search and RAG Pipeline

### Decision
Implement a hybrid search retrieval system combining dense vector search (Qdrant `cosine` distance) and sparse keyword search (using PostgreSQL `tsvector` or BM25 index), combined via **Reciprocal Rank Fusion (RRF)**. Surface results to a **Cross-Encoder re-ranker** (e.g., `bge-reranker-large`) before sending to the LLM.

### Rationale
- Dense vectors capture semantic intent (e.g., matching "payment issues" to "billing error"), but often fail on exact matching (e.g., serial numbers, specific error codes like "ERR_404"). Hybrid search covers both semantic and lexical queries.
- Re-ranking ensures the most relevant context is placed at the top of the context window, reducing LLM hallucinations and staying within token budgets.

### Alternatives Considered
- *Dense-only vector search*: Rejected due to poor performance on keyword-heavy or code/ID searches.
- *No re-ranking*: Rejected because it increases prompt token size and yields lower accuracy answers.

---

## 5. Stripe Overage Billing & Message Metering

### Decision
Implement real-time usage tracking in Redis using atomic counters (`INCRBY`). Persist usage stats to PostgreSQL hourly. Use Stripe's **Metered Billing (Usage-based pricing)** model, where the system reports consumption using the Stripe Usage Records API at the end of the billing period.

### Rationale
- Soft limit handling ensures end users do not get cut off mid-conversation during critical support sessions.
- Real-time Redis counters ensure rate limiting can be checked in under 5ms, while avoiding direct, blocking writes to PostgreSQL on every message.

### Alternatives Considered
- *Hard caps (hard blocking)*: Rejected based on business requirements to maximize tenant client retention.

---

## 6. Bilingual (Arabic/English) RTL Mirroring

### Decision
Use React Context to manage a global `dir` state ("rtl" or "ltr"). Dynamically apply standard HTML `dir` attribute to the document root element. Use logical CSS properties (e.g., `margin-inline-start`, `padding-inline-end`, `inset-inline-start`) instead of physical offsets (`margin-left`, etc.) to support seamless layout mirroring.

### Rationale
- RTL mirroring becomes automatic when using HTML `dir` attribute combined with logical CSS properties.
- Avoids writing dual style sheets (one for English, one for Arabic) and minimizes codebase maintenance overhead.

---

## 7. Virus Scanning File Uploads

### Decision
Integrate a lightweight **ClamAV daemon** (running as a sidecar container in Docker/K8s). The FastAPI backend streams uploaded files to ClamAV via TCP/socket before writing them to S3.

### Rationale
- Essential for enterprise security to prevent tenants from uploading malware or malicious files that could compromise internal processing pipelines or other tenants.
- Scanning in-stream prevents storing infected files on disk or S3.

### Alternatives Considered
- *After-the-fact S3 trigger scan*: Rejected because there is a delay between upload and detection, during which the processing pipeline could ingest the malware.

---

## 8. RAG Context Compression (0.75 Cosine Similarity Threshold)

### Decision
After the cross-encoder re-ranking step, apply a **hard cosine similarity filter**: any retrieved chunk with a cosine similarity score below **0.75** is discarded before context assembly. The LLM receives only chunks that pass this threshold.

### Rationale
- Low-similarity chunks pad the context window without adding value, increasing token costs and increasing the probability of hallucination or topic drift.
- The 0.75 threshold is specified by FR-015 and balances precision (high relevance only) against recall (not discarding genuinely helpful borderline matches). It can be tuned per-assistant in future phases.
- Pruning happens post-reranker, so high-scoring semantic matches from dense search that happen to have a lower cosine baseline are still protected by their cross-encoder score.

### Implementation Notes
- Implemented in `backend/src/services/search.py` in the `assemble_context()` function.
- The threshold value is configurable via `assistant.guardrails.context_similarity_threshold` (default: `0.75`).

### Alternatives Considered
- *Token-count truncation only*: Rejected because it removes chunks by position rather than relevance, potentially keeping low-quality tail chunks and discarding relevant ones.
- *No pruning (pass all re-ranked results)*: Rejected per FR-015 mandate and increased hallucination risk.
