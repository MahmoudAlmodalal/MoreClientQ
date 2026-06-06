# Implementation Plan: Landing Page

**Branch**: `005-landing-page` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-landing-page/spec.md`

## Summary

Build the public-facing landing page for the multi-tenant AI assistant platform targeting SMB owners and startup founders. The page converts cold traffic into trial signups through a structured sequence: sticky navigation → animated hero → social proof → features grid → how it works → interactive live demo → pricing table → testimonials → footer CTA. The live demo embeds a functional (unauthenticated) streaming chat widget that dogfoods the platform's own AI infrastructure. The page is fully statically rendered (Next.js App Router server components) with a single public backend endpoint for the live demo.

## Technical Context

**Language/Version**: TypeScript / Node.js 20 (frontend), Python 3.11 (backend — demo endpoint only)

**Primary Dependencies**:
- Frontend: Next.js 14 (App Router), shadcn/ui, Geist font (via `next/font`), Tailwind CSS
- Backend (demo only): FastAPI 0.110, Redis 7 (IP rate limiting), openai SDK (LLM call)

**Storage**: Redis 7 (per-IP demo rate limiting, session scoping). No PostgreSQL writes for the landing page itself.

**Testing**: Jest + React Testing Library (component tests); Playwright (E2E — navigation, CTAs, email validation, demo cap)

**Target Platform**: Linux server via Docker Compose (same production stack); statically rendered at build time by Next.js

**Project Type**: Web application — frontend marketing page within the existing Next.js 14 App Router monorepo

**Performance Goals**:
- LCP < 1.5 s on standard broadband (SC-001)
- CLS < 0.05 (SC-002)
- Live demo first-token latency < 1.0 s (SC-003)
- Mobile responsiveness score 100 (SC-004)

**Constraints**:
- Landing page is fully static (no client-side data fetching except live demo widget)
- Hero animated chat preview is a CSS/JS mock — no API call in the hero section
- Email capture redirects to `/register?email=...` with no server-side storage at landing layer
- Live demo endpoint is unauthenticated but rate-limited (5 msg/IP/24h via Redis)
- No new PostgreSQL tables introduced

**Scale/Scope**: Single public page at `/`; live demo backend endpoint scoped to ~50 req/min under normal launch traffic

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Multi-Tenancy RLS Isolation | ✅ PASS | Landing page introduces no tenant-scoped data. No PostgreSQL writes occur. The live demo endpoint is intentionally tenant-agnostic (no `tenant_id`). |
| II | Per-Tenant Vector Store Isolation | ✅ PASS | Public demo endpoint uses a fixed system prompt with no ChromaDB query. Zero cross-tenant vector access. |
| III | Subdomain Resolution & JWT Validation | ✅ PASS | Landing page serves on the root domain (not a tenant subdomain). No JWT validation required. Demo endpoint is public and intentionally unauthenticated. |
| IV | Resource Quota Enforcement & Rate Limiting | ✅ PASS | Public demo endpoint enforces a 5-message/IP/24h Redis quota. Nginx rate limiting applies at the ingress layer (same as all endpoints). |
| V | Decoupled Async Processing | ✅ PASS | Demo endpoint response is synchronous streaming (SSE). No Celery tasks are triggered. No document ingestion or vector upsert operations occur. |

**Gate result: PASS — all 5 principles satisfied.**

## Project Structure

### Documentation (this feature)

```text
specs/005-landing-page/
├── plan.md                      # This file
├── research.md                  # Phase 0 output
├── data-model.md                # Phase 1 output
├── quickstart.md                # Phase 1 output
├── contracts/
│   └── public-demo-chat.md     # Public demo SSE endpoint contract
└── tasks.md                     # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   └── (marketing)/
│       ├── layout.tsx                    # MODIFY: marketing shell (nav + footer, no auth)
│       └── page.tsx                      # MODIFY: assemble all landing sections
├── components/
│   └── landing/
│       ├── Nav.tsx                       # NEW: sticky navigation bar
│       ├── Hero.tsx                      # NEW: headline + animated mock chat
│       ├── LogoStrip.tsx                 # NEW: social proof / partner logos
│       ├── Features.tsx                  # NEW: 6-feature 3-column grid
│       ├── HowItWorks.tsx                # NEW: 3-step visual guide
│       ├── LiveDemo.tsx                  # NEW: real streaming chat widget (public)
│       ├── Pricing.tsx                   # NEW: 4-plan pricing table
│       ├── Testimonials.tsx              # NEW: 3–4 quote cards
│       ├── FooterCta.tsx                 # NEW: email capture + CTA
│       └── Footer.tsx                    # NEW: sitemap links + social
└── lib/
    └── demo-chat.ts                      # NEW: DemoSession + sendDemoMessage helper

backend/
└── app/
    └── api/
        └── v1/
            └── endpoints/
                └── public_chat.py        # NEW: POST /v1/public/chat (SSE, no auth)
```

**Structure Decision**: Web application (Option 2). The landing page is a frontend-only feature within the existing `frontend/` directory, extended with new components under `components/landing/`. A single new backend endpoint handles the live demo (no new router file — registered directly in the existing `v1/router.py`).

## Complexity Tracking

> No constitution violations detected. This section is intentionally left minimal.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Unauthenticated public endpoint | FR-006 requires anonymous visitors to use the live demo without signing up | A gated demo would eliminate the conversion benefit of showing the product in action |

## Implementation Phases

### Phase 1 — Backend: Public Demo Endpoint

- [ ] Add `POST /v1/public/chat` to `backend/app/api/v1/endpoints/public_chat.py`
- [ ] Implement Redis IP-scoped rate limiter (5 msg/IP/24h, key: `demo:ip:<sha256(ip)>`)
- [ ] Implement Redis session counter (key: `demo:session:<session_id>`)
- [ ] Wire fixed system prompt (no RAG, no ChromaDB) with max_tokens=256
- [ ] Return SSE stream: `{"type":"token","content":"..."}` + `{"type":"done","message_count":N}`
- [ ] Register route in `backend/app/api/v1/router.py`
- [ ] Write unit tests for quota enforcement and error responses

### Phase 2 — Frontend: Design System & Layout

- [ ] Configure Geist + Geist Mono fonts via `next/font/google` in `frontend/app/layout.tsx`
- [ ] Define CSS custom properties for design tokens (colors, spacing, radii) in `globals.css`
- [ ] Build `frontend/app/(marketing)/layout.tsx` with sticky Nav + Footer shell
- [ ] Build `Nav.tsx`: sticky, blur backdrop, links, login button, primary CTA

### Phase 3 — Frontend: Static Sections

- [ ] Build `Hero.tsx`: headline, sub-headline, CTAs, animated mock chat (CSS typewriter)
- [ ] Build `LogoStrip.tsx`: partner/technology logo row
- [ ] Build `Features.tsx`: 6-feature 3-column grid with icons
- [ ] Build `HowItWorks.tsx`: 3-step numbered visual flow
- [ ] Build `Pricing.tsx`: 4-tier table with "Start Free Trial" / "Contact Sales" CTAs
- [ ] Build `Testimonials.tsx`: 3–4 quote cards with avatar, name, company
- [ ] Build `FooterCta.tsx`: email input + validation + redirect to `/register?email=...`
- [ ] Build `Footer.tsx`: sitemap columns + social icons
- [ ] Assemble all sections in `(marketing)/page.tsx`

### Phase 4 — Frontend: Live Demo Widget

- [ ] Build `lib/demo-chat.ts`: `getDemoSession()` + `sendDemoMessage()` with SSE parsing
- [ ] Build `LiveDemo.tsx`: chat UI, streaming indicator, quota-reached CTA state
- [ ] Handle offline/503 state: show graceful fallback message (spec edge case)
- [ ] Handle rate-limit/429 state: disable input + show CTA

### Phase 5 — SEO, Performance & Responsiveness

- [ ] Add `generateMetadata()` to `(marketing)/page.tsx` (title, description, OG, Twitter cards)
- [ ] Audit Tailwind breakpoints for mobile responsiveness (feature grid, pricing table)
- [ ] Add `IntersectionObserver`-based scroll fade-up animations
- [ ] Run Lighthouse audit — target LCP < 1.5s, CLS < 0.05

### Phase 6 — Testing

- [ ] Component tests: Nav links, FooterCta email validation, Pricing CTAs
- [ ] E2E (Playwright): Live Demo 5-message cap, offline fallback, mobile viewport checks
