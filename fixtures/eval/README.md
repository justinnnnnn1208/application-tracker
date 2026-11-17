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

Exit 2 means invalid/missing/less-than-30 data; exit 1 means extraction failures or false confirmed sponsorship; exit 0 means a full baseline run executed without those failures. **Exit 0 is not Phase 2 acceptance.** The extraction baseline deliberately reports UNVERIFIED for graduate/sponsorship fields. Add --role-classification to evaluate the local role-level classifier. Initial owner-agreed targets are at least 90% for deadline/location/graduate-role/start-date labels, and zero false CONFIRMED_YES. Exact start-day positive examples are absent; all null start dates matching must not be presented as demonstrated positive-date extraction. Reports include known-label counts/accuracy and YES prediction/label counts to expose abstention and unknown-label coverage. Sponsorship remains unverified in the app; four positive and fourteen negative sponsorship labels test future evidence assessment, not a shipped automatic confirmation feature. Sponsor information remains informational regardless of later scores; zero false CONFIRMED_YES stays a safety criterion.

The checked reports are in reports/. Both extraction and role-classification runs have zero extraction failures. Role-classification has 30/30 correct labels in the six basic/classification fields on this development set; sponsorship remains unverified (12/30 correct unknown labels, no YES predictions). These results helped develop the parser and classifier and are not independent generalisation scores. Refresh or add held-out sources before making broader quality claims.
