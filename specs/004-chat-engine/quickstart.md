# Quickstart: Chat Engine (004-chat-engine)

**Branch**: `004-chat-engine` | **Date**: 2026-06-06

This guide walks a developer through the Chat Engine implementation from a clean checkout.

---

## Prerequisites

- Docker Compose dev environment running (`docker compose up -d`)
- Phases 0–2 already implemented (Auth, Tenancy, Assistant, Knowledge Base)
- A valid JWT and tenant with at least one assistant that has ingested documents

---

## 1. Install New Dependency

The `openai` Python SDK must be added to the backend:

```bash
# Add to backend/requirements.txt
echo "openai>=1.30.0" >> backend/requirements.txt

# Rebuild the backend container
docker compose build backend
docker compose up -d backend
```

---

## 2. Configure Environment Variables

Add the following to your `.env` file (already aligned in `docker-compose.yml`):

```env
# LLM Configuration
OPENAI_API_KEY=sk-...
LLM_PRIMARY_MODEL=gpt-4o
LLM_FALLBACK_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
RAG_TOP_K=5

# Human Handoff Keywords (comma-separated)
HANDOFF_KEYWORDS=speak to human,/human,talk to agent,human please,support
```

---

## 3. Run the Alembic Migration

```bash
docker compose exec backend alembic upgrade head
```

This migration:
- Adds `title` column to `conversations`
- Updates `status` column default to `'bot'` with a CHECK constraint
- Adds `idx_conversations_status` index
- Enables RLS on `conversations` and `messages` if not already active

---

## 4. Test the REST Endpoint

```bash
# Get a valid JWT first (use the login endpoint)
export JWT="<your-token>"
export TENANT_ID="<your-tenant-uuid>"
export ASSISTANT_ID="<your-assistant-uuid>"

# Send a chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d "{\"assistant_id\": \"$ASSISTANT_ID\", \"message\": \"What is this platform about?\"}"
```

Expected: JSON response with `content`, `tokens_used`, `sources`.

---

## 5. Test the WebSocket Endpoint

```bash
# Using websocat (install: cargo install websocat)
websocat "ws://localhost:8000/api/v1/ws/chat?token=$JWT&tenant_id=$TENANT_ID&assistant_id=$ASSISTANT_ID"

# Then type a JSON message:
{"type":"message","conversation_id":null,"content":"Hello, what can you help me with?"}
```

Expected: A stream of `{"type":"token","delta":"..."}` events, ending with `{"type":"done",...}`.

---

## 6. Test Human Handoff

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d "{\"assistant_id\": \"$ASSISTANT_ID\", \"conversation_id\": \"<existing-conv-id>\", \"message\": \"speak to human\"}"
```

Expected: HTTP 409 with `"Conversation is in handoff mode"`. Verify in DB that `conversations.status = 'handoff'`.

---

## 7. Run Backend Tests

```bash
docker compose exec backend pytest tests/test_chat.py -v
```

---

## 8. Access the Chat UI

Navigate to:

```
http://<tenant-slug>.localhost:3000/dashboard/assistants/<assistant-id>/chat
```

The chat page connects automatically via WebSocket and renders the streaming response.

---

## Key Files Reference

| File | Purpose |
|---|---|
| `backend/app/api/v1/endpoints/chat.py` | REST chat endpoint |
| `backend/app/api/v1/endpoints/ws_chat.py` | WebSocket streaming endpoint |
| `backend/app/services/chat_service.py` | Core orchestration (RAG + LLM + persist) |
| `backend/app/services/llm_service.py` | LLM client with primary/fallback model |
| `backend/app/services/quota_service.py` | Redis token quota enforcement |
| `backend/app/services/handoff_service.py` | Keyword detection + Pub/Sub |
| `backend/app/schemas/chat.py` | Pydantic request/response schemas |
| `backend/alembic/versions/xxxx_add_chat_engine_schema.py` | DB migration |
| `frontend/app/dashboard/assistants/[id]/chat/page.tsx` | Chat UI page |
| `frontend/components/chat/` | Chat UI component library |
| `frontend/lib/chat-api.ts` | REST + WebSocket client helpers |
| `specs/004-chat-engine/contracts/rest-chat.md` | REST API contract |
| `specs/004-chat-engine/contracts/ws-chat.md` | WebSocket API contract |
