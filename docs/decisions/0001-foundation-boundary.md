# Phase 1 foundation boundary

The first implementation supports a manual tracking workflow before any external integration is configured. It performs no network extraction, LLM calls, portal actions or Sheet writes. This gives the owner a persistent dashboard without pretending Phase 1 acceptance is complete.

SQLAlchemy and Alembic own schema changes. The API does not create tables at startup. SQLite foreign-key enforcement is enabled, but models and constraints use portable SQL types. Postgres will additionally need its driver installed and a tested migration run; a connection-string change alone is not yet verified.

Each job gets one application and a creation event in the same transaction. Status updates use compare-and-swap and add history in that transaction. Only foundation statuses can be stored. This deliberately blocks `APPLIED` until a later migration adds confirmation evidence enforcement. Sponsorship is similarly restricted to `UNVERIFIED`; licensed-sponsor state is separately nullable and cannot be changed by the current API.

Facts have stable IDs and explicit owner review. Edits to content, source or category invalidate review even when a client tries to keep `verified=true`. Profile fields do not include legal declarations. No CV or profile is transmitted outside the machine.

The owner requested direct dashboard access instead of an unlock page. The Next.js server reads the private API bearer token from its environment and attaches it to backend requests. Browser code does not receive the credential, use authentication cookies or store it in local/session storage. Both services bind to loopback. The proxy permits loopback Host headers only, rejects cross-site Fetch Metadata and mismatched Origin values, and requires Origin on writes. Direct backend requests still need the token. This trusts users of the local machine; it is not suitable for shared or publicly exposed hosting. All private API responses disable caching, validation errors omit submitted values, and dev API access logs are disabled.

Date-only deadlines are displayed without timezone shifts; reminders use the Europe/London calendar. The foundation only shows in-app reminders and does not change a job's status automatically. Unknown deadlines stay unknown.
