# Tasks: Chat Engine

**Branch**: `004-chat-engine` | **Feature**: Phase 3 — Chat Engine (Week 5)

**Input**: Design documents from `specs/004-chat-engine/`

**Documents loaded**: plan.md, spec.md, research.md, data-model.md, contracts/rest-chat.md, contracts/ws-chat.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to — [US1], [US2], [US3]
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend project configuration and install new dependencies required by the Chat Engine. Must complete before any Phase 2 work.

- [ ] T001 Add `openai>=1.30.0` to `backend/requirements.txt`, then rebuild and restart the backend container: `docker compose build backend && docker compose up -d backend`
- [ ] T002 [P] Add LLM configuration fields to `backend/app/core/config.py`: `LLM_PRIMARY_MODEL`, `LLM_FALLBACK_MODEL`, `LLM_TIMEOUT_SECONDS` (int, default 30), `RAG_TOP_K` (int, default 5), `HANDOFF_KEYWORDS` (comma-separated string)
- [ ] T003 [P] Update `.env` and `.env.example` with the new LLM + handoff env vars documented in `specs/004-chat-engine/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema changes, RLS policies, and shared Pydantic schemas that all user stories depend on. **No user story work can begin until this phase is complete.**

**⚠️ CRITICAL**: This phase blocks all story phases below.

- [ ] T004 Write Alembic migration `backend/alembic/versions/20260606_001_add_chat_engine_schema.py`:
  - Add `title VARCHAR(255) NULL` column to `conversations`
  - Alter `status` column: change default to `'bot'`, add `CHECK (status IN ('bot', 'handoff', 'closed'))`
  - Add index `idx_conversations_status` on `(tenant_id, status)`
  - `ALTER TABLE conversations ENABLE ROW LEVEL SECURITY`
  - `ALTER TABLE messages ENABLE ROW LEVEL SECURITY`
  - Create `FOR ALL` RLS policy on `conversations` and `messages` using `current_setting('app.current_tenant_id')`
- [ ] T005 Apply the migration: run `docker compose exec backend alembic upgrade head` and verify it succeeds without errors
- [ ] T006 [P] Update `backend/app/models/conversation.py`:
  - Add `title = Column(String(255), nullable=True)` field
  - Update `status` column default to `"bot"` and add `CheckConstraint` with allowed values `('bot', 'handoff', 'closed')`
  - Add `idx_conversations_status` index to `__table_args__`
- [ ] T007 [P] Create `backend/app/schemas/chat.py` with Pydantic models:
  - `ChatRequest(assistant_id: UUID, conversation_id: UUID | None, message: str)` with `max_length=4000` validator
  - `ChatResponse(conversation_id, message_id, role, content, tokens_used, sources, model_used)`
  - `SourceReference(document_id, chunk_text, score)`
  - `WSIncomingMessage(type: Literal["message","ping"], conversation_id, content)`
  - `WSTokenEvent(type="token", delta: str)`
  - `WSDoneEvent(type="done", conversation_id, message_id, tokens_used, model_used, sources)`
  - `WSErrorEvent(type="error", code: str, detail: str)`
  - `WSHandoffEvent(type="handoff", conversation_id, detail: str)`
- [ ] T008 [P] Extend `backend/app/services/rag/chroma_client.py` with an async `retrieve(tenant_id, query_text, top_k) -> list[SourceReference]` method that queries the `tenant_{uuid}` collection and returns the top-k chunks with scores
- [ ] T009 [P] Create stub `backend/app/services/handoff_service.py` with:
  - `is_handoff_trigger(message: str) -> bool` returning `False` always (no-op stub so it can be imported by T012's REST endpoint without error; full implementation done in Phase 5 T024)
  - `async trigger_handoff(tenant_id, conversation_id, assistant_id)` as a `pass` stub

**Checkpoint**: Migration applied, models updated, schemas defined, RAG retrieval method available, handoff_service stub importable. User story implementation can now begin.

---

## Phase 3: User Story 1 — Conversational RAG Interface (Priority: P1) 🎯 MVP

**Goal**: Deliver the core synchronous REST chat endpoint that retrieves context from the tenant's knowledge base, calls the LLM, persists both messages, and returns a grounded response.

**Independent Test**: Send `POST /api/v1/chat` with a valid JWT, an assistant that has ingested a unique PDF, and a question about that PDF content. Verify the response `content` references information from the PDF and `sources` contains the matching chunk. Verify zero cross-tenant leakage by repeating with a different tenant's JWT and confirming no results from the first tenant's documents appear.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Create `backend/app/services/quota_service.py`:
  - `async check_quota(tenant_id, required_tokens=0) -> bool` — reads Redis key `quota:{tenant_id}:{YYYYMMDDHH}` and compares to the tenant's hourly limit (read from `tenants.token_quota_hourly` DB column, falling back to `config.DEFAULT_HOURLY_TOKEN_QUOTA`); returns `False` if at or above limit
  - `async consume_quota(tenant_id, tokens_used: int)` — atomically `INCRBY` the Redis quota key and sets a 2-hour TTL
  - `async get_remaining_quota(tenant_id) -> int` — returns remaining budget for current hour
- [ ] T011 [P] [US1] Create `backend/app/services/llm_service.py`:
  - `async complete(messages, model, stream=False)` — calls `AsyncOpenAI` with the given model; on `APIStatusError` (429/503) or `asyncio.TimeoutError`, raises `LLMUnavailableError`
  - `async complete_with_fallback(messages, stream=False)` — tries `LLM_PRIMARY_MODEL` first; on failure, tries `LLM_FALLBACK_MODEL`; on double failure raises `LLMUnavailableError`
  - Define `LLMUnavailableError(Exception)` custom exception
- [ ] T012 [US1] Create `backend/app/services/chat_service.py` with `async chat(tenant_id, assistant_id, conversation_id, user_content) -> ChatResponse`:
  1. Validate assistant belongs to tenant (DB query with RLS context)
  2. Create or load conversation record
  3. Pre-flight `quota_service.check_quota(tenant_id)`; raise `QuotaExceededError` if failed
  4. Retrieve history: last 10 messages from `messages` table ordered by `created_at DESC` limit 10, reversed
  5. Retrieve context: `chroma_client.retrieve(tenant_id, user_content, top_k=RAG_TOP_K)`; if result list is empty, prepend a system note: `"No relevant information was found in the knowledge base. Politely inform the user."`
  6. Build LLM messages array: system prompt + context chunks (or no-context note) + history + user message
  7. Call `llm_service.complete_with_fallback(messages, stream=False)`
  8. Persist user `Message` record (role="user") with `tenant_id` and `conversation_id`
  9. Persist assistant `Message` record (role="assistant") with `tokens_used`, `sources`, `latency_ms`
  10. Call `quota_service.consume_quota(tenant_id, tokens_used)`
  11. Return `ChatResponse`
- [ ] T013 [US1] Create `backend/app/api/v1/endpoints/chat.py`:
  - `POST /` route mapped to `POST /api/v1/chat` via the router
  - Validate JWT + `X-Tenant-ID` header via existing auth dependency
  - Parse `ChatRequest` body
  - Check for handoff keywords before calling `chat_service` (delegate to `handoff_service.is_handoff_trigger` — stub returns `False` until Phase 5)
  - Call `chat_service.chat(...)` and return `ChatResponse`
  - Handle `QuotaExceededError` → 429, `AssistantNotFoundError` → 404, `LLMUnavailableError` → 503, `ConversationInHandoffError` → 409
  - Add `no-store` Cache-Control header to response to prevent upstream caching of sensitive conversation data
- [ ] T014 [US1] Register the new chat router in `backend/app/api/v1/router.py`: `router.include_router(chat_router, prefix="/chat", tags=["chat"])`
- [ ] T015 [P] [US1] Create Next.js chat page at `frontend/app/dashboard/assistants/[id]/chat/page.tsx`:
  - Server component that renders the `ChatWindow` client component
  - Pass `assistantId` from route params, `tenantId` from session
- [ ] T016 [P] [US1] Create `frontend/lib/chat-api.ts` with:
  - `sendMessage(assistantId, conversationId, message): Promise<ChatResponse>` — calls `POST /api/v1/chat`
  - `createWebSocket(assistantId, tenantId, token): WebSocket` — builds WS URL with query params
- [ ] T017 [P] [US1] Create `frontend/components/chat/MessageBubble.tsx` — renders a single message with role-based styling (`user` right-aligned, `assistant` left-aligned with source footnotes)
- [ ] T018 [US1] Create `frontend/components/chat/ChatWindow.tsx` — client component with:
  - Message list using `MessageBubble`
  - Text input + send button
  - Calls `chat-api.sendMessage` on submit and appends response to message list
  - Shows loading state while awaiting response

**Checkpoint**: `POST /api/v1/chat` returns grounded responses for tenant documents (including polite fallback when no relevant context is found). Chat UI renders and is interactive. User Story 1 — including Acceptance Scenario 2 — is fully functional and independently testable.

---

## Phase 4: User Story 2 — Real-Time Response Streaming (Priority: P2)

**Goal**: Add the WebSocket endpoint that streams LLM response tokens in real-time, with graceful handling of mid-stream disconnects and quota breaches.

**Independent Test**: Connect via WebSocket with `websocat` (see `quickstart.md`). Send a `{"type":"message",...}` event and observe a stream of `{"type":"token",...}` events arriving progressively, followed by a final `{"type":"done",...}` event. Disconnect mid-stream and verify the partial response is persisted in the `messages` table with `[response truncated]` suffix.

### Implementation for User Story 2

- [ ] T019 [US2] Extend `backend/app/services/chat_service.py` with `async stream_chat(tenant_id, assistant_id, conversation_id, user_content) -> AsyncGenerator`:
  - Steps 1–6 same as `chat()` (validate, quota check, history, RAG retrieval + no-context fallback, build messages)
  - Call `llm_service.complete_with_fallback(messages, stream=True)` to get an `AsyncStream`
  - Yield each `ChatCompletionChunk.choices[0].delta.content` token via an `async for` loop
  - After each token, check running token count; if quota exceeded, yield a `quota_exceeded` sentinel and break
  - On loop completion, persist user + assistant messages; yield a `done` sentinel with final metadata
  - On `asyncio.CancelledError` (client disconnect), persist partial response with `[response truncated]`
- [ ] T020 [US2] Create `backend/app/api/v1/endpoints/ws_chat.py`:
  - `WebSocket` route at `GET /ws/chat` (registered at `/api/v1/ws/chat`)
  - On connect: extract `token`, `tenant_id`, `assistant_id` from query params; validate JWT; close with `4001`/`4003` on failure
  - Message loop: receive JSON, dispatch on `type`:
    - `"ping"` → send `{"type":"pong"}`
    - `"message"` → call `chat_service.stream_chat(...)`, iterate async generator, send `token` events, handle `quota_exceeded` sentinel → send `WSErrorEvent`, handle `done` sentinel → send `WSDoneEvent`
  - On `WebSocketDisconnect` mid-stream: cancel generator, partial message already persisted by service
- [ ] T021 [US2] Register the WebSocket router in `backend/app/api/v1/router.py`: `router.include_router(ws_router, prefix="/ws", tags=["chat-ws"])`
- [ ] T022 [P] [US2] Create `frontend/components/chat/StreamingDot.tsx` — animated three-dot typing indicator shown while a WebSocket stream is in progress
- [ ] T023 [US2] Update `frontend/components/chat/ChatWindow.tsx` to use WebSocket as the primary transport:
  - On mount, call `chat-api.createWebSocket(...)` and store the connection
  - On send: transmit `{"type":"message",...}` JSON frame
  - On `token` event: append delta to the in-progress assistant bubble in state
  - On `done` event: finalise the bubble, hide `StreamingDot`
  - On `error` event: show inline error message in chat
  - On `handoff` event: render `HandoffBanner`, disable input
  - Fall back to REST (`sendMessage`) if WebSocket connection fails to open
- [ ] T024 [P] [US2] Create `frontend/components/chat/HandoffBanner.tsx` — notification banner displayed when conversation enters handoff state, explaining that a human agent has been notified

**Checkpoint**: WebSocket streaming delivers tokens in real-time. Quota mid-stream breach sends an error event and stops cleanly. Disconnects persist partial messages. User Stories 1 and 2 are both independently testable.

---

## Phase 5: User Story 3 — Human Handoff (Priority: P3)

**Goal**: Implement deterministic keyword/regex handoff detection that transitions conversation status to `handoff`, suspends AI responses, and publishes a real-time event via Redis Pub/Sub.

**Independent Test**: Send a message containing a handoff keyword (e.g., `"speak to human"`) to `POST /api/v1/chat`. Verify HTTP 409 response, `conversations.status = 'handoff'` in the DB, and that a subscriber on Redis channel `handoff:{tenant_id}` receives the JSON event within 100ms. Subsequent messages to the same conversation must not trigger an LLM call.

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement full `backend/app/services/handoff_service.py` (replacing the Phase 2 stub):
  - `is_handoff_trigger(message: str) -> bool` — normalises to lowercase, checks against compiled regex from `config.HANDOFF_KEYWORDS` (split by comma, stripped, regex-escaped, joined with `|`)
  - `async trigger_handoff(tenant_id, conversation_id, assistant_id)`:
    1. Update `conversations.status = 'handoff'` for the given `conversation_id` (with RLS context)
    2. Publish to Redis channel `handoff:{tenant_id}`: `{"conversation_id": "...", "event": "handoff_requested", "assistant_id": "...", "ts": "<ISO-8601>"}`
    3. Return `True`
- [ ] T026 [US3] Integrate handoff detection into `backend/app/api/v1/endpoints/chat.py`:
  - Before calling `chat_service.chat(...)`, call `handoff_service.is_handoff_trigger(request.message)`
  - If `True`, call `handoff_service.trigger_handoff(...)` and raise `ConversationInHandoffError` → 409
  - Also check `conversation.status == 'handoff'` at the start of each request and reject with 409 if already in handoff
- [ ] T027 [US3] Integrate handoff detection into `backend/app/api/v1/endpoints/ws_chat.py`:
  - In the `"message"` handler, call `handoff_service.is_handoff_trigger(content)` before starting the stream
  - If triggered, call `handoff_service.trigger_handoff(...)`, send `WSHandoffEvent`, and stop further LLM processing for that conversation
  - Check `conversation.status` on each message loop iteration; if `handoff`, send `WSHandoffEvent` and skip LLM

**Checkpoint**: Handoff keywords deterministically transition conversations to handoff state. AI responses are suspended. Redis Pub/Sub event is published. All three user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Logging, error boundary hardening, fallback edge cases, and developer-experience polish across all stories.

- [ ] T028 [P] Add structured logging in `backend/app/services/chat_service.py`: log `tenant_id`, `conversation_id`, `model_used`, `tokens_used`, and `latency_ms` at `INFO` level for every successful chat turn; log `ERROR` with full exception context on LLM failures
- [ ] T029 [P] Add structured logging in `backend/app/services/handoff_service.py`: log handoff triggers with `tenant_id`, `conversation_id`, and matched keyword at `INFO` level
- [ ] T030 [P] Validate that the `openai` SDK `Timeout` configuration is set from `config.LLM_TIMEOUT_SECONDS` in `backend/app/services/llm_service.py` and that `AsyncOpenAI(timeout=...)` is correctly initialised
- [ ] T031 Run the full quickstart validation from `specs/004-chat-engine/quickstart.md` — REST endpoint, WebSocket streaming, handoff trigger — and confirm all steps pass end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **User Story Phases (3, 4, 5)**: All depend on Phase 2 completion
  - Can proceed sequentially in priority order (P1 → P2 → P3) with a single developer
  - US1 and US2 share `chat_service.py` — implement US1's `chat()` first, then extend with US2's `stream_chat()`
  - US3 (`handoff_service.py`) is fully independent and can be developed in parallel with US2
- **Polish (Phase 6)**: Depends on all story phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2. No dependency on US2 or US3. ← **Start here for MVP**
- **User Story 2 (P2)**: Starts after Phase 2. Extends `chat_service.py` (depends on US1's T012 being done first). Frontend WebSocket work (T022–T024) can start in parallel with backend T019–T021.
- **User Story 3 (P3)**: Starts after Phase 2. Fully independent of US2; only requires the endpoint hooks in T026/T027 which depend on US1's T013 and US2's T020.

### Within Each User Story

- Backend models/schemas (T006–T009) before services
- Services before endpoints
- Endpoints before frontend integration
- Frontend components can be built in parallel with backend services (different files)

### Parallel Opportunities

| Group | Parallelisable Tasks |
|---|---|
| Phase 1 | T001, T002, T003 — all independent |
| Phase 2 | T007, T008, T009 — independent of migration (T004/T005) |
| US1 backend | T010 (quota_service), T011 (llm_service) — parallel with each other, both needed by T012 |
| US1 frontend | T015, T016, T017 — parallel with each other and with T012/T013 |
| US2 frontend | T022, T024 — parallel with backend T019/T020 |
| US3 | T025 (handoff_service full impl) — parallel with US2 backend work |
| Phase 6 | T028, T029, T030, T031 — all fully parallel |

---

## Parallel Example: User Story 1

```
# Backend (Developer A):
T010 — quota_service.py
T011 — llm_service.py
  ↓ (both complete)
T012 — chat_service.py
T013 — chat.py endpoint
T014 — register router

# Frontend (Developer B, concurrent with backend):
T016 — chat-api.ts
T017 — MessageBubble.tsx
T015 — chat/page.tsx
T018 — ChatWindow.tsx (needs T016 + T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1**: Setup (T001–T003)
2. Complete **Phase 2**: Foundational (T004–T009) — **critical blocker**
3. Complete **Phase 3**: User Story 1 (T010–T018)
4. **STOP and VALIDATE**: Test `POST /api/v1/chat` end-to-end with a real assistant and document
5. Demo the chat UI — grounded responses, source footnotes, zero cross-tenant leakage

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. **US1** → REST chat + basic UI → **MVP Demo** ✅
3. **US2** → WebSocket streaming + animated UI → richer UX
4. **US3** → Handoff protocol → production-ready support workflow
5. **Phase 6** → Logging, hardening, full quickstart validation

### Parallel Team Strategy

With 2–3 developers:

1. All complete Phase 1 + Phase 2 together
2. Once Foundational phase is done:
   - **Dev A**: US1 backend (T010–T014)
   - **Dev B**: US1 frontend (T015–T018) + US2 frontend (T022–T024)
   - **Dev C**: US3 (T025–T027) once T013/T020 are complete
3. Everyone converges on Phase 6 polish

---

## Notes

- `[P]` tasks operate on different files with no dependency on incomplete sibling tasks — safe to parallelize
- `[US1]`, `[US2]`, `[US3]` labels map directly to the user stories in `specs/004-chat-engine/spec.md`
- All database operations in services must run within the existing `TenantMiddleware` context that sets `SET LOCAL app.current_tenant_id`
- The `openai` SDK must be added to `requirements.txt` (T001) before any LLM service code can be imported
- Commit after each Phase checkpoint to maintain a clean, demo-able git history
- Validate the RLS migration (T004/T005) in a transaction with a rollback test before merging to main
