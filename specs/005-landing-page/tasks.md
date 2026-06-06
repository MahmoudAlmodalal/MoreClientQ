# Tasks: Landing Page

**Input**: Design documents from `/specs/005-landing-page/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required for user stories), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/public-demo-chat.md](./contracts/public-demo-chat.md)

**Tests**: Included in all phases. Unit tests and Playwright E2E tests are configured.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `frontend/` (Next.js 14 monorepo app router)
- **Backend**: `backend/` (FastAPI backend service)
- **Tests**: `backend/tests/` and `frontend/e2e/` (Playwright)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and design system setup

- [X] T001 Create project directories and empty placeholders per implementation plan structure
- [X] T002 [P] Configure Geist and Geist Mono fonts via `next/font/google` in `frontend/app/layout.tsx`
- [X] T003 [P] Configure custom CSS variables for design system tokens in `frontend/app/globals.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend rate limit integration and initial page shell setup

**⚠️ CRITICAL**: Must be completed before any user stories can be fully integrated

- [X] T004 Implement Redis IP-scoped rate limiter service helper in `backend/app/core/rate_limit.py`
- [X] T005 [P] Create FastAPI endpoint router file at `backend/app/api/v1/endpoints/public_chat.py`
- [X] T006 Register public chat route in `backend/app/api/v1/router.py`
- [X] T007 Implement the shell layout for the marketing page in `frontend/app/(marketing)/layout.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Try Live Demo (Priority: P1) 🎯 MVP

**Goal**: Anonymous visitor can interact with a live demo widget on the homepage and receive a real-time streaming response up to 5 messages.

**Independent Test**: Visitor loads the page, types a message in the widget, and receives a streaming AI response. Cap is enforced after 5 messages.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Write unit tests for FastAPI public chat endpoint in `backend/tests/api/test_public_chat.py`
- [X] T009 [P] [US1] Write Playwright E2E test for the 5-message demo cap and error fallbacks in `frontend/e2e/live-demo.spec.ts`

### Implementation for User Story 1

- [X] T010 [US1] Implement public demo chat business logic (FAQ system prompt, openai streaming, 256 tokens max) in `backend/app/api/v1/endpoints/public_chat.py`
- [X] T011 [US1] Add Redis-based session and IP quota limits (5 messages/IP/24h) to `backend/app/api/v1/endpoints/public_chat.py`
- [X] T012 [P] [US1] Create frontend demo chat client-side utility in `frontend/lib/demo-chat.ts`
- [X] T013 [US1] Create the interactive Live Demo component in `frontend/components/landing/LiveDemo.tsx`
- [X] T014 [US1] Add support for error fallback state and quota limit exceeding (429 state) in `frontend/components/landing/LiveDemo.tsx`
- [X] T015 [US1] Write Jest component tests for `LiveDemo.tsx` in `frontend/components/landing/__tests__/LiveDemo.test.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Convert via Call-To-Action (Priority: P1)

**Goal**: Visitor can click CTA buttons in navigation, hero, pricing, or footer to redirect to registration (with email pre-filled from footer).

**Independent Test**: Clicking CTAs redirects to `/register` with optional email parameter. Invalid email format in footer shows a validation error.

### Tests for User Story 2

- [X] T016 [P] [US2] Write Playwright E2E tests for CTAs and email redirect in `frontend/e2e/conversion.spec.ts`

### Implementation for User Story 2

- [X] T017 [P] [US2] Create Footer CTA component with email validation input in `frontend/components/landing/FooterCta.tsx`
- [X] T018 [P] [US2] Create Hero section component with primary/secondary CTAs in `frontend/components/landing/Hero.tsx`
- [X] T019 [P] [US2] Create Partner logo section component in `frontend/components/landing/LogoStrip.tsx`
- [X] T020 [P] [US2] Create Features Grid section component (6 capabilities) in `frontend/components/landing/Features.tsx`
- [X] T021 [P] [US2] Create How It Works section component (3 setup steps) in `frontend/components/landing/HowItWorks.tsx`
- [X] T022 [US2] Assemble static sections (Hero, LogoStrip, Features, HowItWorks, FooterCta) on the page in `frontend/app/(marketing)/page.tsx`
- [X] T023 [US2] Write Jest component tests for email validation and redirection logic in `frontend/components/landing/__tests__/FooterCta.test.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compare Pricing Plans (Priority: P2)

**Goal**: Visitor can view all pricing tiers (Starter, Pro, Business, Enterprise) and click CTA buttons (redirecting Starter/Pro/Business to registration, Enterprise to contact sales).

**Independent Test**: Clicking Enterprise pricing button redirects to contact sales; other pricing buttons redirect to registration.

### Implementation for User Story 3

- [X] T024 [P] [US3] Create Pricing table section component in `frontend/components/landing/Pricing.tsx`
- [X] T025 [P] [US3] Create Testimonials section component in `frontend/components/landing/Testimonials.tsx`
- [X] T026 [US3] Integrate Pricing and Testimonials components into `frontend/app/(marketing)/page.tsx`
- [X] T027 [US3] Write Jest component tests for pricing CTAs in `frontend/components/landing/__tests__/Pricing.test.tsx`

**Checkpoint**: User Stories 1, 2, and 3 should now be functional and testable together

---

## Phase 6: User Story 4 - Navigation & External Links (Priority: P2)

**Goal**: Visitor can navigate using the sticky top navigation bar and footer links (login routes to login page, docs routes to external site).

**Independent Test**: Clicking Login and Docs navigates to respective destinations.

### Tests for User Story 4

- [X] T028 [P] [US4] Write Playwright E2E tests for navigation redirects in `frontend/e2e/navigation.spec.ts`

### Implementation for User Story 4

- [X] T029 [P] [US4] Create sticky Navigation bar component with features/pricing/docs/login links in `frontend/components/landing/Nav.tsx`
- [X] T030 [P] [US4] Create Footer sitemap and social links component in `frontend/components/landing/Footer.tsx`
- [X] T031 [US4] Integrate Nav and Footer into the marketing shell in `frontend/app/(marketing)/layout.tsx`
- [X] T032 [US4] Write Jest component tests for Nav links in `frontend/components/landing/__tests__/Nav.test.tsx`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Polish design detail, optimize, audit, and finalize before release

- [X] T033 Add SEO metadata (Title, Description, OG, Twitter) via `generateMetadata()` in `frontend/app/(marketing)/page.tsx`
- [X] T034 [P] Configure global Tailwind CSS responsive breakpoints for 3-column features and 4-column pricing grids
- [X] T035 Add `IntersectionObserver` scroll-driven fade-up animations in `frontend/components/landing/` components
- [X] T036 Run performance audit (Lighthouse) to verify LCP < 1.5s and CLS < 0.05 targets
- [X] T037 Validate local setup using quickstart.md and run all tests (Jest + Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- E2E or Unit tests should be drafted first, running and failing before implementation
- Backend logic/Endpoints before Frontend integration
- Core implementation before integration with layout

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch both tests for User Story 1 together:
Task: "Write unit tests for FastAPI public chat endpoint in backend/tests/api/test_public_chat.py"
Task: "Write Playwright E2E test for the 5-message demo cap and error fallbacks in frontend/e2e/live-demo.spec.ts"

# Launch client-side library wrapper and API implementation in parallel:
Task: "Create frontend demo chat client-side utility in frontend/lib/demo-chat.ts"
Task: "Implement public demo chat business logic (FAQ system prompt, openai streaming, 256 tokens max) in backend/app/api/v1/endpoints/public_chat.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (anonymous stream, rate limit, error fallback)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (CTAs and conversions)
4. Add User Story 3 → Test independently → Deploy/Demo (Pricing)
5. Add User Story 4 → Test independently → Deploy/Demo (Navigation)
6. Add Polish and SEO optimizations → Run Lighthouse and finalize audits
