# Manual role-specific sponsorship evidence

19 November 2026. Phase 2 includes informational sponsorship evidence. Add an explicit local owner review instead of treating source wording or a company licence as an automatic confirmation. No new dependencies or hosted processing.

The owner selects Offered/Not offered, quotes the complete statement and its conditions, selects a saved source URL for the same vacancy, and confirms the finding. The API requires the quote to occur in saved description/requirements (whitespace-normalised, case-sensitive), mention sponsorship, and match the current vacancy fingerprint. Notes alone cannot be evidence. This checks provenance and consent; it does **not** establish the statement's meaning, immigration eligibility or employer accuracy. The owner must leave unclear/conditional policy Unverified. The review is not an automatic sponsorship classifier.

Store quote, source, UTC review time and fingerprint in the existing job_eligibility table. Hash URL, company, title, location, dates, description and requirements. Changed content makes evidence stale and the effective status Unverified, while retaining the previous quote for review. A separate clear action removes the review. Old unbound rows are not trusted. Changing Notes or application status alone does not invalidate source evidence. UI confirmation is bound to the fingerprint present when checked; a later background refresh cannot transfer that confirmation to changed text.

Keep jobs.sponsorship as the fail-closed intake field. API/UI effective status comes from current reviewed evidence; no automatic write of source statements to confirmation states. Matching does not consume evidence or licences, so this feature cannot penalise a job or change personal legal declarations. Listing findings open their evidence details. Licences remain a separate, unimplemented signal.

Migration 852ab936cd21 adds nullable fingerprint/time columns; legacy evidence and job/history records survive upgrade/downgrade. Use the existing backup/restore-verifying migration launcher. No live Google writes, portal interaction or environment changes.
