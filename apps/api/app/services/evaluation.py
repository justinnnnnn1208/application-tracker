"""Offline extraction benchmark. Saved public pages are data, never executable code."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.schemas import StrictModel
from app.services.errors import NeedsInput
from app.services.extraction import extract_job, plain_html
from app.services.urls import canonical_url


class Labels(StrictModel):
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    location: str
    deadline: date | None
    start_date: date | None
    graduate: Literal["YES", "NO", "UNVERIFIED"]
    sponsorship: Literal["CONFIRMED_YES", "CONFIRMED_NO", "UNVERIFIED"]
    sponsorship_quote: str = ""

    @model_validator(mode="after")
    def evidence(self):
        if self.sponsorship != "UNVERIFIED" and not self.sponsorship_quote:
            raise ValueError("Confirmed sponsorship labels require a verbatim evidence quote")
        return self


class Case(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    url: str
    html: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    captured_on: date
    reviewed_on: date
    labels: Labels


class Manifest(StrictModel):
    cases: list[Case]


def load_cases(path):
    path = Path(path).resolve()
    if path.stat().st_size > 4_000_000:
        raise ValueError("Manifest exceeds size limit")
    manifest = Manifest.model_validate_json(path.read_text())
    cases, ids, urls = [], set(), set()
    for item in manifest.cases:
        url = canonical_url(item.url)
        if item.id in ids or url in urls:
            raise ValueError("Duplicate case ID or canonical URL")
        ids.add(item.id)
        urls.add(url)
        page = (path.parent / item.html).resolve()
        if not page.is_relative_to(path.parent) or not page.is_file() or page.stat().st_size > 1_000_000:
            raise ValueError("Page must be a bounded file inside the evaluation directory")
        data = page.read_bytes()
        if hashlib.sha256(data).hexdigest() != item.sha256:
            raise ValueError("Page checksum differs from reviewed version")
        html = data.decode("utf-8")
        quote = item.labels.sponsorship_quote
        if quote and " ".join(quote.split()) not in " ".join(plain_html(html).split()):
            raise ValueError("Sponsorship evidence quote is absent from saved page text")
        cases.append((item, html))
    return cases


FIELDS = ("company", "title", "location", "deadline", "start_date", "graduate", "sponsorship")


def normal(value):
    if isinstance(value, date):
        return value.isoformat()
    return " ".join(value.split()).casefold() if isinstance(value, str) else value


def baseline(url, html):
    # No provider is constructed: this baseline never calls hosted APIs or infers eligibility.
    return {**extract_job(url, html).model_dump(), "graduate": "UNVERIFIED", "sponsorship": "UNVERIFIED"}


def evaluate(cases, predict=baseline):
    correct = {field: 0 for field in FIELDS}
    errors, false_yes, predicted_yes, mismatches = 0, 0, 0, []
    known = {field: sum(getattr(case.labels, field) not in (None, "", "UNVERIFIED") for case, _ in cases) for field in FIELDS}
    correct_known = {field: 0 for field in FIELDS}
    for case, html in cases:
        try:
            actual = predict(canonical_url(case.url), html)
        except (NeedsInput, ValueError):
            errors += 1
            mismatches.append({"id": case.id, "fields": ["extraction_failed"]})
            continue
        wrong = []
        for field in FIELDS:
            if normal(actual.get(field)) == normal(getattr(case.labels, field)):
                correct[field] += 1
                if getattr(case.labels, field) not in (None, "", "UNVERIFIED"):
                    correct_known[field] += 1
            else:
                wrong.append(field)
        if actual.get("sponsorship") == "CONFIRMED_YES":
            predicted_yes += 1
        if actual.get("sponsorship") == "CONFIRMED_YES" and case.labels.sponsorship != "CONFIRMED_YES":
            false_yes += 1
        if wrong:
            mismatches.append({"id": case.id, "fields": wrong})
    total = len(cases)
    return {"pages": total, "dataset_ready": total >= 30, "extraction_failures": errors,
            "accuracy": {field: correct[field] / total if total else None for field in FIELDS},
            "known_labels": known, "known_label_accuracy": {field: correct_known[field] / known[field] if known[field] else None for field in FIELDS},
            "predicted_confirmed_yes": predicted_yes, "labelled_confirmed_yes": sum(case.labels.sponsorship == "CONFIRMED_YES" for case, _ in cases),
            "false_confirmed_yes": false_yes, "mismatches": mismatches,
            "phase_2_accepted": False,
            "limits": ["Field/role labels from the supplied predictor only; applicant eligibility and production-score accuracy are not assessed.",
                       "Real-page labels, representative coverage and owner-agreed thresholds require review."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--role-classification", action="store_true", help="Include the local role-level classifier (not personal eligibility)")
    args = parser.parse_args()
    try:
        predict = baseline
        if args.role_classification:
            from app.services.matching import graduate_level
            def predict(url, html):
                data = baseline(url, html)
                data["graduate"] = graduate_level(data["title"], data["description"])
                return data
        cases = load_cases(args.manifest)
        report = evaluate(cases, predict)
        report["mode"] = "role-classification" if args.role_classification else "extraction-baseline"
        report["limits"] = [f"Saved-page evaluation: {len(cases)} postings and {len({case.labels.company for case, _ in cases})} employer labels. See accompanying review for development/held-out status and ATS coverage.", "Automatic sponsorship remains UNVERIFIED; zero false YES is not proof of evidence-assessment or manual-review quality.", f"Exact start-date labels: {report['known_labels']['start_date']}. Null matches do not demonstrate positive-date extraction; shared-template examples do not establish generalisation.", "Field targets: at least 0.9 for deadline/location/graduate/start_date; zero false confirmed YES. Full Phase 2 scope still incomplete."]
    except (OSError, ValueError):
        print("Evaluation could not load validated local fixtures. Check paths, labels, quotes and checksums.")
        return 2
    print(json.dumps(report, indent=2))
    # Empty/small data is not a passing benchmark. Baseline reports never accept Phase 2.
    return 2 if not report["dataset_ready"] else 1 if report["extraction_failures"] or report["false_confirmed_yes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
