# Contract: Public Demo Chat Endpoint

**Feature**: Landing Page (Phase 4 — Week 6)
**Date**: 2026-06-06
**Spec**: [spec.md](../spec.md)

---

## Overview

The Live Demo widget on the landing page connects to a single public (unauthenticated) streaming chat endpoint. This contract defines the request/response structure and rate limiting guarantees.

This endpoint is intentionally minimal — it accepts plain text messages and returns streaming token responses using Server-Sent Events (SSE). It does **not** require a JWT token and does **not** create persistent conversation records.

---

## Endpoint

```
POST /v1/public/chat
```

**Authentication**: None (public endpoint)
**Rate Limits**: 5 messages per IP per 24 hours (Redis-backed)
**Content-Type (Request)**: `application/json`
**Content-Type (Response)**: `text/event-stream`

---

## Request

```json
{
  "message": "string",       // The visitor's input. Required. Max 500 characters.
  "session_id": "string"     // Client-generated UUID for the browser session. Required. Used for Redis scoping.
}
```

### Request Validation Rules

| Field       | Required | Max Length | Notes                                        |
|-------------|----------|------------|----------------------------------------------|
| `message`   | Yes      | 500 chars  | Stripped of leading/trailing whitespace       |
| `session_id`| Yes      | 36 chars   | Must be a valid UUID v4                       |

---

## Response

### Success (Streaming)

Response is an SSE stream. Each event is a JSON object on a `data:` line.

**Event: token** (during streaming)
```
data: {"type": "token", "content": "Hello"}

data: {"type": "token", "content": " there"}
```

**Event: done** (stream complete)
```
data: {"type": "done", "message_count": 3}
```

| Field           | Type    | Description                                               |
|-----------------|---------|-----------------------------------------------------------|
| `type`          | string  | Either `"token"` or `"done"`                              |
| `content`       | string  | The partial token text (only present on `token` events)   |
| `message_count` | integer | Updated count of messages sent this session (only on `done`) |

### Error Responses

| HTTP Status | Error Code           | Description                                                  |
|-------------|----------------------|--------------------------------------------------------------|
| `400`       | `INVALID_REQUEST`    | Message is missing, too long, or session_id is malformed     |
| `429`       | `DEMO_QUOTA_EXCEEDED`| This IP or session has used all 5 demo messages              |
| `503`       | `SERVICE_UNAVAILABLE`| Backend LLM service is temporarily unreachable               |

**Error Body Example (non-streaming)**:
```json
{
  "error": {
    "code": "DEMO_QUOTA_EXCEEDED",
    "message": "You have reached the demo limit. Start your free trial to continue.",
    "message_count": 5
  }
}
```

---

## Rate Limiting Behavior

| Scope       | Limit                       | Reset Period | Action on Breach           |
|-------------|-----------------------------|--------------|----------------------------|
| Per IP      | 5 messages                  | 24 hours     | HTTP 429 + `DEMO_QUOTA_EXCEEDED` |
| Per session | 5 messages (client enforced)| Browser tab  | Input disabled before request sent |

The server-side IP rate limit acts as a safety net for clients that bypass `sessionStorage`. Both limits are tracked independently via Redis keys:
- `demo:ip:<sha256(ip)>` — TTL 86400 seconds
- `demo:session:<session_id>` — TTL 86400 seconds

---

## LLM Context

The public demo assistant is pre-configured with a fixed system prompt that describes the platform's capabilities. It does **not** use any tenant-specific vector store. It responds from a small hardcoded FAQ knowledge set embedded in the system prompt.

- **No RAG**: No ChromaDB query is performed for the public demo.
- **No persistence**: No conversation or message records are written to the database.
- **Model**: Uses the primary configured LLM model (same as production chat engine), but with a reduced `max_tokens` budget (256 tokens max per response).

---

## Client Integration Example

```typescript
// frontend/lib/demo-chat.ts (illustrative)

const SESSION_KEY = 'demo_session';

interface DemoSession {
  session_id: string;
  message_count: number;
}

export function getDemoSession(): DemoSession {
  const stored = sessionStorage.getItem(SESSION_KEY);
  if (stored) return JSON.parse(stored);
  const session = { session_id: crypto.randomUUID(), message_count: 0 };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

export async function sendDemoMessage(
  message: string,
  onToken: (token: string) => void
): Promise<number> {
  const session = getDemoSession();
  if (session.message_count >= 5) throw new Error('DEMO_QUOTA_EXCEEDED');

  const response = await fetch('/v1/public/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: session.session_id }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error.code);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let newCount = session.message_count;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    for (const line of chunk.split('\n')) {
      if (!line.startsWith('data:')) continue;
      const event = JSON.parse(line.slice(5));
      if (event.type === 'token') onToken(event.content);
      if (event.type === 'done') newCount = event.message_count;
    }
  }

  session.message_count = newCount;
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return newCount;
}
```
