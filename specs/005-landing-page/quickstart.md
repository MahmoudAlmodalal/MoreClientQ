# Quickstart: Landing Page

**Feature**: Landing Page (Phase 4 — Week 6)
**Date**: 2026-06-06

---

## Prerequisites

- Backend and frontend services running via Docker Compose (see root `docker-compose.yml`)
- Redis service running (required for demo rate limiting)
- Node.js 20 + npm installed for local frontend development

---

## Running the Landing Page Locally

```bash
# From project root — start all backend services including Redis
docker compose up -d redis backend

# In a separate terminal — start the Next.js dev server
cd frontend
npm install   # first time only
npm run dev
```

The landing page is served at: **http://localhost:3000/**

---

## Backend: Public Demo Endpoint

The live demo widget calls `POST /v1/public/chat`. This endpoint is part of the main FastAPI backend.

```bash
# Verify the demo endpoint is reachable
curl -X POST http://localhost:8000/v1/public/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What can this platform do?", "session_id": "00000000-0000-0000-0000-000000000001"}'

# Expect: a streaming SSE response with data: {"type":"token",...} lines
```

---

## Demo Rate Limit Reset (Development)

```bash
# Clear demo rate limit keys from Redis (for local testing)
docker compose exec redis redis-cli KEYS "demo:*" | xargs docker compose exec -T redis redis-cli DEL
```

---

## File Locations

| Resource | Path |
|---|---|
| Landing page entry | `frontend/app/(marketing)/page.tsx` |
| Marketing layout (nav + footer) | `frontend/app/(marketing)/layout.tsx` |
| Landing components | `frontend/components/landing/` |
| Demo chat helper | `frontend/lib/demo-chat.ts` |
| Backend demo endpoint | `backend/app/api/v1/endpoints/public_chat.py` |
| Interface contract | `specs/005-landing-page/contracts/public-demo-chat.md` |

---

## Tailwind Design Tokens (Landing)

The landing page uses CSS custom properties defined in `frontend/app/globals.css`:

```css
:root {
  --color-bg:       #0a0a0a;
  --color-surface:  #111111;
  --color-primary:  #7C3AED; /* violet-600 */
  --color-accent:   #22D3EE; /* cyan-400  */
  --color-text:     #F9FAFB;
  --color-muted:    #6B7280;
}
```

---

## Running Tests

```bash
# Component tests
cd frontend && npm run test -- --testPathPattern=landing

# E2E tests (Playwright — requires both services running)
npx playwright test tests/landing/
```

---

## Key Acceptance Checks

Before marking the feature complete, verify:

- [ ] All 10 page sections render correctly on desktop (1280px)
- [ ] All 10 sections stack cleanly on mobile (375px) — no horizontal overflow
- [ ] "Start Free Trial" CTAs in Nav, Hero, and Pricing redirect to `/register`
- [ ] Footer CTA with invalid email shows validation error (no redirect)
- [ ] Footer CTA with valid email redirects to `/register?email=<email>&source=footer`
- [ ] Live demo widget sends and streams a response for the first message
- [ ] After 5 messages, input is disabled and CTA prompt appears
- [ ] With backend offline (stop the backend service), hero still renders and demo shows graceful fallback
- [ ] Lighthouse report shows LCP < 1.5s, CLS < 0.05 on `/`
- [ ] `<title>` and `<meta name="description">` are present in page source
