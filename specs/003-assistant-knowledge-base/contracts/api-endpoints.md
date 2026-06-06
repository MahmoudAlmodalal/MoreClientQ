# API Contracts: Assistant & Knowledge Base

This document defines the HTTP API contracts for the Assistant and Knowledge Base services.

---

## 1. Assistants API

All assistants endpoints are tenant-scoped via the `X-Tenant-ID` header and JWT token.

### 1.1 List Assistants
* **Endpoint**: `GET /api/v1/assistants`
* **Headers**:
  * `Authorization: Bearer <JWT>`
  * `X-Tenant-ID: <UUID>`
* **Response (200 OK)**:
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Customer Support Bot",
    "system_prompt": "You are a helpful customer support bot.",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1024,
    "is_active": true,
    "widget_config": {},
    "created_at": "2026-06-06T12:00:00Z",
    "updated_at": "2026-06-06T12:00:00Z"
  }
]
```

### 1.2 Create Assistant
* **Endpoint**: `POST /api/v1/assistants`
* **Headers**:
  * `Authorization: Bearer <JWT>`
  * `X-Tenant-ID: <UUID>`
* **Request Body**:
```json
{
  "name": "Support Bot",
  "system_prompt": "Answer support tickets.",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 1024
}
```
* **Response (201 Created)**: Returns the created assistant object.
* **Error (400 Bad Request / 403 Forbidden / 422 Unprocessable)**:
  * Invalidation of quota: `"Limit of N assistants exceeded for your plan."`
  * Validation errors.

### 1.3 Get Assistant Details
* **Endpoint**: `GET /api/v1/assistants/{id}`
* **Response (200 OK)**: Single assistant object.

### 1.4 Update Assistant
* **Endpoint**: `PATCH /api/v1/assistants/{id}`
* **Request Body** (all fields optional):
```json
{
  "name": "Updated Support Bot",
  "system_prompt": "Answer support tickets concisely.",
  "temperature": 0.5,
  "is_active": true
}
```
* **Response (200 OK)**: Returns the updated assistant object.

### 1.5 Delete Assistant
* **Endpoint**: `DELETE /api/v1/assistants/{id}`
* **Response (204 No Content)**
* **Error (409 Conflict)**:
  * Triggers if the assistant has active conversations:
    `{"detail": "This assistant has 3 active conversations. Resolve or end them before deleting."}`

### 1.6 Get Widget Embed Code
* **Endpoint**: `GET /api/v1/assistants/{id}/embed`
* **Response (200 OK)**:
```json
{
  "snippet": "<script src=\"https://platform.com/widget.js\" data-assistant=\"3fa85f64-5717-4562-b3fc-2c963f66afa6\"></script>"
}
```

---

## 2. Knowledge Base (Documents) API

### 2.1 Upload Document
* **Endpoint**: `POST /api/v1/documents/upload`
* **Content-Type**: `multipart/form-data`
* **Request Fields**:
  * `file`: (Binary File, e.g. `.pdf`, `.docx`, `.txt`)
  * `assistant_id`: `<UUID>`
* **Response (201 Created)**:
```json
{
  "id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "assistant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "user_guide.pdf",
  "file_type": "pdf",
  "status": "pending",
  "chunk_count": null,
  "error_message": null,
  "created_at": "2026-06-06T12:05:00Z"
}
```
* **Error (400 Bad Request)**:
  * File type unsupported: `"Unsupported file type. Allowed: PDF, DOCX, TXT."`
  * Filename already exists for this assistant: `"This file already exists in this assistant's knowledge base."`
  * File size exceeds limit: `"File size exceeds maximum limit of 50MB."`
  * Quota exceeded: `"Limit of N documents exceeded for your plan."`

### 2.2 Ingest URL
* **Endpoint**: `POST /api/v1/documents/url`
* **Request Body**:
```json
{
  "url": "https://example.com/docs",
  "assistant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```
* **Response (201 Created)**: Same response format as document upload, type `url`.
* **Error (400 Bad Request)**:
  * Synchronous validation fails (unreachable, non-200, redirects to login):
    `{"detail": "This URL could not be reached or requires authentication."}`

### 2.3 List Documents
* **Endpoint**: `GET /api/v1/documents`
* **Query Params**:
  * `assistant_id`: `<UUID>` (optional, to filter)
* **Response (200 OK)**:
```json
[
  {
    "id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
    "assistant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "user_guide.pdf",
    "file_type": "pdf",
    "status": "ready",
    "chunk_count": 42,
    "error_message": null,
    "created_at": "2026-06-06T12:05:00Z"
  }
]
```

### 2.4 Get Document Status (Polling Endpoint)
* **Endpoint**: `GET /api/v1/documents/{id}/status`
* **Response (200 OK)**:
```json
{
  "id": "5fa85f64-5717-4562-b3fc-2c963f66afa7",
  "status": "processing",
  "chunk_count": null,
  "error_message": null
}
```

### 2.5 Delete Document
* **Endpoint**: `DELETE /api/v1/documents/{id}`
* **Response (204 No Content)**
