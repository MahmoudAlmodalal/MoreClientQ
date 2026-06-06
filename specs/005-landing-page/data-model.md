# Data Model: Landing Page

**Feature**: Landing Page (Phase 4 — Week 6)
**Date**: 2026-06-06
**Spec**: [spec.md](./spec.md)

> **Note**: The Landing Page is primarily a static frontend feature. It does not introduce new database tables or backend data models. The only data concern is the **Lead** entity (spec FR-009) and the **DemoSession** ephemeral construct for the live demo widget. These are documented below.

---

## Entities

### Lead

Represents a prospective client who submitted their email via the landing page Footer CTA and was redirected to the registration form.

This entity is **not persisted at the landing page level** (assumption A-004). The email is forwarded as a query parameter to the registration page, where the full `User` record is created by the existing auth system.

| Attribute     | Type     | Description                                                                 | Constraints                          |
|---------------|----------|-----------------------------------------------------------------------------|--------------------------------------|
| `email`       | string   | Prospective client's email address                                          | Required; valid RFC 5322 email format |
| `signup_source` | enum  | Which CTA section triggered the conversion (`hero`, `pricing`, `footer`)   | Required                             |

**Lifecycle**: This entity is transient — it exists as a URL query parameter (`/register?email=...&source=footer`) and is consumed by the registration page to pre-fill the form. No database write occurs at the landing page layer.

---

### DemoSession (Ephemeral / Client-Side)

Tracks the anonymous visitor's usage of the Live Demo widget during a single browser session.

| Attribute        | Type    | Description                                                            | Constraints                     |
|------------------|---------|------------------------------------------------------------------------|---------------------------------|
| `message_count`  | integer | Number of messages sent by the visitor in the current demo session     | 0–5; capped at 5                |
| `session_active` | boolean | Whether the visitor can still send messages (count < 5)                | Derived from `message_count`    |

**Persistence**: Stored in `sessionStorage` under the key `demo_session`. Cleared automatically when the browser tab is closed. Not persisted to any backend database.

**Server-side enforcement**: The backend `/v1/public/chat` endpoint maintains an IP-scoped Redis counter (`demo:ip:<hashed_ip>`) with a 24-hour TTL to prevent bypass via `sessionStorage` clearing.

---

## State Transitions

### Live Demo Widget State Machine

```
IDLE ──────────────► SENDING ──────────────► STREAMING
  ▲                     │                        │
  │                     │ (error)                 │ (stream complete)
  │                     ▼                        ▼
  │                  ERROR ◄──────────── RECEIVED
  │                     │
  └─────────────── QUOTA_REACHED (message_count >= 5)
                        │
                        ▼
                   CTA_PROMPT (show "Start Free Trial")
```

| State         | Entry Condition                          | Exit Condition                                |
|---------------|------------------------------------------|-----------------------------------------------|
| IDLE          | Initial / after message received         | User types and submits a message              |
| SENDING       | User submits message                     | Backend begins streaming OR error received    |
| STREAMING     | Backend sends first token                | Stream closes (done signal)                   |
| RECEIVED      | Stream complete                          | Auto-transitions to IDLE or QUOTA_REACHED     |
| ERROR         | Backend offline or network failure       | User retries or dismisses                     |
| QUOTA_REACHED | `message_count` increments to 5          | N/A (terminal state for session)              |
| CTA_PROMPT    | QUOTA_REACHED                            | User clicks "Start Free Trial"                |

---

## Interface Contracts (Public Demo Endpoint)

The Live Demo widget requires one public backend endpoint. This is documented in [contracts/public-demo-chat.md](./contracts/public-demo-chat.md).

---

## Validation Rules

| Entity       | Rule                                                                                  |
|--------------|---------------------------------------------------------------------------------------|
| Lead.email   | Must match RFC 5322 email pattern. Validated client-side before redirect.             |
| DemoSession.message_count | Must be 0–5. Incremented after each successful send. Hard cap enforced at 5. |

---

## Non-Goals (Out of Scope for this Feature)

- No new PostgreSQL tables are created for the landing page.
- No authentication or session tokens are issued on the landing page.
- The `Lead` entity is not stored in a CRM or newsletter service in this phase (deferred to Phase 7 — Launch).
