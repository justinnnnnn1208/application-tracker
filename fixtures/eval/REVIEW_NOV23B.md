# Further genuine early-career controls — 23 November 2026

Four additional actual postings were fetched through the unchanged approved Greenhouse fetcher, with robots/rate/size/redirect checks. Candidate URLs came from the pinned SimplifyJobs lists in provenance-nov23.json. Original title/OG metadata/logo/header/description were excerpted; forms/scripts/buttons/inputs/SVG removed. Raw originals remain ignored, with hashes and capture times in provenance-nov23b.json. Labels were frozen before first prediction at a491c2d. No model, Google, owner database or form actions.

| Posting | Graduate label | Reason / other labels |
|---|---|---|
| Anduril 5255902007, 2027 Software Engineer Intern | UNVERIFIED | Internship for students graduating2028, not personal eligibility. No full job dates/policy. London header literal. |
| Cloudflare 8328914, Product Manager Intern (2027) - London, UK | UNVERIFIED | Explicit internship, not a leadership opening. May–September2027 is not an exact date. In-Office location is literal metadata, not geographic precision. Export-licence sponsorship is not employment-visa sponsorship. |
| SharkNinja 4726669006, Electronical Engineer Intern | UNVERIFIED | Internship. Official header spelling preserved; the description repeats a differently worded H1. August2027 is not an exact start day. No full deadline/policy. |
| Affirm 8011718003, Software Engineer I, Early Career (London) | YES | Explicit Early Career title and new cohort of graduates. No full dates. Explicit role-specific visa refusal quoted verbatim in the labels; automatic sponsorship still abstains. |

Initial report nov23b-initial-heldout.json retains one SharkNinja extraction failure and two missed role labels: graduate1/4, known-positive0/1; extraction failures stay in all denominators. These failures were recorded before code changes. The existing internship-Unverified and explicit early-career-YES rubric was applied; labels were not edited after prediction.

Fixes: description H1 subheadings no longer count as separate vacancy headers; conflicting headings outside the description still stop, as do different known posting identities. Explicit Early Career/Early-Career titles are recognised, and internship status precedes leadership-word checks. Senior non-intern programme managers remain NO. Score v7 makes old scores/feedback stale until recalculation, preserving Notes/events. These are role-level heuristics, not personal eligibility or semantic language understanding.

Subsequent controls/combined reports are consumed regressions, not independent held-out success. The combined manifest-nov23b.json contains48 genuine excerpts/12 employer labels, all Greenhouse, with12 known deadlines/3 shared-template exact start dates/35 known role labels. Four known sponsorship YES/15 NO labels remain unverified by the automatic predictor: zero false YES is abstention, not policy-assessment quality. No independent multi-ATS/date/model acceptance claim; phase_2_accepted=false.

## Geographic-location review (after code inspection)

Three Cloudflare labels originally measured the literal work-mode header (In-Office/Hybrid). That is insufficient for geographic matching: unchanged body sections explicitly give London, UK (8245211/8328914) and Lisbon, Portugal (8143649). A separate manifest-nov23-geographic.json updates these three labels; geographic-review-nov23.json records prior labels, same source hashes and post-inspection timing. Old manifests/reports are retained. This is an explicit annotation/field-interpretation refinement, not fresh held-out evidence.

Only a missing/work-mode header can fall back to a labelled Available Locations paragraph or its immediately following list. Concrete geographic headers, missing/conflicting sections and existing owner values are preserved. Public board API and pasted page use the same parsing rule. Ordinary city mentions in marketing are not used; multi-location list values are retained together. No new country/visa inference or owner-record rewrite. Against old literal labels location is45/48; against reviewed geographic labels48/48. Both are consumed regressions; no independent acceptance claim.
