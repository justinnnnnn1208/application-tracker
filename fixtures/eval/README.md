# Real job-posting evaluation set

This directory is intentionally empty of job pages until about 30 genuine, individually reviewed postings have been saved. It is not a synthetic benchmark pass. Prioritise graduate/junior UK technology roles; sponsorship is informational and must not exclude a job. Do not save CVs, credentials, application forms or applicant data here.

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

Exit 2 means invalid/missing/less-than-30 data; exit 1 means extraction failures or false confirmed sponsorship; exit 0 means a full baseline run executed without those failures. **Exit 0 is not Phase 2 acceptance.** Graduate/sponsorship inference and scoring are not yet implemented, and overall thresholds have not been agreed. The baseline deliberately reports UNVERIFIED for those fields. Matching must wait for the real hand-labelled set required by SPEC.md. Sponsor information remains informational regardless of later scores; zero false CONFIRMED_YES stays a safety criterion.
