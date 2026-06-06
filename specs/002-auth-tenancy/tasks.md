# Tasks: Auth & Tenancy

**Input**: Design documents from `/specs/002-auth-tenancy/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Includes exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/app/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create core config settings for JWT, Postgres, and Redis in `backend/app/core/config.py`
- [X] T002 [P] Initialize SQLAlchemy engine and session management in `backend/app/db/session.py`
- [X] T003 [P] Setup Alembic migration environment in `backend/alembic/env.py` and `backend/alembic.ini`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define SQLAlchemy Declarative Base with common UUID helper methods in `backend/app/db/base.py`
- [X] T005 [P] Configure Redis connection pool and async caching client in `backend/app/core/redis.py`
- [X] T006 [P] Implement JWT token encoding, decoding, and verification functions in `backend/app/core/security.py`
- [X] T007 Setup global routing, exception handling, and middleware structures in `backend/app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Tenant Registration & Owner Setup (Priority: P1) 🎯 MVP

**Goal**: Register a tenant and its primary owner account in a single API call with slug validation.

**Independent Test**: Send POST to `/api/v1/auth/register`, verify db records are created for tenant (matching slug) and user (role='owner').

### Tests for User Story 1
- [X] T008 [P] [US1] Write integration tests for registration endpoint in `backend/tests/api/test_registration.py`

### Implementation for User Story 1
- [X] T009 [P] [US1] Define SQLAlchemy database model for Tenant in `backend/app/models/tenant.py`
- [X] T010 [P] [US1] Define SQLAlchemy database model for User in `backend/app/models/user.py`
- [X] T011 [US1] Create Alembic migration script to create `tenants` and `users` tables in `backend/alembic/versions/`
- [X] T012 [P] [US1] Implement helper CRUD services for Tenant and User setup in `backend/app/services/user.py`
- [X] T013 [US1] Implement registration endpoint (`POST /api/v1/auth/register`) in `backend/app/api/v1/endpoints/auth.py`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Secure JWT Authentication & Lifecycle (Priority: P1)

**Goal**: Authenticate users, return JWT tokens (access + refresh), and handle token refresh requests.

**Independent Test**: POST credentials to `/api/v1/auth/login`, verify JWT payload contains `sub`, `tenant_id`, and `role`, and call `/refresh`.

### Tests for User Story 2
- [X] T014 [P] [US2] Write integration tests for login and token refresh flows in `backend/tests/api/test_auth.py`

### Implementation for User Story 2
- [X] T015 [P] [US2] Implement secure password hashing and verification helpers in `backend/app/core/security.py`
- [X] T016 [US2] Implement JWT authentication dependency/middleware verification in `backend/app/core/security.py`
- [X] T017 [US2] Implement login (`POST /api/v1/auth/login`) and refresh (`POST /api/v1/auth/refresh`) routes in `backend/app/api/v1/endpoints/auth.py`

**Checkpoint**: User Stories 1 & 2 are functional together.

---

## Phase 5: User Story 3 - Subdomain-Based Tenant Resolution (Priority: P1)

**Goal**: Next.js middleware extracts tenant slug, validates against backend/Redis, and forwards via header.

**Independent Test**: Access dashboard on `acme.localhost:3000`, verify `X-Tenant-ID` injection in headers via logs.

### Tests for User Story 3
- [X] T018 [P] [US3] Write unit tests for Next.js subdomain parsing and routing in `frontend/tests/middleware.test.ts`

### Implementation for User Story 3
- [X] T019 [US3] Implement slug lookup API endpoint (`GET /api/v1/tenants/resolve/{slug}`) in `backend/app/api/v1/endpoints/tenants.py`
- [X] T020 [US3] Implement subdomain extraction, Redis cache-aside lookup, and header forwarding in `frontend/middleware.ts`

**Checkpoint**: Subdomain context maps correctly through Next.js frontend to API backend.

---

## Phase 6: User Story 4 - Row-Level Security (RLS) & Tenant Middleware (Priority: P1)

**Goal**: Set transaction-scoped tenant context in backend and enforce isolation using Postgres RLS.

**Independent Test**: Execute query from Tenant A session, verify Tenant B data is unreachable.

### Tests for User Story 4
- [X] T021 [P] [US4] Write DB tests verifying RLS query constraints on the `users` table in `backend/tests/db/test_rls.py`

### Implementation for User Story 4
- [X] T022 [US4] Implement `TenantMiddleware` in `backend/app/core/middleware.py` to extract `X-Tenant-ID` and run `SET LOCAL app.current_tenant_id`
- [X] T023 [US4] Create Alembic migration script to enable RLS policies on `users` table in `backend/alembic/versions/`

**Checkpoint**: Secure data isolation is mathematically enforced at database layer.

---

## Phase 7: User Story 5 - Role-Based Access Control (RBAC) Enforcement (Priority: P2)

**Goal**: Restrict API endpoint routing based on static roles (`owner`, `admin`, `member`, `viewer`).

**Independent Test**: Call admin-only endpoint as member user, verify request fails with `403 Forbidden`.

### Tests for User Story 5
- [X] T024 [P] [US5] Write integration tests for role check dependencies in `backend/tests/api/test_rbac.py`

### Implementation for User Story 5
- [X] T025 [US5] Implement FastAPI Role verification helper dependencies in `backend/app/core/security.py`
- [X] T026 [US5] Apply static Role requirements to existing User API endpoints in `backend/app/api/v1/endpoints/users.py`

**Checkpoint**: Static RBAC restrictions enforce fine-grained access control.

---

## Phase 8: User Story 6 - User Invites & Team Management (Priority: P2)

**Goal**: Manage team invitations (tokens, accepts), list users, update roles, and offboard tenant.

**Independent Test**: Invite user, accept via registration token, verify list, and offboard tenant to clean up db.

### Tests for User Story 6
- [X] T027 [P] [US6] Write integration tests for invitation creation, acceptance, role updating, and offboarding in `backend/tests/api/test_team.py`

### Implementation for User Story 6
- [X] T028 [P] [US6] Define SQLAlchemy database model for Invitation in `backend/app/models/invitation.py`
- [X] T029 [P] [US6] Define SQLAlchemy database model for QuotaLog in `backend/app/models/quota_log.py`
- [X] T030 [US6] Create Alembic migration script creating `invitations` table (with `quota_logs` already migrated) and enabling RLS in `backend/alembic/versions/`
- [X] T031 [US6] Implement invitation creation and acceptance logic in `backend/app/services/auth.py`
- [X] T032 [US6] Implement team endpoints (invite, list, update role, delete) in `backend/app/api/v1/endpoints/users.py`
- [X] T033 [US6] Implement accept invitation endpoint (`POST /api/v1/auth/invite/accept`) in `backend/app/api/v1/endpoints/auth.py`
- [X] T034 [US6] Implement tenant offboarding / cascade purge API (`DELETE /api/v1/tenants/self`) in `backend/app/api/v1/endpoints/tenants.py`

**Checkpoint**: Team workspace management and offboarding cycles are complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: General optimizations, documentation, and final validations

- [X] T035 Implement user logout invalidation via Redis token blocklist in `backend/app/api/v1/endpoints/auth.py`
- [X] T036 [P] Update developer documentations with endpoint details and setup requirements in `README.md`
- [ ] T037 Execute quickstart verification scripts to validate all workflows in `specs/002-auth-tenancy/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

* **Setup (Phase 1)**: No dependencies - can start immediately.
* **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
* **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  * User Story 1 (US1) is the MVP and must be completed first to bootstrap database rows.
  * User Story 2 (US2) integrates with US1 for credentials login.
  * User Story 3 (US3) integrates with Next.js frontend middleware.
  * User Story 4 (US4) enforces RLS on top of the users model.
  * User Story 5 (US5) enforces RBAC on top of user auth.
  * User Story 6 (US6) handles invitations and team listing.
* **Polish (Phase 9)**: Depends on all user stories being completed.

### Parallel Opportunities

* Setup tasks `T002` and `T003` can run in parallel.
* Foundational tasks `T005`, `T006`, and `T007` can run in parallel.
* Story 1 model creation tasks `T009` and `T010` can run in parallel.
* Test files `T008`, `T014`, `T018`, `T021`, `T024`, and `T027` can be implemented and run in parallel within their respective phases.

---

## Parallel Example: User Story 1

```bash
# Implement the database models concurrently:
Task: "Define SQLAlchemy database model for Tenant in backend/app/models/tenant.py"
Task: "Define SQLAlchemy database model for User in backend/app/models/user.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Tenant Registration & Owner Setup)
4. **STOP and VALIDATE**: Verify tenant and owner tables exist, and endpoints respond successfully.
