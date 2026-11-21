from pathlib import Path
import pytest
from app.schemas import RequirementsData
from app.services.evaluation import load_cases
from app.services.requirements_eval import load_review, evaluate

ROOT = Path(__file__).resolve().parents[3]


def test_real_public_review_terms_are_source_backed_and_do_not_claim_phase_acceptance():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    assert len(review.cases)==9
    def abstain(text):
        return RequirementsData(),'fixture-not-real-model',len(text),False
    result=evaluate(cases,review,predict=abstain)
    assert result['schema_grounding_valid']==9
    assert result['minimum_term_recall']==0 and result['empty_case_accuracy']==1
    assert result['development_checks_passed'] is False and result['cases_failing_development_checks']>0
    assert result['phase_2_accepted'] is False


def test_validation_success_does_not_hide_company_background_false_positives():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    review.cases=[item for item in review.cases if item.id=='canonical-7661586']
    def wrong(text):
        return RequirementsData.model_validate({'skills':[{'value':'Ubuntu','quote':'Ubuntu is the fastest growing Linux distribution'}]}),'fixture',len(text),False
    result=evaluate(cases,review,predict=wrong)
    assert result['schema_grounding_valid']==1 and result['empty_case_accuracy']==0
    assert result['forbidden_terms_returned']==1
    assert result['development_checks_passed'] is False and result['results'][0]['checks_passed'] is False


def test_ungrounded_model_output_stays_in_failure_denominator():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    def invented(text):
        return RequirementsData.model_validate({'skills':[{'value':'FabricatedXYZ','quote':'FabricatedXYZ required.'}]}),'fixture',len(text),False
    result=evaluate(cases,review,predict=invented)
    assert result['schema_grounding_valid']==0 and result['failed']==9
    assert result['minimum_term_recall']==0 and result['empty_case_accuracy']==0


def test_duplicate_or_non_source_review_labels_are_rejected():
    from app.services.requirements_eval import Review
    with pytest.raises(ValueError):
        Review.model_validate({'reviewed_on':'2026-11-20','notes':'Fixture','cases':[{'id':'fixture','sha256':'0'*64,'must_include_skills':['Python'],'empty_skills':True,'forbidden_skills':[],'note':'Conflicting fixture'}]})


def test_unavailable_model_is_not_tested_and_stops_further_requests():
    from app.services.requirements import LocalModelUnavailable
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    calls=[]
    def unavailable(text):
        calls.append(text)
        raise LocalModelUnavailable('Local model unavailable')
    result=evaluate(cases,review,predict=unavailable)
    assert len(calls)==1 and result['not_tested']==9 and result['failed']==0
    assert result['minimum_term_recall'] is None and result['empty_case_accuracy'] is None
    assert result['quality_assessed'] is False and result['phase_2_accepted'] is False
    assert result['development_checks_passed'] is None and result['cases_failing_development_checks']==0
    assert all(row['checks_passed'] is None for row in result['results'])
    assert all(row['missing_skills'] is None and row['forbidden_skills'] is None for row in result['results'])


def test_changed_snapshot_hash_cannot_reuse_old_review_labels(tmp_path):
    import json
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    labels=json.loads((ROOT/'fixtures/eval/requirements-review.json').read_text())
    labels['cases'][0]['sha256']='0'*64
    path=tmp_path/'review.json';path.write_text(json.dumps(labels))
    with pytest.raises(ValueError,match='different source version'):
        load_review(path,cases)


def test_passing_limited_checks_are_explicit_but_do_not_accept_phase_two():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    review.cases=[item for item in review.cases if item.empty_skills]
    seen=[]
    def abstain(text):
        return RequirementsData(),'synthetic-protocol-fixture',len(text),False
    result=evaluate(cases,review,predict=abstain,progress=lambda id,state:seen.append(state))
    assert result['development_checks_passed'] is True and result['cases_failing_development_checks']==0
    assert all(row['checks_passed'] is True for row in result['results'])
    assert seen==['PASSED limited checks']*len(review.cases)
    assert result['phase_2_accepted'] is False


def test_unavailable_reason_is_preserved_across_skips_without_echoing_exception_details():
    from app.services.requirements import LocalModelUnavailable
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    calls=[]
    def unavailable(text):
        calls.append(text)
        raise LocalModelUnavailable('SYNTHETIC_PRIVATE_RESPONSE_MARKER',reason='timed_out')
    result=evaluate(cases,review,predict=unavailable)
    assert len(calls)==1 and result['unavailable_reason']=='timed_out'
    assert result['not_tested']==9 and result['minimum_term_recall'] is None
    assert all(row['error_code']=='timed_out' for row in result['results'])
    assert 'SYNTHETIC_PRIVATE' not in str(result)
    assert 'ollama run' in result['setup_hint']


def test_fail_fast_records_one_failure_and_marks_remaining_cases_untested():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    calls=[]
    def wrong(text):
        calls.append(text);return RequirementsData(),'synthetic',len(text),False
    report=evaluate(cases,review,predict=wrong,fail_fast=True)
    assert len(calls)==1 and report['completed_cases']==1 and report['not_tested']==8
    assert report['stopped_after_failure'] is True and report['development_checks_passed'] is False
    assert report['cases_failing_development_checks']==1 and report['minimum_term_recall'] is None
    assert report['quality_assessed'] is False and report['unavailable_reason'] is None
    assert all(row['error_code']=='stopped_after_failure' for row in report['results'][1:])
    assert report['phase_2_accepted'] is False


def test_fail_fast_does_not_stop_passing_cases_or_claim_phase_acceptance():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    review.cases=[item for item in review.cases if item.empty_skills]
    report=evaluate(cases,review,predict=lambda text:(RequirementsData(),'synthetic',len(text),False),fail_fast=True)
    assert report['not_tested']==0 and report['completed_cases']==len(review.cases)
    assert report['stopped_after_failure'] is False and report['development_checks_passed'] is True
    assert report['phase_2_accepted'] is False
