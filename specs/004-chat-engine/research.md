# Research: Chat Engine

**Branch**: `004-chat-engine` | **Date**: 2026-06-06

## Phase 0 Findings

All technical unknowns identified during planning have been resolved below.

---

### 1. FastAPI WebSocket Authentication

**Decision**: Authenticate WebSocket connections via a short-lived `token` query parameter on the initial handshake URL (e.g., `wss://host/v1/ws/chat?token=<JWT>`).

**Rationale**: The browser WebSocket API does not support custom HTTP headers during the handshake. Passing the JWT as a URL query parameter on first connect is the accepted FastAPI/Starlette pattern. The token is validated immediately after the connection is accepted; if invalid, the socket is closed with code 4001.

**Alternatives considered**:
- First-message auth frame: Adds extra round-trip before the chat can start; rejected.
- Cookie-based auth: Viable but requires `SameSite=None; Secure` cookies and cross-origin complexity with the subdomain architecture; rejected for simplicity.

---

### 2. LLM Client Library & Streaming Pattern

**Decision**: Use the official `openai` Python SDK (>=1.0) with `AsyncOpenAI` client. For streaming, use `client.chat.completions.create(..., stream=True)` and iterate the `AsyncStream[ChatCompletionChunk]`.

**Rationale**: The `openai` SDK v1+ is async-native, supports streaming via async generators, and provides usage statistics (prompt/completion tokens) on the final chunk. It is also compatible with many hosted inference endpoints that mirror the OpenAI API surface (e.g., Azure OpenAI, Groq, Together AI).

**Alternatives considered**:
- `httpx` raw streaming: More control but duplicates SDK logic; rejected.
- LangChain: Too heavy a dependency for focused RAG retrieval; rejected.

---

### 3. Primary/Fallback Model Strategy

**Decision**: Configure two model identifiers in `core/config.py`: `LLM_PRIMARY_MODEL` (e.g., `gpt-4o`) and `LLM_FALLBACK_MODEL` (e.g., `gpt-4o-mini`). `llm_service.py` attempts the primary model first; on `openai.APIStatusError` (HTTP 429, 503) or `TimeoutError`, it retries once with the fallback model. If both fail, a `LLMUnavailableError` is raised and surfaced to the caller.

**Rationale**: Both models share the same API key and endpoint, so no additional credentials are needed. GPT-4o-mini has near-identical latency characteristics but lower quality — acceptable for a graceful degradation scenario.

**Alternatives considered**:
- Multi-provider fallback (Anthropic, Cohere): Requires separate keys, SDKs, and token counting logic; rejected per clarification Q2.

---

### 4. RAG Retrieval Strategy

**Decision**: For each user query, embed the query text (using the same embedding model as ingestion), then query ChromaDB for the top-5 semantically similar chunks from `tenant_{uuid}` collection. Retrieved chunks are injected into the system prompt as context blocks.

**Rationale**: Top-5 chunks strike a balance between context richness and prompt length. The embedding model must match the one used during ingestion to ensure meaningful similarity scores.

**Alternatives considered**:
- BM25 keyword retrieval hybrid: Improves recall for exact-match queries; deferred to a future enhancement.
- Top-3 / Top-10: Top-5 is a widely validated default; configurable via `RAG_TOP_K` env var.

---

### 5. Conversation Context Window

**Decision**: For each chat turn, retrieve the last 10 messages from the `messages` table (ordered by `created_at DESC`, limited to 10, then reversed for chronological order). These are prepended to the LLM messages array as the conversation history.

**Rationale**: Per clarification Q3. A fixed count is predictable, avoids dynamic token estimation, and keeps implementation simple. At ~200 tokens/message average, 10 messages ≈ 2,000 tokens, well within GPT-4o's 128k context.

**Alternatives considered**:
- Dynamic sliding token window: Better for very long conversations but requires per-model token counting; deferred.

---

### 6. Quota Enforcement Pattern

**Decision**: Use Redis `INCRBY` + `EXPIRE` with a 1-hour rolling window key `quota:{tenant_id}:{hour}`. Pre-flight check: if current count ≥ `plan_token_limit`, reject with HTTP 429 before calling LLM. Post-call: `INCRBY` by actual tokens consumed. Mid-stream breach: after each streamed chunk, check running token count against limit; if exceeded, break the stream loop and send a `{"type":"quota_exceeded"}` event.

**Rationale**: Redis atomic `INCRBY` is safe under concurrency. The pre-flight check prevents runaway costs; the mid-stream check prevents over-shooting the limit during long generations.

**Alternatives considered**:
- PostgreSQL-based quota: Too slow for per-chunk checks under streaming; rejected.

---

### 7. Human Handoff Pub/Sub Channel

**Decision**: Publish handoff events to a Redis channel named `handoff:{tenant_id}`. The message payload is a JSON object: `{"conversation_id": "...", "event": "handoff_requested", "ts": "..."}`. Dashboard consumers subscribe to their tenant's channel to receive real-time notifications.

**Rationale**: Redis Pub/Sub is already a project dependency and is the simplest broadcast mechanism. Channel names scoped to `tenant_id` ensure no cross-tenant message leakage.

**Alternatives considered**:
- Server-Sent Events (SSE) from a backend endpoint: Requires long-polling connections per agent; Redis Pub/Sub scales better.
- WebSocket broadcast: More complex connection management; Redis Pub/Sub decouples the subscriber from the API.

---

### 8. Mid-Stream Partial Message Persistence

**Decision**: On WebSocket disconnect or quota breach mid-stream, persist the partially accumulated content with `role="assistant"` and append `" [response truncated]"` to the content field. `tokens_used` is set to however many tokens had been received before truncation.

**Rationale**: Preserving partial responses allows conversation history to remain useful for debugging and UX continuity. The truncation marker makes it clear the response was incomplete.

---

### 9. Alembic Migration Requirements

**Decision**: The migration must:
1. Add `title` column (VARCHAR 255, nullable) to `conversations`.
2. Change `status` column default from `"active"` to `"bot"` and add allowed values check constraint (`status IN ('bot', 'handoff', 'closed')`).
3. Enable RLS on `conversations` and `messages` (if not already enabled by a prior migration).
4. Define `FOR ALL` RLS policy using `current_setting('app.current_tenant_id')` on both tables.

**Rationale**: The spec defines `status` as `bot | handoff` rather than the existing `active`. The migration aligns the schema with the feature spec while preserving backward compatibility via the `closed` catch-all value.

---

### 10. Frontend Chat Transport Decision

**Decision**: Use WebSocket as the primary transport for all chat interactions (both streaming and non-streaming responses). The REST endpoint (`POST /v1/chat`) serves as a fallback for environments where WebSocket is unavailable (e.g., some corporate proxies).

**Rationale**: A single UI code path against the WebSocket endpoint simplifies the frontend; the complete (non-streamed) message is still persisted server-side regardless of transport. The REST endpoint is available as a documented fallback.
