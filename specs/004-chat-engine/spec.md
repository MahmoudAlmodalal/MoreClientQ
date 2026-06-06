# Feature Specification: Chat Engine

**Feature Branch**: `004-chat-engine`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "Phase 3 — Chat Engine (Week 5)"

## Clarifications

### Session 2026-06-06

- Q: How should the system detect the user's intent to trigger a human handoff? → A: Hardcoded keyword and regex matching for deterministic triggers.
- Q: If the primary LLM provider fails or is rate-limited, how should the backend handle the request fallback? → A: Fallback to a secondary model from the same provider (e.g., GPT-4o-mini).
- Q: How should the system determine how much previous conversation history to retrieve and send to the LLM for context? → A: Retrieve a fixed number of recent messages (e.g., last 10 messages).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversational RAG Interface (Priority: P1)

As a tenant member, I want to interact with my AI assistants in a chat interface so that I can ask questions and receive answers grounded in my uploaded knowledge base files.

**Why this priority**: This is the core value proposition of the platform. Without grounding, the AI assistants cannot deliver tenant-specific utility.

**Independent Test**: Can be fully tested by sending a message to an assistant that has ingested a unique PDF document. The assistant responds with information found specifically in that PDF and does not leak info from other tenants.

**Acceptance Scenarios**:

1. **Given** a tenant user is authenticated and has selected an assistant with ingested documents, **When** they send a question related to those documents, **Then** the system retrieves relevant context, queries the LLM, returns a complete grounded response, and saves both messages to the conversation history.
2. **Given** a tenant user sends a question unrelated to the ingested documents, **When** the system retrieves no relevant chunks, **Then** the system returns a polite fallback response indicating no relevant information was found, rather than hallucinating or leaking other tenants' data.

---

### User Story 2 - Real-Time Response Streaming (Priority: P2)

As a tenant member, I want the assistant's response to stream in real-time word-by-word (token-by-token) so that I do not have to wait for the entire response to generate before reading it.

**Why this priority**: Dramatically improves the user experience by reducing perceived latency.

**Independent Test**: Can be tested by initiating a WebSocket connection and sending a message; the system streams partial tokens as they are generated, finishing with a completion signal.

**Acceptance Scenarios**:

1. **Given** an active WebSocket connection authenticated for a tenant, **When** a user sends a message, **Then** the assistant's response tokens are streamed back in real-time as they are produced, and the full completed message is persisted in the database.
2. **Given** a WebSocket connection is interrupted mid-stream, **When** the connection drops, **Then** the system gracefully handles the disconnect, stops generating/consuming tokens for that session, and stores the partially generated response in the database.

---

### User Story 3 - Human Handoff (Priority: P3)

As a tenant customer support agent or supervisor, I want the system to flag a conversation for human intervention when the AI cannot answer or when the user requests a human, so that a human agent can take over the conversation.

**Why this priority**: Essential for production deployments where AI fallback needs to be resolved by humans.

**Independent Test**: Can be tested by requesting a human agent; the system changes the conversation status to `handoff` and publishes a real-time notification to the tenant's support channel.

**Acceptance Scenarios**:

1. **Given** a user is chatting with an assistant, **When** they type a deterministic handoff keyword or command (e.g., "speak to human", "/human", "support"), **Then** the conversation status transitions from `bot` to `handoff`, and a real-time event is published to the notification system.
2. **Given** a conversation is in `handoff` status, **When** the user sends a message, **Then** the AI assistant does not automatically respond, ensuring the user is only chatting with a human agent until the handoff is resolved.

---

### Edge Cases

- **Quota Exceeded Mid-Stream**: What happens when a tenant's token quota is exceeded while streaming a response?
  - *Resolution*: The system must immediately stop streaming tokens, append a system notice/error to the stream informing the user that the quota has been reached, and record the partial usage.
- **Slow LLM / Network Timeout**: What happens if the LLM provider is slow or fails to respond?
  - *Resolution*: The system should enforce a timeout (e.g., 30 seconds). If the primary model fails or times out, it MUST automatically fall back to a secondary model from the same provider (e.g., GPT-4o-mini). If both fail, it returns a user-friendly error message, logs the incident, and does not charge quota tokens.
- **Unauthorized Tenant Cross-Talk**: What happens if a user tries to query an assistant belonging to another tenant?
  - *Resolution*: Database Row-Level Security (RLS) and vector store collection isolation (`tenant_{uuid}`) must block access at the database/store layer, returning a 404/403 error, preventing cross-tenant leakage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a REST API endpoint for sending a message and receiving a synchronous (non-streaming) response.
- **FR-002**: The system MUST provide a WebSocket endpoint that supports streaming response tokens.
- **FR-003**: The system MUST authenticate and authorize all chat requests (both REST and WebSocket) using JWT, validating that the user belongs to the target tenant specified in the `X-Tenant-ID` header.
- **FR-004**: The system MUST isolate all vector retrievals to the ChromaDB collection dedicated to the active tenant (`tenant_{uuid}`).
- **FR-005**: The system MUST persist all conversations and messages in PostgreSQL tables (`conversations` and `messages`) with active Row-Level Security (RLS) policies.
- **FR-006**: The system MUST track token usage (both input and output tokens) for every LLM interaction.
- **FR-007**: The system MUST enforce real-time resource quotas (hourly rollups and rate limits) per tenant, rejecting requests with HTTP 429 when quotas are exceeded.
- **FR-008**: The system MUST support a human handoff state for conversations triggered deterministically by keyword/regex matching, disabling automated AI responses once activated and triggering a real-time event.
- **FR-009**: The system MUST retrieve a fixed window of the most recent conversation history (specifically the last 10 messages) to provide as context to the LLM for each chat turn.

### Key Entities *(include if feature involves data)*

- **Conversation**:
  - Represents a single chat thread between a user and an assistant.
  - Key attributes: `id` (UUID), `tenant_id` (UUID, maps to Tenant), `assistant_id` (UUID, maps to Assistant), `status` (enum: `bot`, `handoff`), `title` (string), `created_at`, `updated_at`.
- **Message**:
  - Represents an individual message within a conversation.
  - Key attributes: `id` (UUID), `tenant_id` (UUID), `conversation_id` (UUID, maps to Conversation), `role` (enum: `user`, `assistant`, `system`), `content` (text), `tokens_used` (integer), `created_at`.
- **QuotaLog**:
  - Tracks token usage and rollups for rate limiting and billing.
  - Key attributes: `id` (UUID), `tenant_id` (UUID), `tokens_consumed` (integer), `action_type` (string, e.g., "chat_completion"), `created_at`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Grounded chat responses retrieve and use context only from the active tenant's collection, with 100% data isolation (zero cross-tenant leaks).
- **SC-002**: Standard REST responses return in under 3.0 seconds for 95% of queries under normal load.
- **SC-003**: WebSocket streaming starts delivering the first token within 500ms of message receipt for 90% of requests.
- **SC-004**: Token tracking accuracy is 100% matched with upstream LLM usage responses, and quota checks add less than 10ms of overhead per API request.
- **SC-005**: Human handoff state transition propagates to the Pub/Sub system and is received by subscriber clients in under 100ms.

## Assumptions

- **Assumption 1**: The active tenant's knowledge documents have already been processed, chunked, and embedded into the ChromaDB collection `tenant_{uuid}` by the ingestion pipeline.
- **Assumption 2**: Users have valid JWTs obtained from the authentication service, containing the tenant claims.
- **Assumption 3**: Standard upstream LLM APIs are accessible and functional, supporting both primary and secondary fallback models from the same provider.
- **Assumption 4**: Redis is available for rate limiting, Pub/Sub, and token bucket tracking.
