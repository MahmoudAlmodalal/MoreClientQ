# API Contract: REST Chat Endpoint

**Branch**: `004-chat-engine` | **Date**: 2026-06-06

---

## Overview

A synchronous (non-streaming) endpoint for sending a user message to an assistant and receiving a complete AI response. Intended for integrations and fallback scenarios where WebSocket is unavailable.

---

## Endpoint

```
POST /api/v1/chat
```

---

## Authentication & Authorization

- **Header**: `Authorization: Bearer <JWT>`
- **Header**: `X-Tenant-ID: <tenant_uuid>`
- JWT must contain `tenant_id` claim matching the `X-Tenant-ID` header.
- JWT must contain an RBAC role of `owner`, `admin`, `member`, or `viewer`.
- Returns `401 Unauthorized` if JWT is missing/invalid.
- Returns `403 Forbidden` if `tenant_id` mismatch.

---

## Request

### Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <JWT>` |
| `X-Tenant-ID` | Yes | UUID of the active tenant |
| `Content-Type` | Yes | `application/json` |

### Body

```json
{
  "assistant_id": "uuid",
  "conversation_id": "uuid | null",
  "message": "string (1–4000 chars)"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `assistant_id` | UUID | Yes | Must belong to the authenticated tenant |
| `conversation_id` | UUID | No | If null, a new conversation is created |
| `message` | string | Yes | User's input text; max 4000 chars |

---

## Responses

### 200 OK — Successful Response

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "role": "assistant",
  "content": "string",
  "tokens_used": 312,
  "sources": [
    {
      "document_id": "uuid",
      "chunk_text": "string",
      "score": 0.87
    }
  ],
  "model_used": "gpt-4o"
}
```

### 400 Bad Request

```json
{ "detail": "message must not be empty" }
```

### 401 Unauthorized

```json
{ "detail": "Invalid or missing authentication token" }
```

### 403 Forbidden

```json
{ "detail": "Tenant ID mismatch" }
```

### 404 Not Found

```json
{ "detail": "Assistant not found" }
```

### 409 Conflict — Conversation in Handoff State

```json
{ "detail": "Conversation is in handoff mode; AI responses are suspended" }
```

### 429 Too Many Requests — Quota Exceeded

```json
{
  "detail": "Token quota exceeded for this billing period",
  "retry_after": "2026-06-06T11:00:00Z"
}
```

### 503 Service Unavailable — LLM Failure

```json
{ "detail": "AI service temporarily unavailable. Please try again shortly." }
```

---

## Behaviour Notes

1. If `conversation_id` is not provided, the server creates a new `Conversation` record with `status = 'bot'` and returns its ID.
2. A pre-flight quota check is performed before calling the LLM. If the tenant's hourly token budget is exhausted, a 429 is returned immediately.
3. The last 10 messages of the conversation are retrieved and included as context history for the LLM.
4. If the user's message matches a handoff keyword (e.g., "speak to human", "/human"), the conversation status is updated to `handoff` and a 409 is returned with an appropriate message — the AI does **not** generate a response.
5. The primary LLM model is attempted first. On failure (429 / 503 from the upstream provider), the fallback model is tried once.
6. Both the user message and assistant response are persisted before the response is returned.
