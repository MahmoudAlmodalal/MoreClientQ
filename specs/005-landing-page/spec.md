# Feature Specification: Landing Page

**Feature Branch**: `005-landing-page`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "specify only Phase 4 — Landing Page (Week 6) in plan.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Try Live Demo (Priority: P1)

An anonymous visitor (e.g., SMB owner or startup founder) lands on the website and wants to see how the AI assistant works in practice before registering. They interact with the live demo widget embedded directly on the homepage.

**Why this priority**: P1. This is the primary interactive element that demonstrates the core value of the product (dogfooding the platform's own AI assistant) and reduces friction for trial signup.

**Independent Test**: An anonymous visitor can load the page, type a message into the demo widget, and receive a real-time response.

**Acceptance Scenarios**:

1. **Given** an anonymous visitor on the landing page, **When** they type a question into the live demo widget and press Send, **Then** they see a typing indicator followed by a streaming response answering their question.
2. **Given** the live demo widget, **When** a visitor reaches the maximum allowed demo messages (5 messages), **Then** the widget displays a message prompting them to start their free trial to continue.

---

### User Story 2 - Convert via Call-To-Action (Priority: P1)

A visitor has reviewed the features and wants to register for the free trial. They look for clear, accessible buttons to start their trial from any section of the landing page.

**Why this priority**: P1. Conversion is the main business objective of the landing page.

**Independent Test**: Clicking any "Start Free Trial" CTA redirects the user to the signup form.

**Acceptance Scenarios**:

1. **Given** a visitor on the landing page, **When** they click "Start Free Trial" in the Navigation, Hero, or Pricing section, **Then** they are redirected to the registration page.
2. **Given** the Footer CTA email capture field, **When** a visitor enters a valid email address and clicks "Start Free Trial", **Then** they are redirected to the registration page with their email pre-filled.
3. **Given** the Footer CTA email capture field, **When** a visitor enters an invalid email format and clicks "Start Free Trial", **Then** they see a validation error and remain on the page.

---

### User Story 3 - Compare Pricing Plans (Priority: P2)

A visitor wants to choose a plan that fits their usage requirements (Starter, Pro, Business, Enterprise) and compare pricing, message quotas, and features.

**Why this priority**: P2. High value for user decision making, but secondary to the primary "Start Free Trial" CTA.

**Independent Test**: A visitor can view all pricing tiers and click their respective signup/contact buttons.

**Acceptance Scenarios**:

1. **Given** a visitor viewing the pricing section, **When** they compare the plans, **Then** they see transparent pricing, message quotas, and features for each plan (Starter, Pro, Business, Enterprise).
2. **Given** the Enterprise plan card, **When** the visitor clicks the CTA, **Then** they are redirected to a contact sales form/scheduling page rather than the registration page.

---

### User Story 4 - Navigation & External Links (Priority: P2)

An existing customer wants to log in, or a developer wants to access the API documentation.

**Why this priority**: P2. Standard navigation utility.

**Independent Test**: A user can click Navigation links and be redirected to the correct destination.

**Acceptance Scenarios**:

1. **Given** a user on the landing page, **When** they click "Login" in the navigation bar, **Then** they are routed to the login page.
2. **Given** a user on the landing page, **When** they click "Docs" in the navigation bar or footer, **Then** they are routed to the external documentation site.

---

### Edge Cases

- **Backend / AI service offline**: If the live demo backend is unavailable, the chat widget must gracefully show a message: "The live demo is currently offline. You can still start your free trial to test the assistant in your dashboard."
- **Rate limiting**: If the visitor exceeds the message limit or IP rate limit on the live demo, the widget should disable inputs and offer a quick CTA to signup.
- **Mobile responsiveness**: The 3-column features grid and 4-column pricing layout must stack cleanly on mobile viewports without horizontal scrolling or text clipping.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The landing page MUST contain the following sections: Navigation, Hero, Social Proof/Logos, Features Grid, How It Works, Live Demo, Pricing Table, Testimonials, Footer CTA (with email field), and Footer.
- **FR-002**: The Navigation bar MUST be sticky or fixed at the top and include links to Features, How It Works, Pricing, Docs, Login, and a "Start Free Trial" CTA button.
- **FR-003**: The Hero section MUST display a main headline, sub-headline, a primary CTA button ("Start Free Trial"), a secondary CTA button ("See a Demo" that scrolls to the Live Demo), and an animated preview of the chat widget.
- **FR-004**: The Features Grid MUST display at least 6 key capabilities with description and representative icons (RAG Knowledge Base, Multi-Tenant Isolation, Real-Time Streaming, Human Handoff, Analytics, Embeddable Widget).
- **FR-005**: The How It Works section MUST detail the 3 setup steps (Create Assistant, Upload Knowledge, Embed Widget) using clear visual aids.
- **FR-006**: The Live Demo MUST embed a functional chat assistant pre-trained to answer questions about the platform. It MUST stream responses to visitor queries.
- **FR-007**: The Live Demo MUST limit each anonymous session to 5 messages, displaying a conversion message afterwards.
- **FR-008**: The Pricing Table MUST display four plans (Starter: Free, Pro: $49/mo, Business: $199/mo, Enterprise: Custom) along with their corresponding quotas and key features.
- **FR-009**: The Footer CTA MUST contain an email input field and a submit button that validates the input and redirects to the registration page.
- **FR-010**: The landing page MUST configure SEO metadata (Title, Description) and Open Graph/Twitter sharing cards.

### Key Entities *(include if feature involves data)*

- **Lead**: Represents a prospective client who initiated a signup process from the landing page. Key attributes: email address, signup source (e.g. Hero, Pricing, Footer).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The landing page achieves an initial page load time (LCP) of under 1.5 seconds on standard broadband connections.
- **SC-002**: The landing page achieves a Cumulative Layout Shift (CLS) of less than 0.05.
- **SC-003**: The live demo chat widget responds with the first token of a streaming response within 1.0 second of query submission.
- **SC-004**: The landing page achieves a mobile responsiveness score of 100 on standard browser accessibility audits.

## Assumptions

- **A-001**: The landing page is static and does not require active database sessions or authentication for any section other than the interactive Live Demo widget.
- **A-002**: The Live Demo widget interacts with a dedicated public API endpoint on the backend that does not require user authentication.
- **A-003**: User registration, authentication, and dashboard pages are handled by existing authentication and dashboard routes.
- **A-004**: Footer email submissions do not save to a database immediately on the landing page; instead, they are forwarded as a query parameter to the registration page where the user completes signup.
