"""Evaluate a local model on validated public snapshots, never the owner database."""
import argparse
from datetime import date
import json
from pathlib import Path

from pydantic import Field, model_validator

from app.schemas import Nonempty, RequirementsData, StrictModel
from app.services.errors import NeedsInput
from app.services.evaluation import load_cases
from app.services.extraction import extract_job
from app.services.matching import contains
from app.services import requirements


class ReviewCase(StrictModel):
    id: Nonempty
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    must_include_skills: list[Nonempty] = Field(max_length=100)
    empty_skills: bool
    forbidden_skills: list[Nonempty] = Field(max_length=100)
    note: Nonempty

    @model_validator(mode='after')
    def consistent(self):
        expected = {term.casefold() for term in self.must_include_skills}
        forbidden = {term.casefold() for term in self.forbidden_skills}
        if self.empty_skills and expected or expected & forbidden or len(expected) != len(self.must_include_skills):
            raise ValueError('Inconsistent manual technology labels')
        return self


class Review(StrictModel):
    reviewed_on: date
    notes: Nonempty
    cases: list[ReviewCase] = Field(min_length=1, max_length=100)


def load_review(path, cases):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError('Review file too large')
    review = Review.model_validate_json(path.read_text())
    by_id = {case.id: (case, html) for case, html in cases}
    seen = set()
    for item in review.cases:
        if item.id in seen or item.id not in by_id:
            raise ValueError('Duplicate or missing reviewed case')
        seen.add(item.id)
        case, html = by_id[item.id]
        if item.sha256 != case.sha256:
            raise ValueError('Review labels refer to a different source version')
        job = extract_job(case.url, html)
        source = requirements.public_text(job)
        if any(not contains(source, term) for term in item.must_include_skills + item.forbidden_skills):
            raise ValueError('Manual expected terms must occur in the validated source')
    return review


def evaluate(cases, review, predict=None, progress=None):
    predict = predict or requirements.extract
    by_id = {case.id: (case, html) for case, html in cases}
    results, valid, expected_count, found_count, empty_count, empty_correct, forbidden_count = [], 0, 0, 0, 0, 0, 0
    unavailable = None
    for item in review.cases:
        case, html = by_id[item.id]
        expected_count += len(item.must_include_skills)
        empty_count += int(item.empty_skills)
        result = {'id': item.id, 'source_sha256': case.sha256, 'state': 'failed', 'checks_passed': False, 'missing_skills': item.must_include_skills, 'forbidden_skills': []}
        try:
            if unavailable:
                raise requirements.LocalModelUnavailable(reason=unavailable)
            job = extract_job(case.url, html)
            text = requirements.public_text(job)
            data, model, chars, truncated = predict(text)
            data = RequirementsData.model_validate(data.model_dump()).grounded(text[:requirements.MAX_CHARS])
            values = [term.value for term in data.skills]
            missing = [term for term in item.must_include_skills if not any(contains(value, term) for value in values)]
            forbidden = [term for term in item.forbidden_skills if any(contains(value, term) for value in values)]
            valid += 1
            found_count += len(item.must_include_skills) - len(missing)
            empty_correct += int(item.empty_skills and not values)
            forbidden_count += len(forbidden)
            result.update(state='validated', model=model, source_chars=chars, truncated=truncated,
                          checks_passed=not missing and not forbidden and (not item.empty_skills or not values),
                          skills=data.model_dump()['skills'], missing_skills=missing, forbidden_skills=forbidden,
                          expected_empty=item.empty_skills, empty_correct=not values if item.empty_skills else None)
        except requirements.LocalModelUnavailable as error:
            unavailable = error.reason
            result.update(state='not_tested', checks_passed=None, missing_skills=None, forbidden_skills=None,
                          error_code=unavailable, error=requirements.MODEL_SETUP_HINTS[unavailable])
        except (NeedsInput, ValueError):
            # No model/source bodies or private configuration in errors/progress.
            result['error'] = 'Local extraction unavailable or output failed validation.'
        results.append(result)
        if progress:
            progress(item.id, 'NOT TESTED' if result['checks_passed'] is None else 'PASSED limited checks' if result['checks_passed'] else 'FAILED limited checks')
    not_tested = sum(row['state'] == 'not_tested' for row in results)
    failed_checks = sum(row['checks_passed'] is False for row in results)
    return {'cases': len(review.cases), 'schema_grounding_valid': valid, 'failed': len(review.cases) - valid - not_tested,
            'development_checks_passed': False if failed_checks else None if not_tested else True,
            'cases_failing_development_checks': failed_checks,
            'not_tested': not_tested, 'quality_assessed': not unavailable,
            'unavailable_reason': unavailable, 'setup_hint': requirements.MODEL_SETUP_HINTS.get(unavailable),
            'expected_skill_terms': expected_count, 'found_expected_terms': found_count,
            'minimum_term_recall': found_count / expected_count if expected_count and not unavailable else None,
            'expected_empty_cases': empty_count, 'correct_empty_cases': empty_correct,
            'empty_case_accuracy': empty_correct / empty_count if empty_count and not unavailable else None,
            'forbidden_terms_returned': forbidden_count, 'results': results, 'phase_2_accepted': False,
            'limits': ['Public saved pages only; this runner never opens the application DB/profile/Notes/CVs.',
                       'Minimum named-term recall and empty-case checks do not measure every requirement or semantic precision.',
                       'Small development subset; education/experience semantics and independent multi-ATS model quality are not certified.',
                       'Schema/source grounding alone does not establish model quality or applicant eligibility.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New JSON report path; existing files are never overwritten')
    args = parser.parse_args()
    if not requirements.configuration():
        print('NOT TESTED: configure a local Ollama model first. No remote calls or application database access attempted.')
        return 2
    try:
        if args.output.exists():
            raise ValueError('Output already exists')
        cases = load_cases(args.manifest)
        review = load_review(args.review, cases)
        report = evaluate(cases, review, progress=lambda id, state: print(f'{id}: {state}', flush=True))
        args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with args.output.open('x', encoding='utf-8') as file:
            file.write(json.dumps(report, indent=2) + '\n')
        args.output.chmod(0o600)
    except (OSError, ValueError):
        print('Evaluation inputs/output could not be validated. Check paths, checksums, review labels and use a new output filename.')
        return 2
    print(f"{report['schema_grounding_valid']}/{report['cases']} schema/grounding-valid; minimum term recall {report['minimum_term_recall']}; empty-case accuracy {report['empty_case_accuracy']}; Phase 2 acceptance remains unassessed.")
    print(f"Limited development checks: {'FAILED' if report['development_checks_passed'] is False else 'NOT TESTED' if report['development_checks_passed'] is None else 'PASSED'}; {report['cases_failing_development_checks']} cases failed checks. This is not Phase 2 acceptance.")
    if report['not_tested']:
        print(f"NOT TESTED [{report['unavailable_reason']}]: {report['setup_hint']}")
        print('No semantic-quality pass/fail conclusion; fix local setup and request another check.')
        return 2
    return 0 if report['development_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
