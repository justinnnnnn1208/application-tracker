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
    errors, false_yes, mismatches = 0, 0, []
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
            else:
                wrong.append(field)
        if actual.get("sponsorship") == "CONFIRMED_YES" and case.labels.sponsorship != "CONFIRMED_YES":
            false_yes += 1
        if wrong:
            mismatches.append({"id": case.id, "fields": wrong})
    total = len(cases)
    return {"pages": total, "dataset_ready": total >= 30, "extraction_failures": errors,
            "accuracy": {field: correct[field] / total if total else None for field in FIELDS},
            "false_confirmed_yes": false_yes, "mismatches": mismatches,
            "phase_2_accepted": False,
            "limits": ["Baseline extraction only; matching/scoring and graduate inference are not implemented.",
                       "Real-page labels, representative coverage and owner-agreed thresholds require review."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(load_cases(args.manifest))
    except (OSError, ValueError):
        print("Evaluation could not load validated local fixtures. Check paths, labels, quotes and checksums.")
        return 2
    print(json.dumps(report, indent=2))
    # Empty/small data is not a passing benchmark. Baseline reports never accept Phase 2.
    return 2 if not report["dataset_ready"] else 1 if report["extraction_failures"] or report["false_confirmed_yes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
