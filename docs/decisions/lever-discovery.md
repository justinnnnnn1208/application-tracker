# Bounded public Lever discovery

19 November 2026. Phase 2 calls for multiple public ATS APIs. Add a GET-only Lever adapter using the existing fetcher/worker/identity path; no new dependencies, form interaction, application API or credentials.

Contract reference: https://github.com/lever/postings-api (README retrieved 19 November 2026, SHA-256 504ed95b1dc39c5a4c0865d05805a6cdff57a973bdb6d7c3fe376ff177b15764). Only the documented GET postings fields/pagination are used. This document's application POST examples are not part of this implementation.

Choose global or EU explicitly. Require the employer display name from the board, because the documented posting response does not provide it; never fabricate it from the slug. Greenhouse may use the same optional name only when its response omits the employer. Existing sources migrate with empty fallback name/global region and retain enabled state.

Read at most 20 pages of 100 postings, through the unchanged public-host/DNS/robots/rate/size/TLS guards. A full last page, repeated posting identity, malformed page or denied later request fails before any partial import is saved. Invalid individual rows are counted. Hosted listing URL must be HTTPS, match provider region/board/UUID and be a listing rather than an application form. applyUrl is never fetched or used. Known ATS identity dedupes against already-pasted apply URLs while retaining both sources and owner history.

Preserve supplied description, requirement lists, closing text and explicit locations. Parse only complete labelled dates; missing day/year stays unknown. No sponsorship inference, filtering or scoring changes. Imports remain manual/opt-in and import the board's published jobs; use existing preference scores afterwards.

Verification: synthetic contract fixtures in fixtures/discovery (explicitly not real jobs/evaluation data), parser/pagination/atomicity/worker/API/migration tests and browser source-configuration coverage. Live api.lever.co robots access was blocked by this cloud proxy with CONNECT 403. No network policy/DNS fallback was changed or bypassed; live Lever compatibility and real multi-ATS evaluation remain NOT TESTED. The existing 30 genuine Greenhouse development snapshots are separate.
