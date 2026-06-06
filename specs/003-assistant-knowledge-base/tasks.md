# Tasks: Assistant & Knowledge Base

**Input**: Design documents from `/specs/003-assistant-knowledge-base/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are requested and included to verify requirements such as file validations, duplicate naming, active conversation guards, and quota limits.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `T### [P?] [US?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US#]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are specified in descriptions.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure updates.

- [X] T001 [P] Install `minio` in dependency file `backend/requirements.txt`
- [X] T002 [P] Configure MinIO connection parameters in `backend/app/core/config.py`
- [X] T003 Create database migrations for assistants and documents updates in `backend/alembic/versions/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and schemas that must be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement custom recursive character chunker in `backend/app/services/rag/chunker.py`
- [ ] T005 [P] Create MinIO client utility helper in `backend/app/services/storage.py`
- [ ] T006 [P] Define quota configuration constants in `backend/app/core/quotas.py`
- [ ] T007 Define Pydantic request/response schemas for assistants and documents in `backend/app/schemas/`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Create and Configure an AI Assistant (Priority: P1) 🎯 MVP

**Goal**: Enable tenant administrators to create, read, update, and delete custom AI assistants.

**Independent Test**: Create an assistant through the API or UI, edit its fields, check that leaving the name blank displays a validation error, and delete it (asserting deletion is blocked if there are active conversations).

### Tests for User Story 1

- [ ] T008 [P] [US1] Create API tests for assistants management in `backend/tests/api/test_assistants.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement assistant repository/service methods or DB operations in `backend/app/services/assistant.py`
- [ ] T010 [US1] Implement assistant endpoints (POST, GET, PATCH, DELETE) in `backend/app/api/v1/endpoints/assistants.py` and register in `backend/app/api/v1/router.py`
- [ ] T011 [US1] Implement active conversation check guard during assistant deletion in `backend/app/api/v1/endpoints/assistants.py`
- [ ] T012 [P] [US1] Create frontend components for assistants cards and assistant creation/editing forms in `frontend/components/assistants/`
- [ ] T013 [US1] Create frontend dashboard assistants page in `frontend/app/(dashboard)/dashboard/assistants/page.tsx`

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Upload Documents to the Knowledge Base (Priority: P1)

**Goal**: Allow tenant administrators to upload document files (PDF, DOCX, TXT) and ingest public URLs with background processing.

**Independent Test**: Upload a PDF or submit a valid public URL. Verify the document transitions through the pending, processing, and ready states. Verify duplicate filename uploads are rejected, and ingestion failures log a structured error.

### Tests for User Story 2

- [ ] T014 [P] [US2] Create API tests for document upload and ingestion in `backend/tests/api/test_documents.py`

### Implementation for User Story 2

- [ ] T015 [US2] Implement background Celery task for document ingestion (text extraction, chunking, embedding, vector database upsert) in `backend/app/tasks/ingest.py`
- [ ] T016 [US2] Implement synchronous pre-flight URL validation in `backend/app/api/v1/endpoints/documents.py`
- [ ] T017 [US2] Implement document creation and file upload logic to MinIO/DB, checking duplicate filename and quota restrictions, in `backend/app/api/v1/endpoints/documents.py` and register in `backend/app/api/v1/router.py`
- [ ] T018 [US2] Implement structured logging of ingestion failures in `backend/app/tasks/ingest.py`
- [ ] T019 [P] [US2] Create file upload and URL ingest components in `frontend/components/knowledge-base/`
- [ ] T020 [US2] Create knowledge base page view layout in `frontend/app/(dashboard)/dashboard/assistants/[id]/knowledge-base/page.tsx`

**Checkpoint**: At this point, User Stories 1 and 2 are fully functional and integrated.

---

## Phase 5: User Story 3 - Manage and Remove Knowledge Base Documents (Priority: P2)

**Goal**: List documents and delete them permanently from DB, MinIO storage, and ChromaDB index.

**Independent Test**: Verify documents are listed with details (status, type, size). Clicking delete removes the document from DB, storage, and ChromaDB index within 30 seconds. Deleting a processing document cancels ingestion.

### Tests for User Story 3

- [ ] T021 [P] [US3] Add list and delete document tests in `backend/tests/api/test_documents.py`

### Implementation for User Story 3

- [ ] T022 [US3] Implement list documents endpoint in `backend/app/api/v1/endpoints/documents.py`
- [ ] T023 [US3] Implement delete document endpoint (removing files from MinIO, deleting vectors from ChromaDB, updating DB) in `backend/app/api/v1/endpoints/documents.py`
- [ ] T024 [US3] Implement polling endpoint for document status in `backend/app/api/v1/endpoints/documents.py`
- [ ] T025 [P] [US3] Create document list polling component in `frontend/components/knowledge-base/document-list.tsx`
- [ ] T026 [US3] Integrate document listing and deletion in `frontend/app/(dashboard)/dashboard/assistants/[id]/knowledge-base/page.tsx`

**Checkpoint**: Document management and listing is fully operational.

---

## Phase 6: User Story 4 - Retrieve the Embeddable Widget Code (Priority: P3)

**Goal**: Provide the copy-pasteable script tag widget code for the assistant.

**Independent Test**: Access the embed code from an assistant card, copy the snippet, and verify it contains the correct assistant ID and options.

### Implementation for User Story 4

- [ ] T027 [P] [US4] Implement embed code endpoint returning widget script in `backend/app/api/v1/endpoints/assistants.py`
- [ ] T028 [US4] Add embed code modal and clipboard copy function in `frontend/components/assistants/embed-code-modal.tsx`
- [ ] T029 [US4] Integrate embed code modal trigger in `frontend/components/assistants/assistant-card.tsx`

**Checkpoint**: All user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T030 [P] Verify RLS database isolation and tenant restrictions for all new endpoints using testing scripts
- [ ] T031 Run quickstart.md validation to ensure migrations and service setups run smoothly
- [ ] T032 [P] Perform manual user journey checks on local environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phases 3 to 6)**: Depend on Foundational phase completion.
  - User Story 1 (P1) is the MVP and should be completed first.
  - User Story 2 (P1) depends on User Story 1 to attach documents.
  - User Story 3 (P2) depends on User Story 2 (requires documents to list/delete).
  - User Story 4 (P3) depends on User Story 1.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### Parallel Opportunities

- Phase 1 tasks (T001, T002) can run in parallel.
- Phase 2 tasks (T005, T006) can run in parallel.
- Test tasks (T008, T012, T014, T019, T021, T025, T027) can run in parallel with respective logic.
- Developer A can build assistants UI (US1) while Developer B builds the backend endpoints.

---

## Parallel Example: User Story 1

```bash
# Implement the API tests and frontend UI simultaneously:
Task: T008 [P] [US1] Create API tests for assistants management in backend/tests/api/test_assistants.py
Task: T012 [P] [US1] Create frontend components for assistants cards and assistant creation/editing forms in frontend/components/assistants/
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (creation, validation, editing, deletion guard).

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready.
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!).
3. Add User Story 2 -> Test document upload and URL ingest -> Deploy/Demo.
4. Add User Story 3 -> Test polling status, list view, and document deletion.
5. Add User Story 4 -> Test widget code copying.
