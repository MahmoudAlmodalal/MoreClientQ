# Feature Specification: Assistant & Knowledge Base Management

**Feature Branch**: `003-assistant-knowledge-base`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "specify only Phase 2 — Assistant & Knowledge Base (Weeks 3–4) in plan.md file"

## Clarifications

### Session 2026-06-06

- Q: What should happen when an admin uploads a file that already exists in the same assistant's knowledge base? → A: Reject the upload with a clear error message: "This file already exists in this assistant's knowledge base."
- Q: How many times should the system retry a failed background ingestion task before marking the document as "failed"? → A: 3 retries with a 30-second delay between each attempt (4 total attempts); the document is marked "failed" after all retries are exhausted.
- Q: What should happen when an admin tries to delete an assistant that has ongoing active conversations? → A: Block the deletion and display an error: "This assistant has N active conversations. Resolve or end them before deleting."
- Q: What should happen when an admin submits a URL that is unreachable, returns a non-200 status, or redirects to a login page? → A: Reject the submission immediately with a descriptive error before queuing the task (e.g., "This URL could not be reached or requires authentication.").
- Q: Should ingestion failures be surfaced beyond the UI (e.g., logged or notified to the admin out-of-band)? → A: Record each ingestion failure as a structured log entry accessible to the platform operator; no tenant-facing notification beyond the UI "failed" status is required in Phase 2.
- Q: What maximum file upload size should Phase 2 support? → A: 10 MB maximum; files above 10 MB are rejected before upload.
- Q: What should happen when an admin uploads a document while the tenant's storage quota is full? → A: Reject before upload with a clear "storage quota exceeded" error; no document is created.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Configure an AI Assistant (Priority: P1)

A tenant administrator creates a new AI assistant for their organization by providing a name, defining its behavior through a system prompt, and selecting the AI model and response parameters that best fit their use case.

**Why this priority**: Creating an assistant is the foundational action that enables all downstream features — without an assistant, no knowledge base can be attached, no conversations can occur, and no widget can be embedded. This is the entry point to the entire Phase 2 feature set.

**Independent Test**: Can be fully tested by an admin user creating an assistant, verifying it appears in the assistant list with the correct configuration, and confirming the settings persist after the session.

**Acceptance Scenarios**:

1. **Given** a logged-in admin user on the Assistants page, **When** they fill in the assistant name, system prompt, AI model, and response parameters and submit, **Then** the new assistant appears in the assistant list with the correct configuration and an "active" status.
2. **Given** an existing assistant, **When** the admin edits any configuration field and saves, **Then** the assistant reflects the updated configuration immediately.
3. **Given** an existing assistant, **When** the admin deletes it, **Then** the assistant is removed from the list and all associated knowledge base data is also deleted.
4. **Given** an admin filling in the assistant creation form, **When** they leave the assistant name blank and attempt to submit, **Then** a validation error is displayed and the form is not submitted.

---

### User Story 2 - Upload Documents to the Knowledge Base (Priority: P1)

A tenant administrator uploads documents (PDF, Word, or plain text files) or submits a URL to populate an assistant's knowledge base. The system processes these documents in the background and notifies the user of the current processing status.

**Why this priority**: A knowledge base populated with content is what transforms a generic AI assistant into a domain-specific support agent. Without document ingestion, the assistant cannot answer questions grounded in the tenant's own content.

**Independent Test**: Can be fully tested by uploading a PDF document to an assistant's knowledge base, monitoring the status transition from "pending" to "processing" to "ready", and confirming the document is listed with the correct status.

**Acceptance Scenarios**:

1. **Given** an admin on the Knowledge Base page for an assistant, **When** they upload a PDF, DOCX, or TXT file, **Then** the document appears in the list with a "pending" status that transitions to "processing" and ultimately "ready" upon successful ingestion.
2. **Given** an admin submitting a URL for ingestion, **When** they provide a valid, publicly accessible web URL and submit, **Then** the URL is ingested as a document and appears in the list with the same status lifecycle.
3. **Given** an admin submitting a URL for ingestion, **When** the URL is unreachable, returns a non-200 HTTP status, or redirects to a login/authentication page, **Then** the submission is rejected immediately with a descriptive error message before any background task is queued.
4. **Given** a document that encounters an error during ingestion, **When** the processing fails, **Then** the document status shows "failed" with a human-readable error message.
5. **Given** an admin uploading a file that exceeds the allowed size limit, **When** they attempt to submit, **Then** an error is shown before upload begins explaining the size restriction.
6. **Given** an admin uploading a file of an unsupported type, **When** they attempt to submit, **Then** a clear error message explains which file types are accepted.

---

### User Story 3 - Manage and Remove Knowledge Base Documents (Priority: P2)

A tenant administrator reviews the documents currently in an assistant's knowledge base, checks their processing status, and removes outdated or incorrect documents to keep the knowledge base accurate.

**Why this priority**: Knowledge base maintenance is essential for long-running assistants. Outdated documents lead to incorrect answers. Admins must be able to delete stale content to ensure response quality.

**Independent Test**: Can be fully tested by viewing the document list, deleting a document, and confirming it no longer appears in the list and is no longer used in assistant responses.

**Acceptance Scenarios**:

1. **Given** an admin on the Knowledge Base page, **When** they view the page, **Then** all uploaded documents are listed with their filename, file type, status, and upload date.
2. **Given** an admin on the Knowledge Base page, **When** they click delete on a document, **Then** the document is removed from the list and permanently deleted from storage and the knowledge index.
3. **Given** an admin deleting a document that is currently being processed, **When** they confirm deletion, **Then** the ingestion process is cancelled and the document is removed cleanly.

---

### User Story 4 - Retrieve the Embeddable Widget Code (Priority: P3)

A tenant administrator retrieves the embed code for a configured assistant so they can install it on their external website or product.

**Why this priority**: The embed code delivery is a read-only output of a configured assistant. It depends on an assistant existing (P1), making it naturally lower priority in Phase 2 scope.

**Independent Test**: Can be fully tested by navigating to an existing assistant, retrieving the embed code snippet, and verifying it contains the correct assistant identifier and is formatted for copy-paste installation.

**Acceptance Scenarios**:

1. **Given** an existing assistant, **When** the admin requests the embed code, **Then** a ready-to-paste script snippet is displayed that uniquely identifies the assistant.
2. **Given** the embed code is displayed, **When** the admin copies it, **Then** the full snippet is copied to the clipboard without truncation.

---

### Edge Cases

- What happens when an admin attempts to create a second assistant when the tenant's plan only allows one?
- If a tenant's storage quota is full, document uploads are rejected before upload begins with a clear "storage quota exceeded" error and no document entry is created.
- If the same file is uploaded twice to the same assistant, the upload is rejected with a clear error message: "This file already exists in this assistant's knowledge base." No duplicate document entry is created.
- How does the system behave if the knowledge base document count exceeds the plan's document limit?
- If an admin attempts to delete an assistant that has one or more active conversations, the deletion is blocked and an error is displayed: "This assistant has N active conversations. Resolve or end them before deleting."
- If the background job queue is under high load and all 3 retries are exhausted (maximum ~1.5 minutes in "processing" state), the document is marked "failed" with an appropriate error message; the admin may delete and re-upload the file to try again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow tenant admins and owners to create named AI assistants with a configurable system prompt, AI model selection, and response parameters.
- **FR-002**: The system MUST allow tenant admins and owners to update any configuration field of an existing assistant, with changes taking effect on the next conversation.
- **FR-003**: The system MUST allow tenant admins and owners to delete an assistant, which MUST cascade to remove all associated knowledge base documents and indexed content. Deletion MUST be blocked if the assistant has any active conversations, displaying the count and an instruction to resolve them first.
- **FR-004**: The system MUST list all assistants belonging to the tenant, displaying name, active status, and creation date at minimum.
- **FR-005**: The system MUST allow tenant admins and owners to upload documents (PDF, DOCX, TXT formats) to an assistant's knowledge base.
- **FR-006**: The system MUST allow tenant admins and owners to submit a publicly accessible URL for ingestion into an assistant's knowledge base. The system MUST validate the URL synchronously at submission time — if the URL is unreachable, returns a non-200 HTTP status, or redirects to an authentication-gated page, the submission MUST be rejected immediately with a descriptive error message before any background task is queued.
- **FR-007**: The system MUST process uploaded documents asynchronously in the background without blocking the user interface.
- **FR-008**: The system MUST display the processing status of each document as one of: pending, processing, ready, or failed.
- **FR-009**: The system MUST allow users to poll or receive live updates on document processing status without requiring a full page refresh.
- **FR-010**: The system MUST display a human-readable error message for documents that fail ingestion, describing the nature of the failure.
- **FR-011**: The system MUST enforce a 10 MB maximum file upload size, rejecting files that exceed the limit before the upload begins.
- **FR-012**: The system MUST reject uploads of unsupported file types with a clear error message listing accepted formats.
- **FR-013**: The system MUST allow tenant admins and owners to delete a document from the knowledge base, which MUST remove it from both document storage and the knowledge index simultaneously.
- **FR-014**: The system MUST provide an embeddable widget code snippet for each assistant that can be copied and installed on an external website.
- **FR-015**: The system MUST enforce tenant-level data isolation — no admin may view, modify, or delete assistants or documents belonging to another tenant.
- **FR-016**: The system MUST enforce plan-based limits on the number of assistants and documents a tenant may create (e.g., Starter: 1 assistant, 5 documents; Pro: 5 assistants, 100 documents).
- **FR-017**: The system MUST reject a document upload if a document with the same filename already exists in the same assistant's knowledge base, displaying the error: "This file already exists in this assistant's knowledge base."
- **FR-018**: The system MUST prevent deletion of an assistant that has one or more conversations in "active" status, returning an error message that includes the count of active conversations and instructs the admin to resolve them before retrying the deletion.
- **FR-019**: The system MUST emit a structured log entry for every document ingestion failure, including at minimum: tenant ID, document ID, filename or URL, failure reason, attempt number, and timestamp. These log entries are accessible to platform operators and are NOT surfaced to the tenant admin beyond the "failed" status in the UI.
- **FR-020**: The system MUST reject document uploads before upload begins when the tenant's storage quota is full, displaying a clear "storage quota exceeded" error and creating no document entry.

### Key Entities *(include if feature involves data)*

- **Assistant**: A named, configurable AI agent belonging to a tenant. Key attributes: name, system prompt, AI model, response parameters, active status, widget configuration, and creation date. An assistant owns zero or more knowledge base documents.
- **Document**: A file or URL ingested into an assistant's knowledge base. Key attributes: filename or URL, file type, processing status (pending / processing / ready / failed), error message (if failed), number of indexed chunks, and upload date. A document belongs to exactly one assistant and one tenant.
- **Knowledge Index**: The searchable representation of all processed documents for an assistant. Not directly visible to users, but its state is reflected through document status. Deleting a document must update the knowledge index accordingly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin can create a fully configured assistant in under 2 minutes from the point they begin filling in the form.
- **SC-002**: A document of up to 10 MB is successfully ingested and ready for use within 3 minutes of upload under normal load conditions.
- **SC-003**: Document processing status is visible and up-to-date within 5 seconds of a status change occurring in the background.
- **SC-004**: 95% of valid document uploads (within size and type limits) complete ingestion successfully and reach "ready" status.
- **SC-005**: Deleting a document removes it from the knowledge index within 30 seconds, after which it no longer influences assistant responses.
- **SC-006**: No data from one tenant's assistants or knowledge base is accessible to users of any other tenant under any conditions.
- **SC-007**: Plan-based limits are enforced 100% of the time — no tenant exceeds their allowed assistant or document count regardless of concurrent requests.
- **SC-008**: The embed widget code is retrievable within 1 second of the admin requesting it for any existing assistant.

## Assumptions

- Phase 1 (Authentication & Multi-Tenancy) is fully complete — tenant resolution, JWT authentication, RBAC, and RLS are operational and available as a dependency.
- Only users with the `owner` or `admin` role may create, edit, or delete assistants and manage knowledge base documents; `member` and `viewer` roles have no write access to these resources.
- A single assistant may be associated with multiple documents; documents are scoped to one assistant (not shared across assistants).
- URL ingestion fetches the publicly accessible content of the submitted URL at the time of submission; subsequent changes to the URL's content are not automatically re-ingested.
- Supported file types for upload are PDF, DOCX, and TXT only for the initial Phase 2 release; additional formats may be added in later phases.
- Maximum single file upload size is 10 MB for Phase 2.
- Document processing status polling is implemented via client-side polling at a reasonable interval (e.g., every 5 seconds) as the default; push-based updates (e.g., Server-Sent Events) are an enhancement for later phases.
- The widget embed code is a static, pre-formatted code snippet; its visual customization (colors, position, greeting) is handled separately in a later phase (Phase 5 — Dashboard & Widget).
- Tenant plan limits (assistant count, document count) are enforced at the API level and are defined by the tenant's current subscription plan stored in the tenant record.
- Background document processing tasks are retried automatically on transient failures up to **3 times** (4 total attempts), with a **30-second delay** between each retry. After all retries are exhausted the document is marked "failed" and the admin must delete and re-upload to retry.
