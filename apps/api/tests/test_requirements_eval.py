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
    assert seen==['CHECKING local setup and public extraction','PASSED limited checks']*len(review.cases)
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


def test_targeted_case_preserves_skipped_coverage():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    calls=[]
    def predict(text):
        calls.append(text);return RequirementsData(),'synthetic',len(text),False
    report=evaluate(cases,review,predict=predict,case_id='canonical-7661586',fail_fast=True)
    assert len(calls)==1 and 'Sales Development Representative' in calls[0]
    assert report['completed_cases']==1 and report['not_tested']==8 and report['schema_grounding_valid']==1
    assert report['development_checks_passed'] is None and report['quality_assessed'] is False
    assert report['minimum_term_recall'] is None and report['empty_case_accuracy'] is None
    assert report['phase_2_accepted'] is False
    assert all(row['error_code']=='not_selected' for row in report['results'] if row['id']!='canonical-7661586')


def test_unknown_target_case_fails_before_model_calls():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    with pytest.raises(ValueError,match='reviewed case'):
        evaluate(cases,review,predict=lambda _:pytest.fail('No model call'),case_id='unknown')


@pytest.mark.parametrize('valid',[True,False])
@pytest.mark.parametrize('explain',[False,True])
def test_targeted_native_cli_never_turns_one_case_into_a_full_pass(tmp_path,valid,explain):
    import json,os,subprocess,sys
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    from threading import Thread
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append((self.path,body))
            if self.path=='/api/show':
                assert body=={'model':'synthetic-case-fixture'}
                payload={'model_info':{'general.architecture':'fixture'}}
            else:
                assert self.path=='/api/chat' and 'Sales Development Representative' in body['messages'][-1]['content']
                skills=[] if valid else [{'value':'Ubuntu','quote':'Ubuntu is the fastest growing Linux distribution'}]
                data={'skills':skills}
                if explain and not valid:
                    import re
                    words=list(dict.fromkeys(word.casefold() for word in re.findall(r'\b[A-Za-z]{4,}\b',body['messages'][-1]['content'])))[:5]
                    data={'skills':[], 'experience':[{'value':word,'quote':word} for word in words]+[{'value':'syntheticpublicmismatch','quote':'Synthetic public mismatch \u001b[31m'}]}
                payload={'done':True,'message':{'content':json.dumps(data)}}
            raw=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    report_path=tmp_path/'public.json'
    try:
        env={'PATH':os.environ['PATH'],'LLM_PROVIDER':'ollama','LLM_MODEL':'synthetic-case-fixture','LLM_BASE_URL':f'http://127.0.0.1:{server.server_port}/v1'}
        result=subprocess.run([sys.executable,'-m','app.services.requirements_eval','--manifest',str(ROOT/('fixtures/eval/manifest-nov20.json' if explain else 'fixtures/eval/manifest-nov21.json')),'--review',str(ROOT/'fixtures/eval/requirements-review.json'),'--output',str(report_path),'--case','canonical-7661586','--fail-fast','--single-attempt']+(['--explain-failure'] if explain else []),env=env,capture_output=True,text=True,timeout=15)
        report=json.loads(report_path.read_text())
        assert result.returncode==(2 if valid else 1)
        assert report['completed_cases']==1 and report['not_tested']==8 and report['phase_2_accepted'] is False
        assert report['results'][1]['checks_passed'] is valid
        selected=report['results'][1]
        if explain and not valid:
            assert selected['rejected_public_entry']['field']=='experience.5.quote:quote_not_in_source'
            assert 'Rejected public entry (untrusted model text):' in result.stdout
            assert '\x1b' not in result.stdout and '\\u001b' in result.stdout
        else:
            assert 'rejected_public_entry' not in selected
            assert 'Rejected public entry' not in result.stdout
        assert report['results'][1]['elapsed_seconds'] >= 0
        assert 'canonical-7661586: CHECKING local setup and public extraction' in result.stdout
        assert 'Check elapsed (setup + extraction): canonical-7661586' in result.stdout
        assert report['minimum_term_recall'] is None and report['empty_case_accuracy'] is None
        assert not report['stopped_after_failure']
        assert [path for path,_ in calls]==['/api/show','/api/chat']
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


def test_progress_announces_selected_case_before_slow_model_work():
    cases=load_cases(ROOT/'fixtures/eval/manifest-expanded.json')
    review=load_review(ROOT/'fixtures/eval/requirements-review.json',cases)
    seen=[]
    def predict(text):
        assert seen[-1]==('canonical-7661586','CHECKING local setup and public extraction')
        return RequirementsData(),'synthetic',len(text),False
    report=evaluate(cases,review,predict=predict,case_id='canonical-7661586',progress=lambda id,state:seen.append((id,state)))
    result=next(row for row in report['results'] if row['id']=='canonical-7661586')
    assert result['elapsed_seconds']>=0
    assert all('elapsed_seconds' not in row for row in report['results'] if row['id']!='canonical-7661586')
    assert report['not_tested']==8 and report['phase_2_accepted'] is False


@pytest.mark.parametrize('case',[None,'canonical-7661586'])
def test_failure_explanation_refuses_nonbundled_inputs_before_configuration_or_model(tmp_path,monkeypatch,case):
    from app.services import requirements_eval as runner
    monkeypatch.setattr(runner.requirements,'configuration',lambda:pytest.fail('Do not reach model setup for unsupported private/custom inputs'))
    args=['requirements_eval','--manifest',str(tmp_path/'private.json'),'--review',str(tmp_path/'private-review.json'),'--output',str(tmp_path/'out.json'),'--explain-failure']
    if case:args+=['--case',case]
    monkeypatch.setattr('sys.argv',args)
    with pytest.raises(SystemExit) as error:runner.main()
    assert error.value.code==2


@pytest.mark.parametrize('final',['validated','output_limit'])
def test_explanation_does_not_publish_an_earlier_retry_when_final_result_changes(tmp_path,monkeypatch,capsys,final):
    import json
    from app.services import requirements_eval as runner
    monkeypatch.setattr(runner.requirements,'configuration',lambda:('http://127.0.0.1:11434/api/chat','synthetic'))
    def extract(text,**kwargs):
        kwargs['on_grounding_failure']({'field':'experience.0.quote:quote_not_in_source','reason':'quote_not_in_source','value':'Earlier entry','quote':'Earlier rejected synthetic marker'})
        if final=='output_limit':raise runner.requirements.InvalidRequirementsOutput('output_limit',3)
        return RequirementsData(),'synthetic',len(text),False
    monkeypatch.setattr(runner.requirements,'extract',extract)
    output=tmp_path/'report.json'
    monkeypatch.setattr('sys.argv',['requirements_eval','--manifest',str(ROOT/'fixtures/eval/manifest-nov20.json'),'--review',str(ROOT/'fixtures/eval/requirements-review.json'),'--output',str(output),'--case','canonical-7661586','--explain-failure'])
    assert runner.main()==(2 if final=='validated' else 1)
    report=json.loads(output.read_text())
    assert all('rejected_public_entry' not in row for row in report['results'])
    assert 'Earlier rejected synthetic marker' not in output.read_text()+capsys.readouterr().out
