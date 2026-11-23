import hashlib
import json
from copy import deepcopy

import pytest

from app.services.evaluation import Case, evaluate, load_cases
from app.services.errors import NeedsInput


def fixture(tmp_path):
    html = '<p>No sponsorship is available for this role.</p><script type="application/ld+json">' + json.dumps({"@type": "JobPosting", "title": "Graduate Engineer", "hiringOrganization": {"name": "Fixture Company"}, "jobLocation": {"address": {"addressLocality": "Leeds"}}, "description": "Public fixture"}) + '</script>'
    (tmp_path / "job.html").write_text(html)
    item = {"id": "fixture-01", "url": "https://example.org/job?utm_source=test", "html": "job.html", "sha256": hashlib.sha256(html.encode()).hexdigest(), "captured_on": "2026-11-09", "reviewed_on": "2026-11-09", "labels": {"company": "Fixture Company", "title": "Graduate Engineer", "location": "Leeds", "deadline": None, "start_date": None, "graduate": "YES", "sponsorship": "CONFIRMED_NO", "sponsorship_quote": "No sponsorship is available for this role."}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"cases": [item]}))
    return path, item


def test_baseline_reports_unknowns_without_claiming_phase_acceptance(tmp_path):
    path, _ = fixture(tmp_path)
    result = evaluate(load_cases(path))
    assert result["pages"] == 1 and result["dataset_ready"] is False
    assert result["accuracy"]["deadline"] == 1 and result["accuracy"]["location"] == 1
    assert result["accuracy"]["graduate"] == 0 and result["accuracy"]["sponsorship"] == 0
    assert result["false_confirmed_yes"] == 0 and result["phase_2_accepted"] is False
    assert result["mismatches"] == [{"id": "fixture-01", "fields": ["graduate", "sponsorship"]}]


def test_false_sponsorship_confirmation_is_reported_separately(tmp_path):
    path, item = fixture(tmp_path)
    result = evaluate(load_cases(path), lambda *_: {**item["labels"], "sponsorship": "CONFIRMED_YES"})
    assert result["false_confirmed_yes"] == 1


def test_extraction_failures_remain_in_accuracy_denominator(tmp_path):
    path, _ = fixture(tmp_path)
    def failed(*_):
        raise NeedsInput("No metadata")
    result = evaluate(load_cases(path), failed)
    assert result["extraction_failures"] == 1
    assert all(value == 0 for value in result["accuracy"].values())
    assert evaluate([])["accuracy"]["location"] is None


@pytest.mark.parametrize("problem", ["path", "hash", "quote", "duplicate", "missing_evidence"])
def test_manifest_rejects_unreviewable_cases(tmp_path, problem):
    path, item = fixture(tmp_path)
    if problem == "path":
        item["html"] = "../outside.html"
    elif problem == "hash":
        item["sha256"] = "0" * 64
    elif problem == "quote":
        item["labels"]["sponsorship_quote"] = "Fabricated evidence"
    elif problem == "missing_evidence":
        item["labels"]["sponsorship_quote"] = ""
    cases = [item]
    if problem == "duplicate":
        duplicate = deepcopy(item)
        duplicate["id"] = "fixture-02"
        duplicate["url"] = "https://example.org/job?utm_campaign=duplicate"
        cases.append(duplicate)
    path.write_text(json.dumps({"cases": cases}))
    with pytest.raises(ValueError):
        load_cases(path)


def test_field_targets_do_not_hide_failed_known_dates_behind_null_matches(tmp_path):
    path, item = fixture(tmp_path)
    cases = load_cases(path) * 29
    positive = deepcopy(item)
    positive['id'] = 'positive-date'
    positive['labels']['deadline'] = '2026-12-01'
    positive['labels']['start_date'] = '2027-09-01'
    cases.append((Case.model_validate(positive), cases[0][1]))
    result = evaluate(cases, lambda *_: {**item['labels']})
    assert result['accuracy']['deadline'] == 29 / 30
    assert result['field_targets']['deadline']['state'] == 'FAILED'
    assert result['field_targets']['deadline']['known_accuracy'] == 0
    assert result['field_targets']['start_date']['state'] == 'FAILED'
    assert result['field_checks_passed'] is False
    assert result['phase_2_accepted'] is False


def test_absent_positive_dates_are_not_a_pass_even_when_all_nulls_match(tmp_path):
    path, item = fixture(tmp_path)
    result = evaluate(load_cases(path) * 30, lambda *_: item['labels'])
    assert result['field_targets']['deadline']['state'] == 'NOT TESTED'
    assert result['field_targets']['start_date']['state'] == 'NOT TESTED'
    assert result['field_targets']['location']['state'] == 'PASSED'
    assert result['field_checks_passed'] is None
    assert result['phase_2_accepted'] is False


def test_unknown_predictions_do_not_escape_field_target_denominator(tmp_path):
    path, item = fixture(tmp_path)
    positive = deepcopy(item)
    positive['labels']['deadline'] = '2026-12-01'
    positive['labels']['start_date'] = '2027-09-01'
    case = Case.model_validate(positive)
    result = evaluate([(case, load_cases(path)[0][1])] * 30, lambda *_: item['labels'])
    assert result['field_targets']['deadline']['state'] == 'FAILED'
    assert result['field_targets']['start_date']['state'] == 'FAILED'
    assert result['field_checks_passed'] is False


@pytest.mark.parametrize(('field', 'value', 'expected_exit', 'expected_state'), [
    ('deadline', None, 1, 'FAILED'),
    ('graduate', 'UNVERIFIED', 1, 'FAILED'),
    ('start_date', '2027-09-01', 0, 'PASSED'),
])
def test_cli_fails_missed_field_targets_without_claiming_acceptance(tmp_path, monkeypatch, capsys, field, value, expected_exit, expected_state):
    from app.services import evaluation
    path, item = fixture(tmp_path)
    positive = deepcopy(item)
    positive['labels'].update(deadline='2026-12-01', start_date='2027-09-01')
    source = load_cases(path)[0][1]
    cases = [(Case.model_validate(positive), source)] * 30
    actual = {**positive['labels'], field: value}
    monkeypatch.setattr(evaluation, 'load_cases', lambda _: cases)
    monkeypatch.setattr(evaluation, 'baseline', lambda *_: actual)
    monkeypatch.setattr('sys.argv', ['evaluation', '--manifest', str(path)])
    assert evaluation.main() == expected_exit
    report = json.loads(capsys.readouterr().out)
    assert report['field_targets'][field]['state'] == expected_state
    assert report['phase_2_accepted'] is False


def test_cli_missing_known_dates_returns_not_tested(tmp_path, monkeypatch, capsys):
    from app.services import evaluation
    path, item = fixture(tmp_path)
    cases = load_cases(path) * 30
    monkeypatch.setattr(evaluation, 'load_cases', lambda _: cases)
    monkeypatch.setattr(evaluation, 'baseline', lambda *_: item['labels'])
    monkeypatch.setattr('sys.argv', ['evaluation', '--manifest', str(path)])
    assert evaluation.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report['field_checks_passed'] is None
    assert report['phase_2_accepted'] is False
