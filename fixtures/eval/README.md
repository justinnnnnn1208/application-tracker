# Real job-posting evaluation set

This directory contains 30 genuine posting snapshots captured and reviewed on 17 November 2026, from Graphcore, Canonical, Monzo and Deliveroo. These form an initial development set on Greenhouse, not a held-out or multi-ATS benchmark. See LABEL_REVIEW.md and provenance.json. Prioritise graduate/junior UK technology roles; sponsorship is informational and must not exclude a job. Snapshots retain original header metadata, company logo and visible job header/description only. Application forms, scripts, tracking/asset markup and applicant data are excluded. No generated job metadata was added. Raw-response hashes record provenance; raw responses remain ignored locally. Do not save CVs or credentials here.

Save public individual vacancy HTML under this directory, respecting source terms and robots rules. Do not scrape LinkedIn/Indeed, bypass access restrictions or save search/results pages as vacancies. Record the actual source URL, capture/review dates and SHA-256 of the saved bytes. Retain enough page text to verify each label. Unknown dates are null; unknown sponsorship/graduate eligibility is UNVERIFIED. A sponsor licence or old sponsorship history never establishes role-specific confirmation.

Add entries to manifest.json using this shape (illustrative only, not an actual posting):

```json
{
  "id": "reviewed-posting-01",
  "url": "https://employer.example/jobs/actual-vacancy-id",
  "html": "posting-01.html",
  "sha256": "replace-with-64-character-sha256",
  "captured_on": "2026-11-09",
  "reviewed_on": "2026-11-09",
  "labels": {
    "company": "Verbatim company",
    "title": "Verbatim role title",
    "location": "Verbatim location in extractor format",
    "deadline": null,
    "start_date": null,
    "graduate": "UNVERIFIED",
    "sponsorship": "UNVERIFIED",
    "sponsorship_quote": ""
  }
}
```

Use YES/NO/UNVERIFIED for graduate eligibility; CONFIRMED_YES/CONFIRMED_NO/UNVERIFIED for sponsorship. Confirmed sponsorship needs an exact visible-page quote. Each saved vacancy must have a unique canonical URL. Include positive, negative and unknown examples, multiple ATS sources, missing metadata and dates. Review diversity and label correctness before treating accuracy as representative.

From apps/api:

```sh
uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest.json
```

This offline baseline calls the existing structured extractor without a provider. It never fetches pages, calls an LLM, evaluates legal declarations or creates jobs. It reports exact normalized field accuracy, extraction failures and false CONFIRMED_YES independently. Failure counts stay in the denominator. Text comparison ignores case and repeated whitespace; dates compare exactly. Reports include case IDs and field names, not page contents.

Exit 1 means extraction failures, false confirmed sponsorship, or an evaluated deadline/location/graduate/start-date field below 90% on either all labels or known labels. Exit 2 means invalid inputs, an otherwise non-failing sample below 30 pages, or absent known labels for a target field. Exit 0 means these limited development checks passed, not representative coverage. Field targets are reported separately with known-label counts; matching many null dates cannot hide failure on the known dates. **Exit 0 is not Phase 2 acceptance.** The extraction baseline deliberately reports UNVERIFIED for graduate/sponsorship fields. Add --role-classification to evaluate the local role-level classifier. Initial owner-agreed targets are at least 90% for deadline/location/graduate-role/start-date labels, and zero false CONFIRMED_YES. Exact start-day positive examples are absent; all null start dates matching must not be presented as demonstrated positive-date extraction. Reports include known-label counts/accuracy and YES prediction/label counts to expose abstention and unknown-label coverage. Sponsorship remains unverified in the app; four positive and fourteen negative sponsorship labels test future evidence assessment, not a shipped automatic confirmation feature. Sponsor information remains informational regardless of later scores; zero false CONFIRMED_YES stays a safety criterion.

The checked reports are in reports/. Both extraction and role-classification runs have zero extraction failures. Role-classification has 30/30 correct labels in the six basic/classification fields on this development set; sponsorship remains unverified (12/30 correct unknown labels, no YES predictions). These results helped develop the parser and classifier and are not independent generalisation scores. Refresh or add held-out sources before making broader quality claims.

Source text spacing is preserved, including trailing blanks between inline HTML nodes. A narrowly scoped .gitattributes rule permits those trailing blanks only for captured pages; code retains ordinary whitespace checks. Do not trim source nodes indiscriminately, since that can join words and change evidence quotes.

## 19 November expansion and honest held-out result

The original manifest remains frozen at 30 development cases. Five genuine Marshall Wace snapshots are added in heldout-nov19.json, with provenance-nov19.json and REVIEW_NOV19.md. Three state an exact start day, 6 September 2027; the two flexible date ranges remain null. The initial check at aaebca9 missed 3/3 positive dates (report retained). After adding month-first date support these five are consumed regression cases, not fresh held-out validation. manifest-expanded.json combines all 35. The expanded regression matches basic/role fields and all three exact dates, with zero false YES from abstaining automatic sponsorship predictions; it does not establish manual-review quality, multiple ATS coverage or Phase 2 acceptance.

Run the expanded regression with `uv run --frozen python -m app.services.evaluation --manifest ../../fixtures/eval/manifest-expanded.json --role-classification` from apps/api. New reports are named nov19-initial-heldout, nov19-original-regression and nov19-expanded-regression. Historical “no exact-day positives” statements above describe only the original 30-page set. Automatic sponsorship remains unverified; current owner-reviewed job evidence is a separate feature.

## Local requirement-model checks (20 November)

requirements-review.json contains manually reviewed minimum named-technology expectations and explicit empty/forbidden controls for nine real snapshots, with source hashes. This is a small development subset, not exhaustive education/experience labels or independent semantic precision. The local-only requirements_eval command in SETUP.md checks input hashes, term recall, false company-background terms and empty cases without reading the application DB/Notes/CVs. Unavailable models report NOT TESTED with unknown quality metrics and stop further calls. Current cloud execution had no Ollama server/model; no real-model quality pass is claimed.

20 November: `manifest-nov20.json` contains 38 real excerpts; the prior 30/35 manifests are frozen. Three new GoCardless controls had labels frozen before initial prediction (see REVIEW_NOV20.md, provenance-nov20.json and reports/nov20-initial-heldout.json). The 3-case-only probe exits 2 for insufficient dataset size, with correct field/role results; combined regression exits 0. Still one ATS and no additional positive exact dates or policy findings. These are regression inputs after inspection, not a renewed independent acceptance claim. Local requirement-model review remains the separate nine-case subset.

21 November: `manifest-nov21.json` combines 40 genuine excerpts/seven employer labels, all Greenhouse. Two Cloudflare pages exposed an official legacy/current og:url mismatch: initial 2/2 source failures retained. The source-identity fix and annotation correction are documented in REVIEW_NOV21.md and provenance-nov21.json; initial intern YES was corrected to the existing internship Unverified rubric, with original labels retained. These are consumed regressions, not fresh held-out success. Still 12 known deadlines/3 shared-template exact start days. Model review stays nine separate cases; all prior manifests/reports remain frozen. Use the latest combined manifest for current field/role regressions.

23 November: `manifest-nov23.json` adds four genuine early-career controls (44 total, nine employer labels, still Greenhouse). Labels were frozen before prediction. Initial control graduate accuracy was3/4, with the sole known New Grad positive missed; report preserved. Explicit New Grad title support and internship precedence fix those consumed regressions. No new positive exact days/deadlines; see REVIEW_NOV23.md and provenance. Two ambiguous publisher/employer-brand captures were excluded before prediction and this selection limitation is recorded. No independent multi-ATS/model acceptance claim.

23 November additional controls: manifest-nov23b.json combines48 genuine excerpts/12 employer labels, still Greenhouse only. Fresh labels frozen before prediction exposed a differently worded description H1 and missed Early Career/manager-intern levels. Initial failures are retained; fixes and limitations are in REVIEW_NOV23B.md. Exact dates remain3 shared-template positives; sponsorship has4 YES/15 NO labels and automatic abstention. Current reports are consumed regressions, not independent acceptance.
