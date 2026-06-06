# Research: Landing Page

**Feature**: Landing Page (Phase 4 — Week 6)
**Date**: 2026-06-06
**Spec**: [spec.md](./spec.md)

## Summary

All technical questions for the Landing Page feature were resolved using the existing project context from [plan.md](../../plan.md) (Section 9) and the project constitution. No external research was needed — the design system, component structure, route group layout, SEO strategy, and live demo approach are all fully specified.

---

## Decision Log

### Decision 1: Route Group Strategy

- **Decision**: Use the existing Next.js `(marketing)` route group (`frontend/app/(marketing)/`) for all landing page routes, with a dedicated `layout.tsx` that excludes the authenticated dashboard shell.
- **Rationale**: The project already has this route group defined. Keeping the landing page in `(marketing)` isolates its layout (no sidebar, no auth guards) from the `(dashboard)` shell. The `layout.tsx` there should carry the minimal navigation bar and footer rather than the app header.
- **Alternatives considered**: A separate `/landing` sub-route — rejected because the landing page is the root `/` and should live at `app/(marketing)/page.tsx`.

---

### Decision 2: Fully Static Page

- **Decision**: The landing page is a server-side rendered (SSR) static export with no client-side data fetching, except for the Live Demo widget which connects to a public backend endpoint.
- **Rationale**: Aligns with spec assumption A-001 and plan section 9.5 ("Landing page is fully static"). Static rendering achieves LCP < 1.5 s (SC-001) and CLS < 0.05 (SC-002). The Next.js App Router defaults to server components, which satisfies this naturally.
- **Alternatives considered**: Client-side-only SPA rendering — rejected due to SEO and performance requirements.

---

### Decision 3: Live Demo Integration

- **Decision**: The Live Demo widget connects to a public backend endpoint `POST /v1/public/chat` with rate limiting enforced at the Nginx level. The widget tracks a `demo_message_count` in `sessionStorage` (client-side) to enforce the 5-message cap before the backend is reached. The backend also enforces the cap via an IP-scoped Redis counter as a server-side safety net.
- **Rationale**: The spec (FR-006, FR-007) requires both streaming responses and a 5-message cap. Using `sessionStorage` for the counter gives immediate UX feedback (disable input) without a round-trip. Redis-backed IP counter prevents abuse from visitors who clear session storage.
- **Alternatives considered**: Cookie-based tracking — rejected because cookies require consent banners under GDPR; `sessionStorage` is ephemeral and requires no consent.

---

### Decision 4: Design System

- **Decision**: Apply the design system defined in plan section 9.4 — Dark theme (`#0a0a0a` background, `#7C3AED` primary violet, `#22D3EE` accent cyan), Geist + Geist Mono font pair, and CSS-based scroll animations (Intersection Observer API for fade-up, typewriter using CSS `@keyframes`).
- **Rationale**: Consistency with the overall product aesthetics. The plan explicitly defines this palette and animation approach. shadcn/ui is available in the project for base components; landing-specific sections use custom components.
- **Alternatives considered**: Tailwind animation plugins — not rejected per se, but the spec uses Tailwind (already in the project), so scroll animations use `animate-fade-up` utility or a small helper class rather than adding a new dependency.

---

### Decision 5: SEO & Open Graph

- **Decision**: Use Next.js `generateMetadata()` on `app/(marketing)/page.tsx` to export static `<title>`, `<meta name="description">`, and Open Graph / Twitter card tags.
- **Rationale**: Next.js 14 App Router's metadata API generates the correct `<head>` tags at build time, compatible with static export. This satisfies FR-010 with zero additional libraries.
- **Alternatives considered**: `next-seo` package — rejected; overkill for a single static landing page. The built-in metadata API is sufficient.

---

### Decision 6: Email Capture Flow

- **Decision**: The Footer CTA email field is an HTML `<form>` with client-side validation (HTML5 `type="email"` + a regex check before submit). On submit, the form redirects to `/register?email=<encoded_email>` via `router.push()`. No server-side email storage occurs at the landing page level (assumption A-004).
- **Rationale**: Spec FR-009 and A-004 clarify that email storage happens during the full registration flow, not on the landing page. This keeps the landing page fully static.
- **Alternatives considered**: A server action to POST email to a newsletter service — deferred to a future phase (Phase 7 Launch).

---

### Decision 7: Animated Hero Chat Preview

- **Decision**: The Hero animated chat preview (FR-003) is a scripted CSS animation of a mock conversation — not a real API call. Pre-written message pairs are shown in sequence using a CSS/JS typewriter effect and a looping timer, giving the appearance of a live chat without any backend dependency.
- **Rationale**: A real API call in the Hero section risks degrading LCP if the backend is slow. The Live Demo section (below the fold) is the appropriate place for real API interaction. The animated mock keeps the hero fast and always-on.
- **Alternatives considered**: Hero connected to real `/v1/public/chat` — rejected for LCP impact and risk of the hero "breaking" if the backend is offline.
