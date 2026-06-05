# Tasks: MoreClient AI Enterprise Platform

**Input**: Design documents from `specs/001-moreclient-ai-platform/`

**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initial project layout and dependencies config.

- [ ] T001 Create folder structures for `backend/` and `frontend/` per design doc
- [ ] T002 Initialize Python 3.11 environment, poetry dependencies, and FastAPI application in `backend/src/main.py`
- [ ] T003 Initialize React TypeScript boilerplate with Vite and create standard layout container in `frontend/src/main.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be completed before any user story work can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Setup database connection, SQLAlchemy models (with tenant RLS context manager dependency executing `SET LOCAL app.current_tenant_id = :tenant_id`), and Alembic migrations framework in `backend/src/database.py`
- [ ] T005 [P] Setup Redis caching client and rate-limiting keyspace helpers in `backend/src/services/redis.py`
- [ ] T006 [P] Configure Qdrant vector client connection and single shared collection initialization in `backend/src/services/qdrant.py`
- [ ] T007 Configure JWT authentication and session context manager with PostgreSQL RLS variables in `backend/src/api/auth.py`
- [ ] T008 Configure structured logging, custom error handling middleware, and rate-limiting in `backend/src/main.py`

### Security & RBAC Foundations
- [ ] T049 [P] Implement RBAC permission middleware enforcing four roles (Super Admin, Tenant Admin, Agent, Viewer) with permission scope validation on all protected endpoints in `backend/src/api/middleware/rbac.py`
- [ ] T050 [P] Implement role and default permission seeding script for all four roles in `backend/src/models/roles.py`
- [ ] T051 [P] Implement break-glass emergency access endpoint requiring explicit authorization, recorded as an immutable audit event visible to the Tenant Admin in `backend/src/api/auth.py`
- [ ] T052 [P] Configure AES-256 encryption at rest for all stored data, secrets management integration (Vault or AWS Secrets Manager), and encrypted backup configuration in `backend/src/config.py`

### Contract Tests (Constitution Principle III)
- [ ] T059 [P] Create contract test suite for auth endpoints (registration, login, OAuth, token refresh) in `backend/tests/contract/test_auth_contracts.py`
- [ ] T060 [P] Create contract test suite for tenants endpoints (workspace CRUD, branding, region) in `backend/tests/contract/test_tenants_contracts.py`
- [ ] T061 [P] Create contract test suite for knowledge endpoints (upload, URL scraping, Q&A, versioning) in `backend/tests/contract/test_knowledge_contracts.py`
- [ ] T062 [P] Create contract test suite for chat endpoints (session, messages, escalation routing) in `backend/tests/contract/test_chat_contracts.py`
- [ ] T063 [P] Create contract test suite for leads endpoints (auto-create, pipeline stages) in `backend/tests/contract/test_leads_contracts.py`
- [ ] T064 [P] Create contract test suite for billing endpoints (plans, usage metering, webhooks) in `backend/tests/contract/test_billing_contracts.py`
- [ ] T065 [P] Create contract test suite for exports endpoints (conversations, leads, audit log download) in `backend/tests/contract/test_exports_contracts.py`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Tenant Onboarding & First AI Assistant (Priority: P1) 🎯 MVP

**Goal**: Tenant admin registers, verifies account, uploads first document, builds vector index, and tests widget script.

**Independent Test**: Register a new tenant, confirm the database sets up workspace & default assistant, scan & process a clean file, and verify vector storage in Qdrant.

### Tests for User Story 1 (TDD)
- [ ] T009 [P] [US1] Create integration test suite for tenant registration, verification, and workspace configuration in `backend/tests/integration/test_onboarding.py`
- [ ] T010 [P] [US1] Create integration test suite for knowledge source upload and vector store processing in `backend/tests/integration/test_knowledge_upload.py`

### Implementation for User Story 1
- [ ] T011 [US1] Implement tenant signup and email verification token generation in `backend/src/api/auth.py` (authentication and JWT token flow only; workspace provisioning is exclusively handled by T012)
- [ ] T012 [US1] Implement workspace and assistant creation and details updating in `backend/src/api/tenants.py`
- [ ] T013 [P] [US1] Create ClamAV connector for scan streaming of uploaded documents in `backend/src/services/scanner.py` (with local mock fallback when daemon is offline)
- [ ] T014 [US1] Implement file upload route with in-memory virus checking in `backend/src/api/knowledge.py`
- [ ] T015 [US1] Implement PDF/DOCX text extraction, normalization, and chunking in `backend/src/services/extractor.py`
- [ ] T016 [US1] Implement text embedding generation (pluggable OpenAI/Gemini) and index insertion into the shared collection in `backend/src/services/vectorizer.py`
- [ ] T017 [US1] Implement React onboarding page, verification panel, profile form, and file upload wizard in `frontend/src/pages/Onboarding.tsx`
- [ ] T045 [US1] Implement Google OAuth2 callback handler, token exchange, and account linking (with mock bypass mode for local development) in `backend/src/api/auth.py`
- [ ] T054 [US1] Implement guardrails configuration API (restrict external knowledge toggle — default on, competitor blocking, configurable escalation rules) in `backend/src/api/assistants.py`
- [ ] T055 [US1] Build guardrails configuration UI panel with toggles for external knowledge restriction, competitor blocking, and escalation rules in `frontend/src/pages/AssistantBuilder.tsx`
- [ ] T056 [US1] Implement tenant data residency region selection (GCC vs Global metadata storage) at signup in `backend/src/api/tenants.py` (infrastructure region routing omitted per user request)

**Checkpoint**: User Story 1 is functional. New tenants can onboard and index knowledge.

---

## Phase 4: User Story 2 - End Customer AI Conversation (Priority: P1)

**Goal**: Customer chats with widget, gets hybrid search RAG answer, escalates to live support on low confidence or complaints.

**Independent Test**: Submit a message to the assistant widget, verify RAG retrieves the correct knowledge source via hybrid search, and verify auto-escalation when querying with complain keywords.

### Tests for User Story 2 (TDD)
- [ ] T018 [P] [US2] Create unit test suite for RAG retrieval and reciprocal rank fusion search in `backend/tests/unit/test_rag.py`
- [ ] T019 [P] [US2] Create integration test suite for chat sessions, intent detection, and escalation routing in `backend/tests/integration/test_chat.py`

### Implementation for User Story 2
- [ ] T020 [US2] Implement hybrid search (PostgreSQL full-text search + Qdrant cosine search with `tenant_id` payload filtering) in `backend/src/services/search.py` (with sentence-transformers re-ranking and mock fallback)
- [ ] T021 [US2] Implement message intent detection, sentiment, and query rewriting in `backend/src/services/intelligence.py`
- [ ] T022 [US2] Implement LLM prompt builder, context compressor, and RAG generator (pluggable OpenAI/Gemini support) in `backend/src/services/rag.py`
- [ ] T023 [US2] Implement client chat endpoint and chat sessions history in `backend/src/api/chat.py`
- [ ] T024 [US2] Build the embeddable chat widget script and customizable themes in `frontend/src/components/Widget.tsx` and `frontend/src/components/Widget.css`

**Checkpoint**: User Story 2 is functional. RAG conversations and escalation logic are active.

---

## Phase 5: User Story 3 - Knowledge Base Management (Priority: P2)

**Goal**: Admin scans URLs, uploads spreadsheets, updates knowledge versions, and rolls back to older active versions.

**Independent Test**: Trigger a site scrape, confirm new version is generated, update active version flags, and trigger rollback to verify older knowledge index.

### Tests for User Story 3 (TDD)
- [ ] T025 [P] [US3] Create integration test suite for knowledge versions and active index rollbacks in `backend/tests/integration/test_versioning.py`

### Implementation for User Story 3
- [ ] T026 [US3] Implement URL scraping using HTTP client and HTML parsing in `backend/src/services/scraper.py`
- [ ] T027 [US3] Implement knowledge versioning snapshots and DB version switches in `backend/src/services/versioning.py`
- [ ] T028 [US3] Implement Knowledge Base tab showing uploads list, URL forms, version log, and rollback buttons in `frontend/src/pages/KnowledgeBase.tsx`
- [ ] T057 [US3] Add manual Q&A entry form (question + answer input) and API endpoint to `backend/src/api/knowledge.py`; extend `frontend/src/pages/KnowledgeBase.tsx` (T028) with a Q&A tab

**Checkpoint**: User Story 3 is functional. Scraped URLs, manual Q&A entry, and rollback points are live.

---

## Phase 6: User Story 4 - Human Agent Handling Live Escalations (Priority: P2)

**Goal**: Support agent toggles online, receives escalated chats in a queue, chats in real time, and resolves tickets.

**Independent Test**: Trigger escalation from client widget, verify agent inbox receives notification, claim chat, exchange messages, and close chat.

### Tests for User Story 4 (TDD)
- [ ] T029 [P] [US4] Create integration test suite for agent queue routing and status toggling in `backend/tests/integration/test_agents.py`

### Implementation for User Story 4
- [ ] T030 [US4] Implement agent assignment routing strategies — Round Robin, Least Busy, and Skill-Based Routing (match agent skill tags to conversation intent/topic) — in `backend/src/services/agent_manager.py`
- [ ] T031 [US4] Implement agent and customer bidirectional real-time WebSockets communication endpoint in `backend/src/api/sockets.py`
- [ ] T032 [US4] Implement agent workspace dashboard view with chat list, transcript history, and reply input in `frontend/src/pages/AgentInbox.tsx`

**Checkpoint**: User Story 4 is functional. Real-time agent takeover and agent chat queues work.

---

## Phase 7: User Story 5 - Subscription & Usage Billing (Priority: P2)

**Goal**: Stripe usage metering, billing metrics in dashboard, overage charge calculations at billing end.

**Independent Test**: Exceed message limits, verify soft allow lets messages pass, verify Stripe billing records usage, and verify limit warning notifications trigger.

### Tests for User Story 5 (TDD)
- [ ] T033 [P] [US5] Create integration test suite for Stripe webhooks and limit alerts in `backend/tests/integration/test_billing.py`

### Implementation for User Story 5
- [ ] T034 [US5] Implement Stripe usage sync worker, webhook endpoints, and usage limit indicators in `backend/src/services/billing.py` and `backend/src/api/webhooks.py` (with simulated mock billing mode fallback)
- [ ] T035 [US5] Implement Billing Dashboard containing usage progress bars, plans grid, and invoices list in `frontend/src/pages/Billing.tsx`

**Checkpoint**: User Story 5 is functional. Stripe metered billing is fully automated.

---

## Phase 8: User Story 6 - AI Training Center (Priority: P3)

**Goal**: View downvoted responses, train AI with custom Q&As, and flag hallucination sources.

**Independent Test**: Downvote a message, locate it in Training page, submit correct QA answer, and verify it updates the vector index.

### Tests for User Story 6 (TDD)
- [ ] T036 [P] [US6] Create integration test suite for response correction indexing in `backend/tests/integration/test_training.py`

### Implementation for User Story 6
- [ ] T037 [US6] Implement training endpoints to retrieve downvoted logs and insert trained QA vectors in `backend/src/api/training.py`
- [ ] T038 [US6] Implement Training page showing downvoted log lists, correction forms, and index status in `frontend/src/pages/TrainingCenter.tsx`

**Checkpoint**: User Story 6 is functional. Admin can refine AI answers interactively.

---

## Phase 9: User Story 7 - CRM Lead Pipeline (Priority: P3)

**Goal**: Detect purchase intent from customer chat, auto-generate CRM lead card, and track pipeline stages.

**Independent Test**: Send "I want to buy the enterprise tier" in widget, verify a lead card is created, and update pipeline stage.

### Tests for User Story 7 (TDD)
- [ ] T039 [P] [US7] Create integration test suite for lead extraction and stage tracking in `backend/tests/integration/test_leads.py`

### Implementation for User Story 7
- [ ] T040 [US7] Implement lead auto-generation rules and CRM pipeline state routes in `backend/src/api/leads.py`
- [ ] T041 [US7] Implement Kanban lead pipeline board with stage update triggers in `frontend/src/pages/Leads.tsx`

**Checkpoint**: User Story 7 is functional. Auto lead creation from chat is active.

---

## Phase 10: Cross-Cutting Platform Services

**Purpose**: Notifications, data exports, CLI interface, and retrieval analytics — features spanning all user stories.

- [ ] T046 Implement notifications service delivering email and in-app alerts for 5 events: complaint received, lead created, subscription expiring, document processing failed, agent assigned — in `backend/src/services/notifications.py`
- [ ] T047 [P] Implement in-app notification storage, delivery endpoint, and notification bell UI component in `backend/src/api/notifications.py` and `frontend/src/components/NotificationBell.tsx`
- [ ] T048 Implement tenant-scoped data export endpoints for conversation history, lead records, and audit logs in CSV and JSON format in `backend/src/api/exports.py`
- [ ] T053 Implement CLI administration interface exposing tenant management, billing administration, and system health commands in `backend/src/cli.py`
- [ ] T058 Implement per-tenant retrieval accuracy tracking (fraction of queries surfacing the correct knowledge chunk), metrics storage endpoint, and analytics dashboard page in `backend/src/api/analytics.py` and `frontend/src/pages/Analytics.tsx`

**Checkpoint**: Cross-cutting platform services live — notifications, exports, CLI, and retrieval analytics.

---

## Phase 11: Polish, Internationalization & Validation

**Purpose**: Multi-language support, audit logs, load testing, and performance validation.

- [ ] T042 Setup English/Arabic translation dictionary hook, direction attributes (RTL mirroring), and font loading — Outfit for LTR/English, Cairo for Arabic/RTL — with CSS token configuration in `frontend/src/hooks/useLocale.ts` and `frontend/src/index.css`
- [ ] T043 Implement audit log middleware capturing all 6 event types — (1) login/logout, (2) file upload/delete, (3) billing changes, (4) user creation/deletion, (5) permission changes, (6) break-glass access — with 365-day retention enforcement and immutability guarantees in `backend/src/services/audit.py`
- [ ] T066 Implement load testing suite validating platform supports 10,000 simultaneous tenant workspaces and 1,000,000 conversations/month without degradation, and 100 concurrent agent sessions in `backend/tests/load/test_scale.py`
- [ ] T067 Validate backup and recovery procedures: script a full backup, simulate failure, restore, and verify RTO ≤ 1 hour and RPO ≤ 15 minutes
- [ ] T068 Run performance audit against all admin dashboard pages to verify page load times under 2 seconds (SC-004); document results in `frontend/tests/performance/` and remediate failures
- [ ] T044 Run docker compose environment and run full verification against `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. Blocks all user stories. Includes RBAC, encryption, and contract test suites.
- **User Stories (Phase 3–9)**: All depend on Foundational completion.
  - Recommended order: US1 & US2 (P1 core loops) → US3, US4, US5 (P2 operations) → US6 & US7 (P3 optimization).
- **Cross-Cutting Services (Phase 10)**: Depends on user story implementations (T046–T048 require notification triggers from billing, chat, and knowledge phases).
- **Polish & Validation (Phase 11)**: Depends on all user stories and cross-cutting services being complete.

---

## Parallel Opportunities

- All Setup tasks (T001 to T003) can run in parallel.
- Foundational tasks T005, T006, T049, T050, T051, T052 can run in parallel with database schema setup.
- All contract test suites (T059–T065) can be written in parallel during Phase 2.
- TDD test suites (T009/T010, T018/T019, T025, T029, T033, T036, T039) can be written concurrently.
- Once Foundation (Phase 2) is complete, different developers can implement stories in parallel (e.g., Dev A working on Onboarding US1, Dev B working on Conversational Core US2).
- Phase 10 tasks T046–T048, T053, T058 can run in parallel once the user story phases they depend on are complete.

---

## Implementation Strategy

### MVP First (User Stories 1 & 2)
1. Complete Setup (Phase 1)
2. Complete Foundational (Phase 2)
3. Complete User Story 1 (Phase 3)
4. Complete User Story 2 (Phase 4)
5. **STOP and VALIDATE**: Confirm that a tenant can register, upload a document, and get relevant AI answers in the widget.

### Incremental Delivery
1. Release MVP (US1 + US2).
2. Deliver US3 (Knowledge Management) & US4 (Human Agent inbox).
3. Deliver US5 (Metered billing) & US6 (AI Training Center).
4. Deliver US7 (CRM Lead extraction).
5. Deliver Cross-Cutting Services (Phase 10): notifications, exports, CLI, analytics.
6. Polish & Validation (Phase 11): i18n, audit logs, load testing, performance validation.
