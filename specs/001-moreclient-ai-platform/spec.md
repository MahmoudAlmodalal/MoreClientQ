# Feature Specification: MoreClient AI Enterprise Platform

**Feature Branch**: `001-moreclient-ai-platform`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "MoreClient AI — Multi-Tenant AI Customer Support Platform (Enterprise Edition v2.0)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tenant Onboarding & First AI Assistant (Priority: P1)

A new B2B customer signs up, verifies their account, and has a working AI assistant live on their website within a single session — without needing engineering support.

**Why this priority**: This is the core activation moment. Without a functional onboarding path, no other features matter. Determines the product's time-to-value and first-impression conversion.

**Independent Test**: Can be fully tested by registering a new account, completing workspace setup, uploading one document, and embedding the chat widget — delivering a live AI chat experience without human help.

**Acceptance Scenarios**:

1. **Given** a new visitor on the registration page, **When** they submit full name, valid email, and a compliant password, **Then** their account is created, a verification email is sent, and a workspace with a default assistant is automatically provisioned.
2. **Given** a verified account, **When** the user uploads a PDF knowledge document, **Then** the document is processed (virus scan → extraction → embedding) and marked as "Ready" within a defined time limit.
3. **Given** a configured assistant, **When** the user copies the widget embed code and opens it in a browser, **Then** the chat widget renders and the assistant responds using only the uploaded knowledge.

---

### User Story 2 - End Customer AI Conversation (Priority: P1)

An end customer visits a business's website, opens the chat widget, and receives accurate answers from the AI assistant — with automatic escalation to a human agent when needed.

**Why this priority**: This is the product's core value delivery. Every conversation is a direct test of AI resolution quality and the human handoff reliability.

**Independent Test**: Can be tested by initiating a conversation with a question covered by the knowledge base, verifying an accurate response, then sending a complaint-intent message and confirming escalation to a live agent queue.

**Acceptance Scenarios**:

1. **Given** a widget embedded on a website, **When** an end customer sends a question matching knowledge base content, **Then** the AI responds with a relevant, accurate answer in under 5 seconds.
2. **Given** an ongoing conversation, **When** the customer sends a message expressing clear negative sentiment or requests a human (e.g., "I want to speak to someone"), **Then** the conversation is escalated and assigned to an available human agent.
3. **Given** a conversation with low-confidence AI retrieval, **When** the confidence score falls below the configured threshold, **Then** the system automatically routes the conversation to the human handoff queue.

---

### User Story 3 - Knowledge Base Management (Priority: P2)

A Tenant Admin uploads, organizes, and versions their company knowledge so the AI assistant stays accurate as policies and products change.

**Why this priority**: Knowledge quality directly determines AI resolution rate. Versioning and rollback prevent accidental degradation when knowledge is updated incorrectly.

**Independent Test**: Can be tested independently by uploading multiple document types, triggering a knowledge update that creates a new version, and rolling back to a prior version — then verifying the AI responds using the rolled-back knowledge.

**Acceptance Scenarios**:

1. **Given** a knowledge base, **When** the admin uploads a DOCX, PDF, or CSV file, **Then** the file is processed through the full pipeline and the knowledge version is incremented (e.g., v1.0 → v1.1).
2. **Given** multiple knowledge versions exist, **When** an admin selects a prior version and triggers rollback, **Then** the active knowledge reverts and the AI answers reflect the earlier version's content.
3. **Given** a URL scraping request, **When** the admin provides a valid website URL, **Then** the system extracts and indexes the page content as a knowledge source.

---

### User Story 4 - Human Agent Handling Live Escalations (Priority: P2)

A human support agent receives escalated conversations, responds to customers in real time, and resolves or closes tickets — with full AI conversation history visible.

**Why this priority**: The human handoff layer is what makes the platform enterprise-safe. Agents need full context to avoid making customers repeat themselves.

**Independent Test**: Can be tested by triggering an escalation from the AI chat, logging in as an agent, accepting the assignment, sending a reply visible to the customer, and marking the conversation resolved.

**Acceptance Scenarios**:

1. **Given** an escalated conversation, **When** an available agent accepts it, **Then** they see the full prior AI conversation history alongside the live chat interface.
2. **Given** a live escalated session, **When** the agent sends a message, **Then** the customer receives it in the widget in real time.
3. **Given** a resolved escalation, **When** the agent marks it closed, **Then** the conversation is archived and a CSAT prompt may be triggered to the customer.

---

### User Story 5 - Subscription & Usage Billing (Priority: P2)

A Tenant Admin manages their subscription plan, monitors usage metering, and receives automated overage billing when limits are exceeded.

**Why this priority**: Billing is the revenue mechanism. Overage billing without manual intervention is critical for the SaaS business model at scale.

**Independent Test**: Can be tested by selecting a plan, simulating messages beyond the plan limit, and verifying an overage charge is applied automatically without admin action.

**Acceptance Scenarios**:

1. **Given** a workspace on a monthly plan, **When** the admin navigates to billing, **Then** they see current usage (messages, tokens, storage, agents) against their plan limits.
2. **Given** usage exceeding the plan message limit, **When** the billing cycle is evaluated, **Then** an overage charge is automatically calculated and applied to the payment method on file.
3. **Given** a subscription about to expire, **When** 7 days remain, **Then** the admin receives an in-app and email notification warning them.

---

### User Story 6 - AI Training Center (Priority: P3)

A Tenant Admin reviews failed AI responses and trains the assistant by providing correct answers — improving future resolution accuracy.

**Why this priority**: Continuous improvement of the AI is required to maintain high deflection rates over time. This closes the quality feedback loop.

**Independent Test**: Can be tested by identifying a failed/downvoted AI response, providing a correct answer, and confirming the question is resolved and the knowledge updated.

**Acceptance Scenarios**:

1. **Given** a list of failed AI responses (low confidence, hallucination reports, downvotes), **When** an admin selects one and provides the correct answer, **Then** the answer is embedded into the knowledge base and the question is marked Resolved.
2. **Given** a hallucination report, **When** the admin reviews it, **Then** they can flag the knowledge source causing the issue and trigger re-processing.

---

### User Story 7 - CRM Lead Pipeline (Priority: P3)

When a conversation reveals purchase intent, a lead record is automatically created and tracked through a sales pipeline by the Tenant Admin.

**Why this priority**: Lead capture from conversations is a differentiating feature for sales-focused tenants. Automating this closes the gap between support and revenue.

**Independent Test**: Can be tested by sending a purchase-intent message in the chat widget, verifying a lead is auto-created with contact fields, and moving it through pipeline stages.

**Acceptance Scenarios**:

1. **Given** an AI conversation where purchase intent is detected, **When** the intent is classified, **Then** a lead record is created with available contact information (name, channel, estimated value).
2. **Given** a lead in "New" status, **When** the admin moves it to "Contacted", **Then** the pipeline stage updates and the change is logged.

---

### Edge Cases

- What happens when a document upload contains a virus? The file must be rejected before any storage or processing, and the admin notified.
- What happens when the AI retrieves no relevant results for a customer query? The system falls back to a configurable "I don't know" message and optionally escalates.
- What happens when a human agent is unavailable during escalation? The system queues the conversation and notifies the customer of expected wait time or offers a callback option.
- What happens when a tenant exceeds storage limits? Uploads are blocked and the admin is notified before data is rejected.
- What happens when the widget is offline (website not connected)? The widget shows a configurable offline message.
- How does the system handle concurrent knowledge updates? Versioning is atomic — only one update is applied at a time; concurrent requests are queued.
- What happens when a lead's contact details are incomplete? The lead is still created with available data; incomplete fields are flagged for manual completion.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Identity**

- **FR-001**: System MUST allow registration with full name, email, and password, enforcing uniqueness on email and password complexity (min 8 chars, uppercase, lowercase, number, symbol).
- **FR-002**: System MUST send an email verification link upon registration and prevent full platform access until email is confirmed.
- **FR-003**: System MUST automatically provision a workspace, default assistant, and tenant resources upon successful registration.
- **FR-004**: System MUST support Google OAuth login as an alternative to email/password.
- **FR-005**: System MUST implement JWT-based sessions with refresh tokens and rotation to maintain secure authenticated state.

**Workspace Management**

- **FR-006**: System MUST provide each tenant with an isolated workspace containing company information (name, industry, website, country, timezone) and branding (logo, color, favicon).
- **FR-007**: Each tenant's data MUST be logically isolated via PostgreSQL Row Level Security with separate Qdrant collections, S3 prefixes, and Redis key namespaces.
- **FR-007b**: Tenants MUST select a data residency region at signup (GCC region or Global). All tenant data — conversations, knowledge, audit logs — MUST be stored exclusively in the selected region for the lifetime of the workspace.

**Assistant Builder**

- **FR-008**: Tenant Admins MUST be able to configure the assistant's identity (name, avatar, description), personality (Friendly, Professional, Formal, Sales, Technical Support), and language mode (Arabic, English, Bilingual).
- **FR-009**: System MUST enforce guardrails: restrict external knowledge by default, with optional competitor blocking and configurable escalation rules.

**Knowledge Management**

- **FR-010**: System MUST accept knowledge uploads in PDF, DOCX, TXT, CSV, and XLSX formats, and support URL scraping and manual Q&A entry.
- **FR-011**: Every file upload MUST pass a virus scan before any storage or processing occurs; infected files must be rejected and the admin notified.
- **FR-012**: Knowledge processing pipeline MUST execute: virus scan → storage → text extraction → normalization → chunking → embedding → vector storage → Ready status.
- **FR-013**: Every knowledge update MUST create a new version with a version number, change log, and rollback point — enabling restore to any prior version.

**RAG Engine**

- **FR-014**: The retrieval pipeline MUST execute: intent detection → query rewrite → embedding → hybrid vector + keyword search → re-ranking (cross encoder) → context assembly → LLM response.
- **FR-015**: System MUST apply context compression and token optimization before passing context to the LLM.

**Conversation Intelligence**

- **FR-016**: System MUST classify each message with an intent (FAQ, Complaint, Purchase Intent, Refund Request, Booking Request, Escalation Request, Unknown), sentiment (Positive/Neutral/Negative with 0–100 score), and urgency (Low/Medium/High/Critical).

**Human Handoff**

- **FR-017**: System MUST automatically escalate conversations when: AI confidence falls below the configured threshold, negative sentiment is detected, a complaint intent is classified, or the customer explicitly requests a human. The confidence threshold is configurable per-assistant by the Tenant Admin (default: 70%); when unset, the platform default applies.
- **FR-018**: System MUST support agent assignment strategies: Round Robin, Least Busy, and Skill-Based Routing.

**CRM & Lead Management**

- **FR-019**: System MUST auto-create a lead record when purchase intent is detected, capturing name, email, phone, channel, and estimated value where available.
- **FR-020**: System MUST provide a lead pipeline with stages: New → Contacted → Qualified → Proposal → Won/Lost, with stage transition logging.

**AI Training Center**

- **FR-021**: System MUST surface failed AI responses (low confidence, no retrieval, hallucination reports, downvotes) for admin review.
- **FR-022**: Admins MUST be able to provide a correct answer for any failed question, which is then embedded into the knowledge base and the question marked Resolved.

**Internationalization & RTL**

- **FR-032**: The admin dashboard and agent interface MUST support both English (LTR) and Arabic (RTL) layouts in Phase 1. Users MUST be able to switch between languages via a setting; all UI elements — forms, tables, navigation, modals — MUST mirror correctly in RTL mode. The platform MUST load Outfit font for English/LTR typography and Cairo font for Arabic/RTL typography. Font loading, line height, and character rendering MUST be validated for readability in both language modes.

**Widget Platform**

- **FR-023**: The embeddable widget MUST support Light, Dark, and Auto themes, unlimited color customization, configurable typography, and a custom greeting message.
- **FR-024**: Widget MUST support suggested questions, auto-open with delay, typing animation, read receipts, and an offline mode with a configurable message.

**Billing System**

- **FR-025**: System MUST support monthly and annual subscription plans via Stripe, with usage metering for messages, tokens, storage, assistants, and agents.
- **FR-026**: When a tenant reaches their monthly message limit, the system MUST continue serving AI conversations without interruption (soft allow). Overage messages are metered in real-time and charged automatically at the end of the billing cycle — no manual action required. The Tenant Admin MUST receive an in-app and email alert when usage crosses 80% and again at 100% of their plan limit.

**Notifications Engine**

- **FR-027**: System MUST deliver notifications via email and in-app channels for events: complaint received, lead created, subscription expiring, document processing failed, and agent assigned.

**Audit & Compliance**

- **FR-028**: System MUST maintain an immutable audit log of all significant actions: login/logout, file upload/delete, billing changes, user creation, and permission changes, with a minimum 365-day retention.
- **FR-033**: Tenant Admins MUST be able to export conversation history, lead records, and audit logs in CSV and JSON formats on demand. Exports MUST be scoped to the tenant's own data only. Knowledge base document export is out of scope for Phase 1.

**Security & RBAC**

- **FR-029**: System MUST enforce role-based access control with four roles — Super Admin, Tenant Admin, Agent, Viewer — each with strictly defined permission scopes. Super Admin access is restricted to platform-level operations: tenant management, billing administration, and system health. Super Admin MUST NOT have routine read access to tenant conversation data. Emergency access to tenant data (e.g., for critical support) MUST require an explicit break-glass procedure that is recorded as an immutable audit log entry visible to the Tenant Admin.
- **FR-030**: All data at rest MUST be encrypted with AES-256; secrets MUST be stored in a dedicated vault; backups MUST be encrypted.
- **FR-031**: The platform MUST be protected by WAF, rate limiting, DDoS mitigation, bot detection, and IP reputation filtering — applied at both the infrastructure/network layer (cloud provider controls) and the application layer (rate limiting middleware). Responsibility for network-layer protections is owned by the infrastructure team; application-layer rate limiting is owned by the backend service.

**CLI Administration Interface**

- **FR-034**: System MUST provide a command-line interface (CLI) exposing all administrative operations — tenant management, billing administration, and system health monitoring — enabling programmatic and scripted administration without the web dashboard.

### Key Entities

- **Tenant**: An isolated customer organization with its own workspace, billing, and data boundary. Attributes: id, name, industry, plan, created_at, status.
- **Workspace**: Per-tenant configuration container. Attributes: company info, branding assets, timezone, country.
- **Assistant**: AI agent configured per workspace. Attributes: name, avatar, personality, language_mode, guardrails configuration.
- **KnowledgeSource**: An uploaded or scraped content item. Attributes: type (document/url/qa), status, version, file_metadata.
- **KnowledgeVersion**: Immutable snapshot of the knowledge base at a point in time. Attributes: version_number, change_log, created_at, active flag.
- **Conversation**: A chat session between an end customer and the assistant or agent. Attributes: channel, status (AI/escalated/resolved), intent, sentiment, urgency.
- **Message**: A single turn in a conversation. Attributes: sender_type (user/assistant/agent), content, confidence_score, timestamp.
- **Lead**: A sales prospect auto-detected from conversation. Attributes: name, email, phone, channel, estimated_value, pipeline_stage.
- **HumanAgent**: A support team member who handles escalated conversations. Attributes: name, email, skills, availability_status.
- **Subscription**: A tenant's billing plan. Attributes: plan_type, billing_cycle, limits, current_usage, stripe_subscription_id.
- **AuditLog**: Immutable record of a system action. Attributes: actor, action_type, resource, timestamp, metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 80% of customer conversations are fully resolved by the AI without human escalation (AI deflection rate ≥ 80%).
- **SC-002**: AI responses are delivered to the end customer in under 5 seconds from message submission.
- **SC-003**: New tenants can complete registration, upload their first knowledge document, and have a live widget within a single session (target: under 30 minutes, no engineering assistance required).
- **SC-004**: Dashboard and admin pages load in under 2 seconds under normal operating conditions.
- **SC-005**: Platform supports 10,000 simultaneous tenant workspaces and 1,000,000 conversations per month without degradation.
- **SC-006**: 100 human agents can handle concurrent live escalations without system performance impact.
- **SC-007**: System achieves 99.9% uptime (standard tier) with a Recovery Time Objective of 1 hour and a Recovery Point Objective of 15 minutes.
- **SC-008**: Overage billing charges are applied automatically within 24 hours of the billing cycle evaluation — zero manual intervention.
- **SC-009**: Retrieval accuracy (correct knowledge chunk surfaced) is measurably tracked per tenant and reported in the analytics dashboard.
- **SC-010**: Audit logs are available for all tracked events within 365 days of occurrence, with zero gaps in coverage.

## Clarifications

### Session 2026-06-05

- Q: Must customer and conversation data be stored in a specific geographic region (GCC/MENA compliance)? → A: Region-selectable — tenants choose GCC region or Global cloud at signup.
- Q: When a tenant hits their monthly message limit mid-period, what happens to end customer conversations? → A: Soft allow with real-time overage metering — messages continue uninterrupted; overage is metered and charged at billing cycle end.
- Q: Can the Super Admin (platform operator) access individual tenant conversation data? → A: Platform-level access only — Super Admin manages tenants, billing, and system health; accessing tenant conversation data requires an audited emergency break-glass procedure logged in the audit trail.
- Q: Does the admin dashboard need Arabic/RTL support in Phase 1? → A: Yes — all admin and agent screens must support full Arabic/RTL layout and text in Phase 1.
- Q: Must tenants be able to export their data from the platform? → A: Structured export for conversations, leads, and audit logs in CSV/JSON format; knowledge base document export excluded from Phase 1.

## Assumptions

- Data residency is region-selectable per tenant (GCC or Global) at signup; region cannot be changed after workspace creation without a full data migration.
- Users are business decision-makers or technical administrators; end customers interacting with the widget are not platform users.
- The admin dashboard and agent interface must support full Arabic/RTL layout in Phase 1 alongside English/LTR — this is a Phase 1 requirement, not deferred.
- Mobile responsiveness of the admin dashboard is desirable but not P1 for the initial launch; the embeddable widget must be mobile-responsive.
- API Sync for knowledge sources is deferred to a future phase; all knowledge input is via upload, URL scrape, or manual Q&A entry in v1.
- Microsoft OAuth and SMS notifications are out of scope for Phase 1; these are acknowledged future features.
- Paddle and Lemon Squeezy billing providers are deferred to Phase 2; only Stripe is required for Phase 1.
- File upload (from end customers in the widget) is deferred to a future release.
- The LLM used for response generation is selected and configured at the infrastructure level; tenants do not choose or swap LLM providers.
- Bilingual (Arabic + English) detection is automatic based on customer message language; the assistant does not require a manual mode switch per-message.
- The "Restrict External Knowledge" guardrail is enabled by default for all new assistants and requires explicit admin action to disable.
- SLA Management, Feature Flags, API Keys Management, Webhook System, and Marketplace are in the enterprise roadmap but not included in Phase 1 functional scope.
- Knowledge base document export is out of scope for Phase 1; tenants can export conversations, leads, and audit logs only.
