# Phase 1 foundation boundary

The first implementation supports a manual tracking workflow before any external integration is configured. It performs no network extraction, LLM calls, portal actions or Sheet writes. This gives the owner a persistent dashboard without pretending Phase 1 acceptance is complete.

SQLAlchemy and Alembic own schema changes. The API does not create tables at startup. SQLite foreign-key enforcement is enabled, but models and constraints use portable SQL types. Postgres will additionally need its driver installed and a tested migration run; a connection-string change alone is not yet verified.

Each job gets one application and a creation event in the same transaction. Status updates use compare-and-swap and add history in that transaction. Only foundation statuses can be stored. This deliberately blocks `APPLIED` until a later migration adds confirmation evidence enforcement. Sponsorship is similarly restricted to `UNVERIFIED`; licensed-sponsor state is separately nullable and cannot be changed by the current API.

Facts have stable IDs and explicit owner review. Edits to content, source or category invalidate review even when a client tries to keep `verified=true`. Profile fields do not include legal declarations. No CV or profile is transmitted outside the machine.

An in-memory bearer token unlocks the UI; it is never built into browser assets, cookies, local storage or session storage. A same-origin Next.js route forwards the caller's bearer token to a fixed API destination. Both services bind to loopback. Reloading the browser requires unlocking again. All private API responses disable caching, validation errors omit submitted values, and dev API access logs are disabled.

Date-only deadlines are displayed without timezone shifts; reminders use the Europe/London calendar. The foundation only shows in-app reminders and does not change a job's status automatically. Unknown deadlines stay unknown.
