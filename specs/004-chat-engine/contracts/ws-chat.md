# API Contract: WebSocket Chat Endpoint

**Branch**: `004-chat-engine` | **Date**: 2026-06-06

---

## Overview

A WebSocket endpoint for real-time, token-by-token streaming of assistant responses. This is the primary transport for the chat UI.

---

## Endpoint

```
GET /api/v1/ws/chat?token=<JWT>&tenant_id=<uuid>&assistant_id=<uuid>
Upgrade: websocket
```

---

## Authentication & Authorization

- JWT is passed as a `token` query parameter (browser WebSocket API does not support custom headers on handshake).
- `tenant_id` is passed as a query parameter; must match the `tenant_id` in the JWT.
- After the connection is accepted, the server validates the token. If invalid, the connection is closed with code `4001` (policy violation).
- If `tenant_id` mismatch, closed with code `4003`.

---

## Connection Lifecycle

```
Client                          Server
  │                               │
  ├──── WS Handshake ────────────►│
  │◄─── 101 Switching Protocols ──┤  (token validated; conversation initialised)
  │                               │
  ├──── {"type":"message", ...} ──►│  (user sends a message)
  │◄─── {"type":"token", ...} ────┤  (streaming tokens arrive)
  │◄─── {"type":"token", ...} ────┤
  │◄─── {"type":"done", ...} ─────┤  (stream complete; full message persisted)
  │                               │
  ├──── {"type":"message", ...} ──►│  (next turn)
  │      ...                      │
  ├──── WS Close ─────────────────►│
```

---

## Client → Server Messages

### `message` — Send a user chat message

```json
{
  "type": "message",
  "conversation_id": "uuid | null",
  "content": "string (1–4000 chars)"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string | Yes | Always `"message"` |
| `conversation_id` | UUID | No | If null, server creates a new conversation |
| `content` | string | Yes | User's message text |

### `ping` — Keepalive

```json
{ "type": "ping" }
```

---

## Server → Client Messages

### `token` — Streamed partial response

```json
{
  "type": "token",
  "delta": "string"
}
```

### `done` — Stream complete

```json
{
  "type": "done",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "tokens_used": 312,
  "model_used": "gpt-4o",
  "sources": [
    {
      "document_id": "uuid",
      "chunk_text": "string",
      "score": 0.87
    }
  ]
}
```

### `error` — Application-level error (connection stays open)

```json
{
  "type": "error",
  "code": "string",
  "detail": "string"
}
```

| Error Code | Meaning |
|---|---|
| `quota_exceeded` | Tenant token quota exhausted; AI response terminated |
| `handoff_active` | Conversation is in handoff mode; AI response suspended |
| `llm_unavailable` | Both primary and fallback LLM failed |
| `assistant_not_found` | Provided `assistant_id` not found for this tenant |
| `invalid_message` | Message validation failure (empty, too long, etc.) |

### `handoff` — Handoff event triggered

```json
{
  "type": "handoff",
  "conversation_id": "uuid",
  "detail": "This conversation has been transferred to a human agent."
}
```

### `pong` — Keepalive reply

```json
{ "type": "pong" }
```

---

## WebSocket Close Codes

| Code | Meaning |
|---|---|
| `1000` | Normal closure (client or server initiated) |
| `4001` | Authentication failed (invalid JWT) |
| `4003` | Forbidden (tenant_id mismatch) |
| `4008` | Policy violation (rate limit) |

---

## Behaviour Notes

1. On connection, the server validates the JWT and `tenant_id` parameter.
2. When a `message` event is received, the server performs a pre-flight quota check before streaming begins.
3. If the user message matches a handoff keyword, the server immediately sends a `{"type":"handoff", ...}` event and updates the conversation status in the database — no tokens are streamed.
4. Token streaming uses async generator iteration over the LLM SDK's response stream. Each yielded chunk delta is sent as a `token` event immediately.
5. On mid-stream quota breach, the server sends `{"type":"error","code":"quota_exceeded"}` and stops iterating. The partial response is persisted with `[response truncated]` appended.
6. On WebSocket disconnect mid-stream, the server stops consuming tokens and persists the partial response.
7. The `done` event is only sent after the full response is successfully persisted.
