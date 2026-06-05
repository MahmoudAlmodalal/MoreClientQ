# Tasks: MoreClient AI Enterprise Platform

**Input**: Design documents from `specs/003-fix-all-buge/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Included — constitution Principle III mandates TDD and contract tests for all API endpoints.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Paths follow web application structure: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding and toolchain configuration

- [X] T001 Create backend/ and frontend/ directory structure per plan.md project layout
- [X] T002 Initialize Python 3.11 backend project: create backend/requirements.txt with fastapi, sqlalchemy[asyncio], alembic, pydantic-settings, pyjwt, bcrypt, httpx, boto3, qdrant-client, redis, stripe, sentence-transformers, pypdf2, python-docx, openpyxl, beautifulsoup4, click, pytest, pytest-asyncio, ruff
- [X] T003 [P] Initialize React/TypeScript/Vite frontend: `npm create vite@latest frontend -- --template react-ts`; add lucide-react, recharts, react-router-dom as dependencies; add vitest, @testing-library/react, @testing-library/jest-dom as devDependencies
- [X] T004 [P] Create docker-compose.local.yml: PostgreSQL 15, Qdrant latest, Redis 7, ClamAV (mkodockr/clamav), and MinIO services with health checks and named volumes
- [X] T005 [P] Configure backend linting: create backend/pyproject.toml with ruff (line-length=120, select=["E","F","I"]) and black settings
- [X] T006 [P] Configure frontend linting: create frontend/eslint.config.js with TypeScript rules and frontend/.prettierrc
- [X] T007 [P] Create backend/.env.example with all environment variables from quickstart.md including RAG_COSINE_THRESHOLD=0.75
- [X] T008 [P] Create backend/tests/conftest.py with pytest fixtures: async test database engine (SQLite in-memory), async httpx client, `make_tenant()` factory, and `set_rls_context(tenant_id)` helper

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Create backend/src/config.py: Pydantic BaseSettings loading DATABASE_URL, REDIS_URL, QDRANT_URL, CLAMAV_HOST, CLAMAV_PORT, JWT_SECRET, STRIPE_API_KEY, OPENAI_API_KEY, RAG_COSINE_THRESHOLD (float default 0.75), MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
- [ ] T010 Create backend/src/database.py: SQLAlchemy async engine, AsyncSessionLocal, `get_db` FastAPI dependency, and `set_tenant_context(tenant_id)` that executes `SET LOCAL app.current_tenant_id = :tenant_id` on each session via SQLAlchemy event listener to enforce RLS
- [ ] T011 Create backend/src/models/audit_log.py: AuditLog SQLAlchemy model (id, tenant_id, actor_id, actor_role, action_type, resource, metadata JSONB, created_at); immutability enforced via PostgreSQL trigger `prevent_audit_log_modification()` from data-model.md; tenant RLS policy
- [ ] T012 [P] Create backend/src/services/audit.py: standalone audit service — `record(actor_id, role, action_type, resource, metadata, tenant_id)` persists AuditLog; `list_logs(tenant_id, limit, offset)` for tenant export; no web server dependency
- [ ] T013 Initialize Alembic: run `alembic init alembic` in backend/; configure alembic/env.py to use async engine from src/config.py and auto-import all models via `target_metadata`
- [ ] T014 Create Alembic initial migration alembic/versions/001_initial_schema.py: CREATE TABLE statements for all 12 tables per data-model.md (tenants, workspaces, assistants, users, knowledge_sources, knowledge_versions, conversations, messages, leads, human_agents, subscriptions, audit_logs); ALTER TABLE ... ENABLE ROW LEVEL SECURITY and CREATE POLICY tenant_isolation_policy for all tenant-scoped tables; all indexes; audit_logs immutability trigger
- [ ] T015 [P] Create backend/src/api/middleware/rbac.py: FastAPI dependency `require_role(*roles)` that extracts JWT claims, checks user.role against allowed roles list, raises 403 if unauthorized; role hierarchy: super_admin > tenant_admin > agent > viewer
- [ ] T016 [P] Create backend/src/main.py: FastAPI app with CORSMiddleware (allow all origins in dev), global exception handlers (HTTPException, ValidationError, 500), structured JSON logging via Python logging, and router registration stubs for all api/ modules
- [ ] T017 [P] Create backend/src/services/cache.py: async Redis client from REDIS_URL, `tenant_key(tenant_id, key) -> str` returning f"{tenant_id}:{key}" for namespace isolation, `incr_usage(tenant_id, metric, amount=1)` atomic INCRBY, `get_usage(tenant_id, metric) -> int`
- [ ] T018 [P] Create backend/src/services/storage.py: boto3 async-compatible S3/MinIO client, `tenant_path(tenant_id, filename) -> str` returning f"tenants/{tenant_id}/{filename}" enforcing tenant-prefixed folders, `upload_file(tenant_id, filename, data)`, `download_file(tenant_id, filename)`, `delete_file(tenant_id, filename)`
- [ ] T019 [P] Create backend/src/services/vector_store.py: Qdrant async client from QDRANT_URL, `get_collection_name(region) -> str` returning "moreclient_vectors_gcc" or "moreclient_vectors_global", `ensure_collection(region)` creates collection if absent (1536 dims, cosine), `tenant_filter(tenant_id)` builds Qdrant Filter must-match payload dict
- [ ] T020 Create frontend/src/index.css: CSS custom properties (--color-primary, --color-bg, --spacing-*), @import for Outfit font (LTR) and Cairo font (RTL) from Google Fonts, `:root[dir="rtl"]` overrides for font-family, base reset using logical properties (margin-inline, padding-inline, inset-inline) throughout
- [ ] T021 Create frontend/src/contexts/DirectionContext.tsx: React context with `dir: "ltr" | "rtl"`, `toggleDirection()`, persists preference to localStorage; on mount, sets `document.documentElement.dir` and `document.documentElement.lang`; exports `useDirection()` hook
- [ ] T022 [P] Create frontend/src/components/RBACGuard.tsx: `<RBACGuard roles={["tenant_admin"]}>{children}</RBACGuard>` — reads user role from AuthContext, returns null (hidden) if role not in allowed list; used to conditionally render navigation links, buttons, settings pages, and forms per FR-029
- [ ] T023 [P] Create frontend/src/services/api.ts: typed fetch wrapper — `apiClient.get/post/put/delete(path, body?)` injects `Authorization: Bearer {token}` from localStorage, handles 401 by calling POST /auth/refresh and retrying once, throws typed ApiError on failure
- [ ] T024 Create frontend/src/main.tsx: ReactDOM.createRoot with BrowserRouter, AuthProvider, DirectionContext.Provider, and route definitions: /register, /verify, /onboarding, /dashboard (protected), /dashboard/knowledge, /dashboard/assistant, /dashboard/agent-inbox, /dashboard/billing, /dashboard/training, /dashboard/leads, /dashboard/analytics, /dashboard/settings

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Tenant Onboarding & First AI Assistant (Priority: P1) 🎯 MVP

**Goal**: A new B2B customer registers, uploads one document, and has a live AI assistant widget within a single session.

**Independent Test**: Register a new account → verify email → upload one PDF → configure assistant → copy embed code → open in browser — AI responds using only uploaded knowledge.

### Tests for User Story 1 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T025 [P] [US1] Contract test POST /api/v1/auth/register in backend/tests/contract/test_auth_register.py: assert 201 + tenant_id on valid payload; assert 422 on password complexity failure (< 8 chars, missing symbol); assert 409 on duplicate email
- [ ] T026 [P] [US1] Contract test GET /api/v1/auth/verify in backend/tests/contract/test_auth_verify.py: assert 200 on valid token; assert 400 on expired token; assert 400 on malformed token
- [ ] T027 [P] [US1] Contract test POST /api/v1/auth/login in backend/tests/contract/test_auth_login.py: assert 200 with access_token, refresh_token, token_type on valid credentials; assert 401 on wrong password; assert 403 on unverified email
- [ ] T028 [P] [US1] Contract test GET/PUT /api/v1/workspace in backend/tests/contract/test_workspace.py: assert GET returns company_info + branding JSONB; assert PUT with valid payload returns 200; assert 403 when called with Agent role token
- [ ] T029 [P] [US1] Contract test POST /api/v1/knowledge/upload in backend/tests/contract/test_knowledge_upload.py: assert 202 + source_id + status=processing on valid PDF; assert 400 on simulated infected file (mock scanner); assert 400 on unsupported file type (.exe)
- [ ] T030 [US1] Integration test full onboarding flow in backend/tests/integration/test_onboarding.py: POST /auth/register → GET /auth/verify → POST /auth/login → POST /knowledge/upload → poll GET /knowledge/sources/{id} until status=ready → GET /assistants/{id}/embed; assert embed snippet contains assistant_id

### Implementation for User Story 1

- [ ] T031 [P] [US1] Create backend/src/models/user.py: User SQLAlchemy model (id UUID PK, tenant_id FK, email unique, hashed_password, full_name, role VARCHAR enum, email_verified BOOLEAN default false, created_at); tenant RLS policy; index on email
- [ ] T032 [P] [US1] Create backend/src/models/tenant.py: Tenant SQLAlchemy model per data-model.md (id, name, industry, plan, region immutable, status, created_at); no RLS on tenants table itself; status enum: active/suspended/cancelled
- [ ] T033 [P] [US1] Create backend/src/models/workspace.py: Workspace SQLAlchemy model (id, tenant_id UNIQUE FK, company_info JSONB, branding JSONB, timezone, country, created_at); tenant RLS policy
- [ ] T034 [P] [US1] Create backend/src/models/assistant.py: Assistant SQLAlchemy model (id, tenant_id FK, workspace_id FK, name, avatar_url, personality enum, language_mode enum, guardrails JSONB default {"context_similarity_threshold": 0.75, "restrict_external": true, "escalation_confidence_threshold": 0.70, "escalation_message_threshold": null, "competitor_domains": []}, created_at); tenant RLS; index on tenant_id
- [ ] T035 [P] [US1] Create backend/src/models/knowledge.py: KnowledgeSource (id, tenant_id, workspace_id, type enum, status enum, file_metadata JSONB, content_hash, created_at, updated_at) and KnowledgeVersion (id, tenant_id, version_number, change_log, is_active, created_at) SQLAlchemy models; tenant RLS policies on both; indexes on tenant_id
- [ ] T036 [US1] Create backend/src/services/auth.py: standalone auth service — `hash_password(plain) -> str`, `verify_password(plain, hashed) -> bool`, `create_access_token(user_id, tenant_id, role) -> str` (15 min expiry), `create_refresh_token(user_id) -> str` (7 day expiry, stored in Redis for rotation), `rotate_refresh_token(old_token) -> (access, refresh)`, `send_verification_email(email, token)` via SMTP (logs to stdout if SMTP_HOST unset)
- [ ] T037 [US1] Create backend/src/services/provisioning.py: standalone tenant provisioning service — `provision_tenant(name, email, hashed_password, region)` creates Tenant + Workspace + default Assistant + User in one atomic DB transaction; calls vector_store.ensure_collection(region) to initialize Qdrant collection; returns (tenant_id, user_id, verification_token)
- [ ] T038 [US1] Implement backend/src/api/auth.py: POST /auth/register (FR-001 password complexity validation, call provisioning.provision_tenant, send verification email, return 201), GET /auth/verify (validate token from Redis, set user.email_verified=True, return 200), POST /auth/login (verify credentials, check email_verified, return JWT pair), POST /auth/refresh (rotate refresh token)
- [ ] T039 [US1] Implement backend/src/api/tenants.py: GET /workspace (return workspace config for authenticated tenant), PUT /workspace (update company_info and branding, require_role("tenant_admin"), record audit log entry)
- [ ] T040 [US1] Create backend/src/services/scanner.py: ClamAV TCP client `scan_file_stream(file_bytes: bytes) -> (bool, str)` returning (is_clean, detail); connects to CLAMAV_HOST:CLAMAV_PORT via socket; returns (True, "OK") mock when CLAMAV_HOST is unset in config
- [ ] T041 [US1] Create backend/src/services/extractor.py: `extract_chunks(file_bytes, file_type) -> list[str]` for PDF (pypdf2.PdfReader), DOCX (python-docx Document), TXT (utf-8 decode), CSV (csv.reader first 3 columns), XLSX (openpyxl load_workbook); chunk into 512-token segments with 10% overlap using simple whitespace tokenizer
- [ ] T042 [US1] Create backend/src/services/vectorizer.py: `embed_and_store(tenant_id, source_id, chunks, region)` — generates embeddings via OpenAI text-embedding-3-small or Gemini text-embedding (pluggable via config.EMBEDDING_PROVIDER), upserts vectors to Qdrant with payload {tenant_id, source_id, text, document_version}; `reindex_source(tenant_id, source_id, region)` deletes existing vectors for source_id then re-embeds from stored chunks
- [ ] T043 [US1] Create backend/src/services/pipeline.py: `process_knowledge_source(source_id)` orchestrates scanner.scan → storage.download → extractor.extract_chunks → vectorizer.embed_and_store → versioning.create_version → set KnowledgeSource.status=ready; enforces 2 min/MB SLA via asyncio.wait_for timeout; on timeout or failure sets status=failed and fires 'document_processing_failed' notification
- [ ] T044 [US1] Create backend/src/services/versioning.py: `create_version(tenant_id, change_log) -> KnowledgeVersion` increments version number (v1.0 → v1.1) and snapshots active source IDs; `rollback_to_version(tenant_id, version_id)` sets target version is_active=True, clears Qdrant vectors for current version's non-overlapping sources, re-indexes rolled-back sources
- [ ] T045 [US1] Implement backend/src/api/knowledge.py (upload scope): POST /knowledge/upload streams file to scanner.scan_file_stream, on clean stores to MinIO via storage.upload_file, creates KnowledgeSource record status=processing, fires pipeline.process_knowledge_source as background task, returns 202 with source_id; GET /knowledge/sources/{id} for status polling
- [ ] T046 [US1] Implement backend/src/api/assistants.py: GET /assistants (list for tenant), POST /assistants (create), GET /assistants/{id}, PUT /assistants/{id} (update name/avatar/personality/language_mode/guardrails, require_role("tenant_admin")), GET /assistants/{id}/embed (return JavaScript embed snippet `<script src="/widget.js" data-assistant-id="{id}"></script>`)
- [ ] T047 [P] [US1] Create frontend/src/pages/Register.tsx: form with full name, email, password (real-time complexity indicator: length/uppercase/lowercase/number/symbol), region selector (GCC/Global with descriptions); calls POST /auth/register; on 201 redirects to /verify
- [ ] T048 [P] [US1] Create frontend/src/pages/EmailVerification.tsx: shows "check your inbox" state with resend link; handles ?token= query param by calling GET /auth/verify on mount; shows success redirect to /onboarding or error state
- [ ] T049 [P] [US1] Create frontend/src/pages/Onboarding.tsx: 3-step wizard (step 1: company name/industry/website/country/timezone → PUT /workspace; step 2: logo upload + primary color picker → PUT /workspace branding; step 3: assistant name + personality + language mode → PUT /assistants/{id}); progress indicator; RTL-aware layout
- [ ] T050 [P] [US1] Create frontend/src/pages/AssistantBuilder.tsx: full assistant config form — name, avatar URL, personality radio (Friendly/Professional/Formal/Sales/Technical Support), language mode (Arabic/English/Bilingual), guardrails toggle (restrict external knowledge, competitor domain blocklist textarea, escalation confidence threshold slider 0–100%, escalation message threshold input); wrapped in `<RBACGuard roles={["tenant_admin"]}>`; saves via PUT /assistants/{id}
- [ ] T051 [US1] Create frontend/src/pages/KnowledgeBase.tsx (US1 scope): drag-and-drop file upload zone (PDF/DOCX/TXT/CSV/XLSX, max 50MB), upload progress bar, processing status with polling (GET /knowledge/sources/{id} every 3s until ready/failed), knowledge source list table; embed code panel showing `<script>` snippet from GET /assistants/{id}/embed with copy-to-clipboard button

**Checkpoint**: Register → verify email → upload PDF → configure assistant → embed widget in HTML → AI responds using uploaded knowledge

---

## Phase 4: User Story 2 - End Customer AI Conversation (Priority: P1)

**Goal**: An end customer chats with the AI assistant in the embedded widget; receives accurate answers in <5s; low-confidence or negative-sentiment messages auto-escalate.

**Independent Test**: Send question matching knowledge base → AI response <5s with confidence_score; send "I want to speak to someone" → escalated=true in response.

### Tests for User Story 2 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T052 [P] [US2] Contract test POST /api/v1/chat/widget in backend/tests/contract/test_chat_widget.py: assert 200 with response (string), confidence_score (0–1 float), escalated (bool); assert escalated=true when intent=EscalationRequest; assert response delivered within 5s
- [ ] T053 [P] [US2] Unit tests for search pipeline in backend/tests/unit/test_search.py: test hybrid_search RRF fusion merges Qdrant + FTS results correctly; test cross-encoder reranker filters by descending score; test cosine threshold pruning drops chunks below 0.75 and keeps chunks at/above 0.75
- [ ] T054 [US2] Integration test AI conversation in backend/tests/integration/test_conversation.py: provision tenant + upload knowledge → POST /chat/widget with matching question → assert response non-empty, confidence_score > 0, message persisted in DB with correct conversation_id

### Implementation for User Story 2

- [ ] T055 [P] [US2] Create backend/src/models/conversation.py: Conversation SQLAlchemy model per data-model.md including csat_triggered BOOLEAN default false, csat_score SMALLINT nullable; tenant RLS policy; composite index on (tenant_id, status); index on assigned_agent_id
- [ ] T056 [P] [US2] Create backend/src/models/message.py: Message SQLAlchemy model (id, tenant_id FK, conversation_id FK, sender_type enum, content TEXT, confidence_score NUMERIC(5,4) nullable, created_at); tenant RLS policy; index on conversation_id
- [ ] T057 [US2] Create backend/src/services/search.py: standalone hybrid search — `hybrid_search(tenant_id, query, assistant_id) -> list[dict]` executes: (1) PostgreSQL full-text search on knowledge_chunks tsvector column, (2) Qdrant vector search with tenant_filter + score_threshold from assistant.guardrails.context_similarity_threshold, (3) RRF merge of both result sets, (4) cross-encoder re-ranking via sentence-transformers (mock returns input order if model unavailable), (5) prune results below cosine threshold; returns ranked chunks with text + score
- [ ] T058 [US2] Create backend/src/services/intelligence.py: standalone intelligence service — `classify_message(content) -> (intent, sentiment_label, sentiment_score, urgency)` using keyword heuristics + optional LLM classification; `rewrite_query(content, history) -> str` prepends last 3 exchanges as context; `check_escalation(assistant_guardrails, intent, sentiment_score, confidence_score, message_count) -> bool` triggers escalation on: intent in [Complaint, EscalationRequest], sentiment_score < 30, confidence_score < guardrails.escalation_confidence_threshold, or message_count > guardrails.escalation_message_threshold (if set)
- [ ] T059 [US2] Create backend/src/services/rag.py: standalone RAG generator — `generate_response(tenant_id, assistant_id, conversation_id, message) -> (response_text, confidence_score)` orchestrates: intelligence.rewrite_query → search.hybrid_search → assemble context string from top chunks → build LLM prompt with assistant personality/language_mode + system guardrails → call LLM (OpenAI or Gemini via abstract factory from config.LLM_PROVIDER) → return response + mean confidence of used chunks; asyncio.wait_for(timeout=5.0) enforces <5s SLA
- [ ] T060 [US2] Implement backend/src/api/chat.py: POST /chat/widget — creates Conversation if conversation_id not found, calls rag.generate_response, persists Message(sender_type=user) + Message(sender_type=assistant, confidence_score=score), calls cache.incr_usage(tenant_id, "messages"), calls intelligence.check_escalation → if True updates Conversation.status=escalated + triggers agent assignment, returns {response, confidence_score, escalated}
- [ ] T061 [P] [US2] Create embeddable widget in frontend/widget/: widget.js (vanilla JS, no bundler dependency) — renders chat bubble button, opens chat panel on click, POSTs messages to /chat/widget, renders AI response with 30ms/char typing animation, shows read receipt (✓✓) after response, handles escalated=true by showing "Connecting you to an agent…" message, respects language_mode and dir attribute for RTL; widget.css — all styles scoped to .mc-widget class using vanilla CSS, no Tailwind
- [ ] T062 [US2] Extend frontend/widget/widget.js: on init render suggested_questions as clickable chips if configured; show offline_mode.message and disable input when widget_status=offline; auto-open after auto_open_delay seconds if configured; use primary_color CSS variable for button and header tint

**Checkpoint**: Embed widget.js snippet in any HTML page → question answered by AI in <5s → complaint message returns escalated=true

---

## Phase 5: User Story 3 - Knowledge Base Management (Priority: P2)

**Goal**: Tenant Admin uploads multiple document types, scrapes URLs (depth 1, max 50 pages), manages versions, and can rollback to any prior knowledge version.

**Independent Test**: Upload DOCX + CSV + scrape a URL → knowledge increments to v1.2 → rollback to v1.0 → AI answers reflect v1.0 content.

### Tests for User Story 3 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T063 [P] [US3] Contract test POST /api/v1/knowledge/scrape in backend/tests/contract/test_knowledge_scrape.py: assert 202 + source_id + pages_queued ≤ 50 on valid URL; assert 400 with "page cap reached" error when tenant already has 50 scraped pages
- [ ] T064 [P] [US3] Contract test knowledge version endpoints in backend/tests/contract/test_knowledge_versions.py: assert GET /knowledge/versions returns list with version_number, is_active, change_log; assert POST /knowledge/versions/{id}/rollback returns 200 on valid version_id; assert 404 on non-existent version
- [ ] T065 [US3] Integration test knowledge versioning in backend/tests/integration/test_knowledge_versioning.py: upload doc → v1.0; upload second doc → v1.1; rollback to v1.0 via POST /knowledge/versions/{id}/rollback; GET /knowledge/versions → assert v1.0 is_active=true

### Implementation for User Story 3

- [ ] T066 [US3] Create backend/src/services/scraper.py: `scrape_url(tenant_id, start_url) -> list[str]` using BeautifulSoup + httpx — enforces depth 1 (only links on start_url page), checks tenant page cap (count existing url-type KnowledgeSources ≤ 50 per FR-010), respects robots.txt; yields cleaned text per page; raises CapExceededError if at limit
- [ ] T067 [US3] Extend backend/src/api/knowledge.py with full knowledge management: POST /knowledge/scrape (check 50-page cap, create KnowledgeSource type=url, enqueue scraper+pipeline), POST /knowledge/qa (create KnowledgeSource type=qa with content directly embedded), GET /knowledge/sources (list all with type/status/version), DELETE /knowledge/sources/{id} (remove from MinIO + Qdrant + DB, create new version), GET /knowledge/versions (list all versions), POST /knowledge/versions/{id}/rollback (call versioning.rollback_to_version)
- [ ] T068 [US3] Implement versioning.rollback_to_version in backend/src/services/versioning.py: set target KnowledgeVersion.is_active=True + current active is_active=False in one transaction; for each source in target version snapshot: if not in current active set, re-run vectorizer.reindex_source; for each source not in target snapshot: delete vectors from Qdrant via vector_store; record audit log entry
- [ ] T069 [P] [US3] Update frontend/src/pages/KnowledgeBase.tsx with full US3 scope: URL scraping input with domain preview + pages-queued feedback; manual Q&A form (question + answer inputs); version history table (version_number, created_at, change_log, is_active chip, Rollback button); rollback confirmation modal; all actions RBAC-gated to tenant_admin via RBACGuard

**Checkpoint**: Upload DOCX + scrape URL → versions increment → rollback to v1 → AI uses v1 knowledge

---

## Phase 6: User Story 4 - Human Agent Handling Live Escalations (Priority: P2)

**Goal**: A human support agent accepts escalated conversations, replies in real time with full AI history visible, closes tickets — CSAT prompt is mandatory on resolution.

**Independent Test**: Trigger escalation from widget → log in as Agent → accept → exchange real-time messages with customer → mark resolved → CSAT 1-5 prompt appears in widget.

### Tests for User Story 4 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T070 [P] [US4] Contract test POST /api/v1/conversations/{id}/resolve in backend/tests/contract/test_conversation_resolve.py: assert 200 with csat_triggered=true; assert 400 if conversation not in 'agent' status; assert 403 if called by Viewer role
- [ ] T071 [P] [US4] Contract test POST /api/v1/conversations/{id}/csat in backend/tests/contract/test_csat.py: assert 200 on score 1–5; assert 422 on score=0 or score=6; assert 404 on unknown conversation_id
- [ ] T072 [US4] Integration test escalation flow in backend/tests/integration/test_escalation.py: POST /chat/widget with complaint intent → assert Conversation.status=escalated; POST /escalations/{id}/accept as agent → assert assigned_agent_id set; POST /conversations/{id}/resolve → assert csat_triggered=True; POST /conversations/{id}/csat with score=4 → assert csat_score=4

### Implementation for User Story 4

- [ ] T073 [P] [US4] Create backend/src/models/agent.py: HumanAgent SQLAlchemy model (id, tenant_id FK, name, email, skills VARCHAR[] default {}, availability_status enum default offline, created_at); tenant RLS policy; unique index on email; composite index on (tenant_id, availability_status)
- [ ] T074 [US4] Create backend/src/services/agent_manager.py: standalone agent routing service — `get_available_agents(tenant_id)` queries availability_status='online'; `assign_agent(tenant_id, conversation_id, strategy)` implementing: Round Robin (circular index in Redis), Least Busy (fewest active conversations), Skill-Based (match conversation intent to agent skills); `update_availability(agent_id, status)` sets availability_status
- [ ] T075 [US4] Implement backend/src/api/agent_chat.py: GET /escalations (list conversations with status=escalated or status=agent for current tenant, require_role("agent","tenant_admin")), POST /escalations/{id}/accept (call agent_manager.assign_agent, set status=agent, record audit), POST /conversations/{id}/resolve (set status=resolved, set csat_triggered=True, notify customer via WebSocket, record audit), POST /conversations/{id}/csat (record csat_score 1-5, 422 if out of range), GET /conversations/{id}/history (return all messages for conversation)
- [ ] T076 [US4] Implement backend/src/api/sockets.py: FastAPI WebSocket endpoint /ws/{conversation_id}?token={jwt} — validate JWT on connect, join room by conversation_id, broadcast incoming messages to all connections in room, handle disconnect gracefully; used by both widget (customer) and agent inbox (agent)
- [ ] T077 [P] [US4] Create frontend/src/pages/AgentInbox.tsx: two-panel layout — left: escalated conversation queue (sorted by urgency, shows intent + sentiment badge + customer wait time), right: selected conversation detail with full AI conversation history (scrollable) + live message composer; WebSocket connection to /ws/{conversation_id}; Resolve button (calls POST /conversations/{id}/resolve); RBAC-gated to agent + tenant_admin via RBACGuard; RTL-aware message bubble alignment
- [ ] T078 [US4] Extend frontend/widget/widget.js with CSAT support: listen for WebSocket message type=csat_prompt; render 5-star rating UI overlay in chat panel; POST selected score to /conversations/{id}/csat; show "Thank you for your feedback" confirmation; dismiss on submit

**Checkpoint**: Log in as Agent, accept escalation, exchange real-time messages, mark resolved — CSAT 5-star rating appears in widget

---

## Phase 7: User Story 5 - Subscription & Usage Billing (Priority: P2)

**Goal**: Tenant Admin monitors usage vs plan limits; alerts fire at 80% and 100%; overage charges apply automatically without manual intervention.

**Independent Test**: Select plan, simulate messages beyond limit via Redis counter, verify 80% alert notification fired, 100% alert fired, Stripe usage record reported.

### Tests for User Story 5 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T079 [P] [US5] Contract test GET /api/v1/billing/subscription in backend/tests/contract/test_billing.py: assert 200 with plan_type (string), limits (object with message_limit), current_usage (object with messages_sent), usage_alert_level enum none/warning_80/critical_100
- [ ] T080 [US5] Integration test usage metering in backend/tests/integration/test_billing.py: provision tenant with message_limit=100, simulate 81 messages via cache.incr_usage, call billing.check_usage_alerts → assert warning_80 notification created; simulate 101 messages → assert critical_100 notification created; assert Stripe usage record API called (mocked)

### Implementation for User Story 5

- [ ] T081 [P] [US5] Create backend/src/models/subscription.py: Subscription SQLAlchemy model per data-model.md (tenant_id UNIQUE FK, plan_type, billing_cycle enum monthly/annual, limits JSONB, current_usage JSONB, stripe_subscription_id, expires_at, created_at, updated_at); add trigger to sync current_usage from Redis hourly
- [ ] T082 [US5] Create backend/src/services/billing.py: standalone Stripe billing service — `get_subscription(tenant_id)` returns Subscription + usage_alert_level computed from Redis counters; `check_usage_alerts(tenant_id)` compares Redis message count to limits, calls notifications.send_in_app + send_email at 80% and 100% crossings (idempotent via Redis flag); `report_overage(tenant_id)` calls Stripe Metered Billing usage records API at billing cycle end; mock all Stripe calls when STRIPE_API_KEY starts with "sk_test_"
- [ ] T083 [US5] Implement backend/src/api/webhooks.py: POST /webhooks/stripe — verify Stripe-Signature header, handle events: invoice.payment_succeeded (mark subscription paid), customer.subscription.updated (sync plan limits), customer.subscription.deleted (suspend workspace); all changes recorded in audit_logs
- [ ] T084 [US5] Create backend/src/models/notification.py + implement backend/src/api/notifications.py: Notification model (id, tenant_id, user_id, event_type, payload JSONB, is_read, created_at); GET /notifications (list unread for authenticated user, max 50), POST /notifications/{id}/read; tenant RLS
- [ ] T085 [US5] Create backend/src/services/notifications.py: standalone notification service — `send_in_app(tenant_id, user_id, event_type, payload)` persists Notification record; `send_email(to, subject, body)` via smtplib (prints to stdout if SMTP_HOST unset); handles all FR-027 events: complaint_received, lead_created, subscription_expiring (7 days before expires_at), document_processing_failed, agent_assigned, usage_warning_80, usage_critical_100
- [ ] T086 [P] [US5] Create frontend/src/pages/Billing.tsx: current plan summary card, usage meters with progress bars for messages/tokens/storage (color-coded: green <80%, amber 80–99%, red ≥100%), alert banners at 80% and 100% thresholds, subscription expiry warning if < 7 days; calls GET /billing/subscription; RBAC-gated to tenant_admin
- [ ] T087 [P] [US5] Create frontend/src/components/NotificationBell.tsx: bell icon with unread count badge in navbar, opens dropdown of last 10 notifications with event type label + timestamp + mark-read; polls GET /notifications every 30s; marks individual items read via POST /notifications/{id}/read; RTL-aware dropdown position

**Checkpoint**: View Billing page, see usage meters; simulate messages past 80% → amber progress bar + alert banner appears

---

## Phase 8: User Story 6 - AI Training Center (Priority: P3)

**Goal**: Tenant Admin reviews failed AI responses, provides correct answers embedded into knowledge, and flags hallucinating source files for re-indexing.

**Independent Test**: Submit correct answer for a downvoted response → knowledge updated; flag source file → re-index job queued; failed response marked Resolved.

### Tests for User Story 6 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T088 [P] [US6] Contract test GET /api/v1/training/failures in backend/tests/contract/test_training.py: assert 200 with list containing message_id, question (string), failure_type (enum), resolved (bool); assert 403 with Agent role token
- [ ] T089 [P] [US6] Contract test POST /api/v1/training/failures/{id}/reindex in backend/tests/contract/test_training_reindex.py: assert 202 on valid source_id belonging to tenant; assert 404 on unknown source_id; assert 403 if source_id belongs to different tenant (RLS validation)
- [ ] T090 [US6] Integration test training workflow in backend/tests/integration/test_training.py: create FailedResponse fixture → POST /training/failures/{id}/answer with correct_answer → assert QA KnowledgeSource created + failure marked resolved; POST /training/failures/{id}/reindex → assert vectorizer.reindex_source called (mocked) + 202 returned

### Implementation for User Story 6

- [ ] T091 [P] [US6] Create backend/src/models/training.py: FailedResponse SQLAlchemy model (id, tenant_id FK, message_id FK, conversation_id FK, failure_type enum low_confidence/no_retrieval/hallucination/downvoted, question TEXT, correct_answer TEXT nullable, flagged_source_id UUID nullable, resolved BOOLEAN default false, created_at); tenant RLS policy
- [ ] T092 [US6] Implement backend/src/api/training.py: GET /training/failures (filter by failure_type + resolved=false, require_role("tenant_admin")), POST /training/failures/{id}/answer (create KnowledgeSource type=qa with answer text, embed immediately via vectorizer.embed_and_store, set FailedResponse.resolved=True, create knowledge version), POST /training/failures/{id}/reindex (validate source_id in tenant's sources via RLS, enqueue vectorizer.reindex_source background task, return 202)
- [ ] T093 [US6] Extend backend/src/services/rag.py failure detection: after generate_response, if confidence_score < 0.5 OR len(search_results)==0, create FailedResponse record with failure_type=low_confidence or no_retrieval; add separate endpoint POST /chat/widget/{message_id}/downvote to create FailedResponse type=downvoted
- [ ] T094 [P] [US6] Create frontend/src/pages/TrainingCenter.tsx: tabbed view (Low Confidence | No Retrieval | Hallucinations | Downvoted), each tab shows paginated list of failed responses with question preview; selected row expands to show full AI response + context; correct-answer textarea with Submit button (POST /training/failures/{id}/answer); source file selector dropdown + Re-index button (POST /training/failures/{id}/reindex); resolved badge on completed items; RBAC-gated to tenant_admin

**Checkpoint**: Open Training Center → select failed response → provide correct answer → knowledge version increments; flag source file → re-index job queued

---

## Phase 9: User Story 7 - CRM Lead Pipeline (Priority: P3)

**Goal**: Purchase-intent AI conversations auto-create lead records; Tenant Admin tracks leads through a visual pipeline.

**Independent Test**: Send "I want to buy your product" in widget → lead auto-created with available contact fields; move lead card from New to Contacted in dashboard.

### Tests for User Story 7 (Constitution Principle III — Write FIRST, verify FAILING before implementation)

- [ ] T095 [P] [US7] Contract test GET /api/v1/leads in backend/tests/contract/test_leads.py: assert 200 with list containing id, name (nullable), email (nullable), phone (nullable), channel, estimated_value (nullable), pipeline_stage enum; assert ?stage=new filter works
- [ ] T096 [P] [US7] Contract test PUT /api/v1/leads/{id}/stage in backend/tests/contract/test_lead_stage.py: assert 200 with updated pipeline_stage; assert 422 on invalid stage value; assert 200 on valid transition New→Contacted; assert audit log entry created
- [ ] T097 [US7] Integration test lead auto-creation in backend/tests/integration/test_leads.py: POST /chat/widget with message "I want to buy" (mocked intelligence returns PurchaseIntent) → assert Lead record created with tenant_id, pipeline_stage=new, channel=web; PUT /leads/{id}/stage with stage=contacted → assert stage updated + audit log entry recorded

### Implementation for User Story 7

- [ ] T098 [P] [US7] Create backend/src/models/lead.py: Lead SQLAlchemy model per data-model.md (id, tenant_id FK, conversation_id FK nullable, name nullable, email nullable, phone nullable, channel, estimated_value NUMERIC(12,2) nullable, pipeline_stage enum, created_at, updated_at); tenant RLS policy; index on (tenant_id, pipeline_stage)
- [ ] T099 [US7] Extend backend/src/api/chat.py lead detection: after intelligence.classify_message returns PurchaseIntent, extract contact fields from conversation context (email regex, name from greeting), create Lead record with available fields + pipeline_stage=new + channel=web, fire notifications.send_in_app(event_type="lead_created"), record audit log
- [ ] T100 [US7] Implement backend/src/api/leads.py: GET /leads (filter by ?stage=, require_role("tenant_admin","agent")), PUT /leads/{id}/stage (validate stage enum, update, record stage transition in audit_log with old_stage and new_stage in metadata), GET /leads/{id} (full detail with linked conversation_id)
- [ ] T101 [P] [US7] Create frontend/src/pages/Leads.tsx: Kanban board with 6 columns (New/Contacted/Qualified/Proposal/Won/Lost), each column shows lead cards (name or "Unknown", channel chip, estimated_value if set, created_at relative time); clicking card opens detail panel with conversation link; drag-and-drop to update stage via PUT /leads/{id}/stage; RBAC-gated to tenant_admin + agent

**Checkpoint**: Send purchase-intent message in widget → Lead appears in New column → drag to Contacted → stage updated in DB

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: CLI, exports, analytics, security hardening, RTL validation, and end-to-end verification

- [ ] T102 [P] Implement backend/src/cli.py: Click CLI with commands — `mc tenant list` (table of all tenants), `mc tenant suspend <id>`, `mc tenant activate <id>`, `mc billing sync <tenant_id>` (force Stripe usage report), `mc system health` (checks DB/Redis/Qdrant/ClamAV connectivity); all operations run standalone without web server per constitution Principle II
- [ ] T103 [P] Implement backend/src/api/exports.py: GET /exports/conversations (stream CSV or JSON of conversations+messages scoped to tenant), GET /exports/leads (stream CSV or JSON of leads scoped to tenant), GET /exports/audit-logs (stream CSV or JSON of audit logs scoped to tenant); each requires ?format=csv|json; download filename set via Content-Disposition header; require_role("tenant_admin"); record export action in audit_log
- [ ] T104 [P] Create frontend/src/pages/Settings.tsx: language toggle (English/Arabic) calling DirectionContext.toggleDirection; Data Export section with explicit "Download CSV" and "Download JSON" buttons for conversations, leads, and audit logs (calls GET /exports/{type}?format=); buttons wrapped in `<RBACGuard roles={["tenant_admin"]}>` per FR-033
- [ ] T105 [P] Implement backend/src/api/analytics.py: GET /analytics/dashboard returns {total_conversations (30d), ai_deflection_rate (% resolved without escalation), avg_confidence_score, top_intents [{intent, count}], messages_per_day [{date, count}]}; data computed from conversations+messages tables with RLS; require_role("tenant_admin","agent")
- [ ] T106 [P] Create frontend/src/pages/Analytics.tsx: Recharts LineChart for daily message volume, RadialBarChart for AI deflection rate %, BarChart for top intents; all charts have RTL-aware axis labels; uses GET /analytics/dashboard
- [ ] T107 Add application-layer rate limiting to backend/src/main.py: integrate slowapi SlowAPIMiddleware; limit POST /chat/widget to 60 req/min per IP; limit POST /auth/login + POST /auth/register to 10 req/min per IP per FR-031
- [ ] T108 [P] Add Google OAuth login to backend/src/api/auth.py: POST /auth/google accepts {code, redirect_uri}, exchanges via Google OAuth2 API, provisions or finds existing user, returns JWT pair; frontend/src/pages/Register.tsx: add "Sign in with Google" button per FR-004
- [ ] T109 [P] Write backend/tests/integration/test_rls_isolation.py: for each API module (workspace, knowledge, conversations, messages, leads, audit_logs), create two tenants A and B, authenticate as tenant A, attempt to read/write tenant B's resources — assert all return 404 or 403 (no data leakage)
- [ ] T110 [P] Write backend/tests/load/test_scale.py: locust LoadTestShape simulating 1000 concurrent users sending POST /chat/widget; assert p95 response time < 5000ms; assert 0 5xx errors; run with `locust -f tests/load/test_scale.py --headless -u 1000 -r 50`
- [ ] T111 [P] Write frontend/tests/performance/page-load.test.ts: Vitest tests using performance.now() to assert /dashboard, /knowledge-base, /agent-inbox pages render within 2000ms with mocked API responses
- [ ] T112 [P] Validate RTL mirroring for all frontend pages: in frontend/tests/components/rtl.test.tsx assert dir="rtl" on document.documentElement when Arabic selected; assert font-family includes "Cairo"; spot-check margin-inline-start computed style on nav and table elements; verify forms and modals mirror correctly
- [ ] T113 Run end-to-end quickstart.md validation: docker-compose -f docker-compose.local.yml up -d → alembic upgrade head → pytest backend/tests/ → npm run test (frontend); confirm all tests pass on clean environment and document any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Requires Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Requires Foundational — needs database, RLS, JWT, storage, Qdrant, ClamAV
- **US2 (Phase 4)**: Requires US1 — needs Tenant, KnowledgeSource, and pipeline running
- **US3 (Phase 5)**: Requires US1 — can run in parallel with US2
- **US4 (Phase 6)**: Requires US2 — needs Conversation model and escalation trigger
- **US5 (Phase 7)**: Requires Foundational — can run in parallel with US3/US4
- **US6 (Phase 8)**: Requires US2 — needs FailedResponse detection in rag.py
- **US7 (Phase 9)**: Requires US2 — needs PurchaseIntent detection in chat.py
- **Polish (Phase 10)**: Requires all desired stories complete

### User Story Dependency Graph

```
Phase 1 (Setup)
  └─> Phase 2 (Foundational)
        ├─> Phase 3 (US1: Onboarding) ────────────────────────┐
        │     └─> Phase 4 (US2: AI Conversation) ──────┐      │
        │           ├─> Phase 6 (US4: Human Handoff)   │      │
        │           ├─> Phase 8 (US6: AI Training)     │      │
        │           └─> Phase 9 (US7: CRM Leads)       │      │
        │     └─> Phase 5 (US3: Knowledge Mgmt) ───────┤      │
        └─> Phase 7 (US5: Billing) ─────────────────────┤      │
Phase 10 (Polish) ←──────────────────────────────────────┴──────┘
```

### Parallel Opportunities

- Phase 1: T003–T008 run in parallel
- Phase 2: T009–T019 (backend) and T020–T023 (frontend) run in parallel across the two groups
- Phase 3: T025–T030 (all tests) run in parallel; T031–T035 (all models) run in parallel; T047–T051 (frontend pages) run in parallel with backend
- Phase 5 (US3) and Phase 7 (US5) can start in parallel once Phase 3 (US1) completes
- Phase 10: T102–T113 are mostly independent, run in parallel

---

## Parallel Example: User Story 1

```bash
# Parallel batch 1: Write all contract tests first (TDD — must fail before implementation)
Task T025: "Contract test POST /auth/register in backend/tests/contract/test_auth_register.py"
Task T026: "Contract test GET /auth/verify in backend/tests/contract/test_auth_verify.py"
Task T027: "Contract test POST /auth/login in backend/tests/contract/test_auth_login.py"
Task T028: "Contract test GET/PUT /workspace in backend/tests/contract/test_workspace.py"
Task T029: "Contract test POST /knowledge/upload in backend/tests/contract/test_knowledge_upload.py"

# Parallel batch 2: Create all models simultaneously
Task T031: "Create backend/src/models/user.py"
Task T032: "Create backend/src/models/tenant.py"
Task T033: "Create backend/src/models/workspace.py"
Task T034: "Create backend/src/models/assistant.py"
Task T035: "Create backend/src/models/knowledge.py"

# Parallel batch 3: Frontend pages (can run alongside backend service work)
Task T047: "Create frontend/src/pages/Register.tsx"
Task T048: "Create frontend/src/pages/EmailVerification.tsx"
Task T049: "Create frontend/src/pages/Onboarding.tsx"
Task T050: "Create frontend/src/pages/AssistantBuilder.tsx"
```

---

## Implementation Strategy

### MVP First (P1 Stories: US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 (Tenant Onboarding)
4. Complete Phase 4: US2 (AI Conversation)
5. **STOP and VALIDATE**: End-to-end test — register, upload knowledge, chat in widget
6. Deploy/demo — this is a working MVP

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 → Tenant can register and upload knowledge
3. US2 → AI chat widget live (MVP!)
4. US3 → Full knowledge management (versioning, rollback, URL scraping)
5. US4 → Human handoff live (escalation + CSAT)
6. US5 → Billing active (Stripe usage metering + alerts)
7. US6 → AI training loop (quality improvement)
8. US7 → CRM leads (revenue capture)
9. Phase 10 → CLI, exports, security hardening, RTL validation

### Parallel Team Strategy

With multiple developers, once Foundational is complete:
- **Dev A**: US1 (Onboarding) → US3 (Knowledge Mgmt) → US6 (AI Training)
- **Dev B**: US2 (AI Conversation) → US4 (Human Handoff) → US7 (CRM)
- **Dev C**: US5 (Billing) → Phase 10 (CLI + exports + security)

---

## Notes

- **[P]** tasks = different files, no shared state dependencies — safe to run in parallel
- **[Story]** label maps each task to a specific user story for traceability
- **TDD is mandatory** — constitution Principle III requires tests written and failing before implementation code
- **RLS coverage** — every new API endpoint must be verified by backend/tests/integration/test_rls_isolation.py (T109)
- **RTL verification** — every frontend page must pass direction toggle test in frontend/tests/components/rtl.test.tsx (T112)
- **Cosine threshold** — read from `assistant.guardrails.context_similarity_threshold`; never hardcode 0.75 in search.py
- **Tenant prefix** — all MinIO paths via `storage.tenant_path()`, all Redis keys via `cache.tenant_key()`; never construct paths inline
- Commit after each completed task or logical group of related tasks
- Stop at each Phase checkpoint to validate the user story independently before advancing
