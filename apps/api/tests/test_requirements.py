import json
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy.orm import Session

from app.db.models import Job, JobRequirements
from app.schemas import RequirementsData
from app.services import requirements
from app.services.errors import NeedsInput
from app.worker.tasks import run_once


def model_transport(handle):
    # Existing output/retry tests focus on generation; supply explicit synthetic
    # local metadata. Separate selection tests exercise refusal/metadata failures.
    def route(request):
        if request.url.path == '/api/show':
            assert set(json.loads(request.content)) == {'model'}
            return httpx.Response(200, json={'model_info': {'general.architecture': 'fixture'}})
        return handle(request)
    return httpx.MockTransport(route)


def configure(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ollama')
    monkeypatch.setenv('LLM_MODEL', 'qwen2.5:3b')
    monkeypatch.setenv('LLM_BASE_URL', 'http://127.0.0.1:11434/v1')


def output():
    return {'skills': [{'value': 'Elixir', 'quote': 'Elixir and PostgreSQL required.'}], 'education': [], 'experience': []}


def create(client, **extra):
    return client.post('/api/jobs', json={'url': 'https://example.org/requirements', 'title': 'Graduate Engineer', 'company': 'Fixture', 'description': 'Elixir and PostgreSQL required.', 'notes': 'PRIVATE OWNER NOTE', **extra}).json()


def test_native_local_provider_is_structured_bounded_and_source_only(monkeypatch):
    configure(monkeypatch)
    calls = []
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        assert request.url == 'http://127.0.0.1:11434/api/chat'
        assert body['stream'] is False and body['options']['num_ctx'] == 8192
        assert 'tools' not in body and body['format']['additionalProperties'] is False
        return httpx.Response(200,json={'done': True,'done_reason': 'stop','message': {'content':json.dumps(output())}})
    job=SimpleNamespace(title='Engineer',location='London',description='Elixir and PostgreSQL required.',eligibility_requirements='',notes='SECRET NOTE',facts='SECRET FACT',legal='SECRET LEGAL')
    with httpx.Client(transport=model_transport(handle)) as client:
        data, model, chars, truncated=requirements.extract(requirements.public_text(job),client=client)
    assert data.skills[0].value == 'Elixir' and model == 'qwen2.5:3b' and chars > 0 and not truncated
    assert 'SECRET' not in json.dumps(calls)
    assert len(calls) == 1


@pytest.mark.parametrize('base',['https://model.example.org/v1','http://192.168.1.2:11434/v1','http://localhost.evil/v1','http://user:password@127.0.0.1/v1','http://[bad','file:///tmp/model','http://127.0.0.1:bad/v1'])
def test_remote_or_malformed_model_configuration_cannot_send_inputs(monkeypatch,base):
    configure(monkeypatch);monkeypatch.setenv('LLM_BASE_URL',base)
    assert requirements.configuration() is None
    with pytest.raises(NeedsInput,match='local Ollama'):
        requirements.extract('public text')


def test_invalid_ungrounded_and_truncated_model_responses_fail_after_two_retries(monkeypatch):
    configure(monkeypatch)
    calls=[]
    for payload in [
        {'skills':[{'value':'Kubernetes','quote':'Kubernetes required.'}]},
        {'skills':[{'value':'Java','quote':'JavaScript required.'}]},
        {'skills':[{'value':'C','quote':'React required.'}]},
        {**output(),'status':'APPLIED'},
    ]:
        calls.clear()
        def handle(request):
            calls.append(request)
            return httpx.Response(200,json={'done':True,'message':{'content':json.dumps(payload)}})
        with httpx.Client(transport=model_transport(handle)) as client:
            with pytest.raises(NeedsInput,match='three attempts'):
                requirements.extract('Elixir and PostgreSQL required. JavaScript required. React required.',client=client)
        assert len(calls)==3
    calls.clear()
    def cut_off(request):
        calls.append(request)
        return httpx.Response(200,json={'done':True,'done_reason':'length','message':{'content':json.dumps(output())}})
    with httpx.Client(transport=model_transport(cut_off)) as client:
        with pytest.raises(NeedsInput):requirements.extract('Elixir and PostgreSQL required.',client=client)
    assert len(calls)==3


def test_worker_cache_new_technology_matching_and_source_change(client,monkeypatch):
    configure(monkeypatch)
    job=create(client)
    client.post('/api/facts',json={'category':'skill','content':'Built Elixir systems','source':'Reviewed fixture CV','verified':True})
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    before=client.get(f"/api/jobs/{job['id']}/match").json()
    assert next(row['points'] for row in before['breakdown'] if row['criterion']=='skills')==0
    seen=[]
    def extract(text):
        seen.append(text)
        return RequirementsData.model_validate(output()).grounded(text),'qwen2.5:3b',len(text),False
    monkeypatch.setattr(requirements,'extract',extract)
    path=f"/api/jobs/{job['id']}/requirements"
    task=client.post('/api/tasks/requirements',json={'job_id':job['id']}).json()
    assert client.post('/api/tasks/requirements',json={'job_id':job['id']}).json()['id']==task['id']
    assert client.get(path).json()['state']=='not_extracted'
    run_once(client.app.state.engine,client.app.state.settings)
    assert client.get(path).json()['state']=='current' and 'PRIVATE' not in seen[0]
    assert client.get(f"/api/jobs/{job['id']}/match").json()['stale'] is True
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    after=client.get(f"/api/jobs/{job['id']}/match").json()
    assert next(row['points'] for row in after['breakdown'] if row['criterion']=='skills')==20
    assert client.get('/api/jobs').json()[0]['sponsorship']=='UNVERIFIED'
    payload={key:job[key] for key in ['url','title','company','description','notes']}
    client.put(f"/api/jobs/{job['id']}",json={**payload,'description':'Changed vacancy requirements.'})
    assert client.get(path).json()['state']=='stale' and client.get(path).json()['data'] is None


def test_notes_only_and_unconfigured_models_do_not_queue(client,monkeypatch):
    configure(monkeypatch)
    job=create(client,description='')
    assert client.post('/api/tasks/requirements',json={'job_id':job['id']}).status_code==409
    job=create(client,url='https://example.org/other')
    monkeypatch.delenv('LLM_MODEL')
    assert client.post('/api/tasks/requirements',json={'job_id':job['id']}).status_code==409


def test_changed_job_during_model_call_never_saves_stale_result(client,monkeypatch):
    configure(monkeypatch);job=create(client)
    def changed(text):
        with Session(client.app.state.engine) as session:
            row=session.get(Job,job['id']);row.description='Owner changed source';session.commit()
        return RequirementsData.model_validate(output()),'qwen2.5:3b',len(text),False
    monkeypatch.setattr(requirements,'extract',changed)
    client.post('/api/tasks/requirements',json={'job_id':job['id']})
    run_once(client.app.state.engine,client.app.state.settings)
    assert client.get('/api/tasks').json()[0]['status']=='NEEDS_INPUT'
    with Session(client.app.state.engine) as session:assert session.get(JobRequirements,job['id']) is None


def test_input_limit_is_visible_and_tail_quotes_cannot_be_claimed(monkeypatch):
    configure(monkeypatch)
    seen=[]
    def empty(request):
        body=json.loads(request.content);seen.append(body['messages'][-1]['content'])
        return httpx.Response(200,json={'done':True,'message':{'content':'{"skills": [], "education": [], "experience": []}'}})
    text='x' * requirements.MAX_CHARS + ' Tail only Kubernetes required.'
    with httpx.Client(transport=model_transport(empty)) as client:
        data,_,chars,truncated=requirements.extract(text,client=client)
    assert truncated is True and chars==requirements.MAX_CHARS and len(seen[0])==chars
    def invented_tail(_):
        return httpx.Response(200,json={'done':True,'message':{'content':json.dumps({'skills':[{'value':'Kubernetes','quote':'Kubernetes required.'}]})}})
    with httpx.Client(transport=model_transport(invented_tail)) as client:
        with pytest.raises(NeedsInput):requirements.extract(text,client=client)


def test_another_jobs_analysis_does_not_invalidate_unrelated_scores(client,monkeypatch):
    configure(monkeypatch)
    first=create(client)
    other=create(client,url='https://example.org/unrelated')
    client.post('/api/tasks/match',json={'job_id':other['id']});run_once(client.app.state.engine,client.app.state.settings)
    before=client.get(f"/api/jobs/{other['id']}/match").json()
    monkeypatch.setattr(requirements,'extract',lambda text:(RequirementsData.model_validate(output()),'fixture-local',len(text),False))
    client.post('/api/tasks/requirements',json={'job_id':first['id']});run_once(client.app.state.engine,client.app.state.settings)
    assert client.get(f"/api/jobs/{other['id']}/match").json()==before
    assert client.get('/api/matches').json()[other['id']]['state']=='current'


def test_tampered_cache_does_not_supply_scores_or_ui_terms(client,monkeypatch):
    configure(monkeypatch);job=create(client)
    from app.services.sponsorship import snapshot
    with Session(client.app.state.engine) as session:
        row=session.get(Job,job['id'])
        session.add(JobRequirements(job_id=job['id'],payload={'skills':[{'value':'Fabricated','quote':'Not in source'}]},inputs_hash=snapshot(row),model='fixture',source_chars=10,truncated=False))
        session.commit()
    data=client.get(f"/api/jobs/{job['id']}/requirements").json()
    assert data['state']=='stale' and data['data'] is None
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    result=client.get(f"/api/jobs/{job['id']}/match").json()
    assert not any('Fabricated' in row['explanation'] for row in result['breakdown'])


@pytest.mark.parametrize('term',['Visa sponsorship','ILR','Indefinite leave to remain','Permanent residency','Settled status','Pre-settled status','EU Settlement Scheme','Authorised to work','Eligible to work','UK work rights','British citizenship','Skilled Worker','Right‑to‑work','pre–settled status','work_authorisation'])
def test_misclassified_sponsorship_terms_never_penalise_preference_scores(client,monkeypatch,term):
    configure(monkeypatch)
    quote=f'{term} is required.'
    job=create(client,description=f'Python required. {quote}')
    client.post('/api/facts',json={'category':'skill','content':'Python','source':'Fixture reviewed fact','verified':True})
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    before=client.get(f"/api/jobs/{job['id']}/match").json()
    data=RequirementsData.model_validate({'skills':[{'value':'Python','quote':'Python required.'},{'value':term,'quote':quote}]})
    monkeypatch.setattr(requirements,'extract',lambda text:(data.grounded(text),'fixture-local',len(text),False))
    client.post('/api/tasks/requirements',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    after=client.get(f"/api/jobs/{job['id']}/match").json()
    assert after['score']==before['score']
    numeric=lambda result:[(row['criterion'],row['points'],row['maximum'],row['fact_ids']) for row in result['breakdown']]
    assert numeric(after)==numeric(before)
    assert client.get('/api/jobs').json()[0]['sponsorship']=='UNVERIFIED'


@pytest.mark.parametrize('protocol',['native','compatible'])
def test_native_loopback_connection_ignores_shell_proxy_settings(monkeypatch,protocol):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    configure(monkeypatch)
    for name in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'):
        monkeypatch.setenv(name,'http://127.0.0.1:9')
    for name in ('NO_PROXY','no_proxy'):
        monkeypatch.setenv(name,'')
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            received.append((self.path,self.headers.get('Authorization'),body))
            payload={'model_info':{'general.architecture':'fixture'}} if self.path=='/api/show' else {'done':True,'message':{'content':json.dumps(output())}} if protocol=='native' else {'choices':[{'message':{'content':json.dumps({'title':'Engineer','company':'Fixture'})}}]}
            body=json.dumps(payload).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*_):
            pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('LLM_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
    try:
        source='Fixture Engineer. Elixir and PostgreSQL required.'
        if protocol=='native':
            data,*_=requirements.extract(source)
            assert data.skills[0].value=='Elixir'
        else:
            from app.integrations.llm.provider import Ollama
            data=Ollama('fixture',base_url=f'http://127.0.0.1:{server.server_port}/v1').extract('https://example.org/job',source)
            assert data.title=='Engineer' and data.description==source
        assert [row[0] for row in received]==['/api/show','/api/chat' if protocol=='native' else '/v1/chat/completions']
        assert all(row[1] is None for row in received) and set(received[0][2])=={'model'}
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)


@pytest.mark.parametrize('base',['https://model.example.org/v1','http://192.168.1.2:11434/v1','http://localhost.evil/v1','http://user:password@127.0.0.1/v1','http://[bad','file:///tmp/model','http://127.0.0.1:bad/v1','http://127.0.0.1/v1?key=private','http://127.0.0.1/v1#private'])
def test_ollama_page_provider_also_rejects_nonlocal_or_credentialed_urls(monkeypatch,base):
    from app.integrations.llm.provider import configured_provider
    configure(monkeypatch);monkeypatch.setenv('LLM_BASE_URL',base)
    with pytest.raises(NeedsInput,match='loopback'):
        configured_provider()


def test_ollama_compatible_page_client_disables_proxy_and_redirects(monkeypatch):
    from app.integrations.llm.provider import Ollama
    calls=[]
    original=httpx.Client
    def handle(request):
        calls.append(request)
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'title':'Engineer','company':'Fixture','description':'ignored model rewrite'})}}]})
    def factory(**kwargs):
        assert kwargs['trust_env'] is False and kwargs['follow_redirects'] is False
        return original(transport=model_transport(handle),**kwargs)
    monkeypatch.setattr(httpx,'Client',factory)
    data=Ollama('fixture').extract('https://example.org/job','Fixture Engineer vacancy source.')
    assert len(calls)==1 and str(calls[0].url)=='http://127.0.0.1:11434/v1/chat/completions'
    assert data.description=='Fixture Engineer vacancy source.'


@pytest.mark.parametrize('failure,reason',[
    ('connect','server_unreachable'),('timeout','timed_out'),
    (404,'model_or_endpoint_missing'),(400,'structured_request_rejected'),
    (401,'local_access_denied'),(429,'model_busy'),(500,'runtime_failure'),
    (307,'redirect_refused'),
])
def test_local_setup_failures_have_safe_actionable_reasons_without_retry_or_body_leak(monkeypatch,failure,reason):
    configure(monkeypatch)
    calls=[]
    private='SYNTHETIC_PRIVATE_RESPONSE_MARKER'
    def handle(request):
        calls.append(request)
        if failure=='connect':raise httpx.ConnectError(private,request=request)
        if failure=='timeout':raise httpx.ReadTimeout(private,request=request)
        return httpx.Response(failure,text=private,headers={'Location':'http://remote.example/secret'} if failure==307 else {})
    with httpx.Client(transport=model_transport(handle)) as client:
        with pytest.raises(requirements.LocalModelUnavailable) as caught:
            requirements.extract('public fixture job text',client=client)
    assert len(calls)==1 and caught.value.reason==reason
    assert private not in str(caught.value) and 'remote.example' not in str(caught.value)


@pytest.mark.parametrize('payload,source,reason',[
    ({'done':True,'done_reason':'length','message':{'content':'{}'}},'Python required.','output_limit'),
    ({'done':False,'message':{'content':'{}'}},'Python required.','incomplete_response'),
    ({'done':True,'message':{'content':'not JSON'}},'Python required.','schema_invalid'),
    ({'done':True,'message':{'content':'{\"SYNTHETIC_PRIVATE_FIELD\": 1}'}},'Python required.','schema_invalid'),
    ({'done':True,'message':None},'Python required.','response_shape'),
    ({'done':True,'message':{'content':json.dumps({'skills':[{'value':'Python','quote':'Python required.'}]*2})}},'Python required.','duplicate_term'),
    ({'done':True,'message':{'content':'{"skills": ["SYNTHETIC_PRIVATE"]}'}},'Python required.','schema_invalid'),
    ({'done':True,'message':{'content':json.dumps({'skills':[{'value':'Python','quote':'Python required.'}]})}},'No technology stated.','quote_not_in_source'),
    ({'done':True,'message':{'content':json.dumps({'skills':[{'value':'Java','quote':'JavaScript required.'}]})}},'JavaScript required.','term_not_in_quote'),
])
def test_single_attempt_diagnoses_rejection_without_echoing_model_output(monkeypatch,payload,source,reason):
    configure(monkeypatch);calls=[]
    def handle(request):calls.append(request);return httpx.Response(200,json=payload)
    with httpx.Client(transport=model_transport(handle)) as client:
        with pytest.raises(requirements.InvalidRequirementsOutput) as error:
            requirements.extract(source,client=client,attempts=1)
    assert len(calls)==1 and error.value.reason==reason and error.value.attempts==1
    assert 'SYNTHETIC_PRIVATE' not in str(error.value) and 'SYNTHETIC_PRIVATE' not in str(error.value.fields)


@pytest.mark.parametrize('attempts',[0,4,True])
def test_attempt_limit_cannot_exceed_spec_or_make_unconfigured_requests(monkeypatch,attempts):
    monkeypatch.setattr(httpx,'Client',lambda **_:pytest.fail('No client for invalid attempt limit'))
    with pytest.raises(ValueError,match='one to three'):
        requirements.extract('Public fixture',attempts=attempts)


def test_prompt_matches_grounding_contract_and_retry_feedback_excludes_rejected_values(monkeypatch):
    configure(monkeypatch);calls=[]
    marker='SYNTHETIC_REJECTED_VALUE_NOT_TO_ECHO'
    def handle(request):
        body=json.loads(request.content);calls.append(body)
        payload={'skills':[{'value':marker,'quote':'JavaScript required.'}]} if len(calls)==1 else {'skills':[{'value':'Java','quote':'Java required.'}]}
        return httpx.Response(200,json={'done':True,'message':{'content':json.dumps(payload)}})
    with httpx.Client(transport=model_transport(handle)) as client:
        data,*_=requirements.extract('JavaScript required. Java required.',client=client)
    assert data.skills[0].value=='Java' and len(calls)==2
    assert 'Each value must occur verbatim inside its own quote' in calls[0]['messages'][0]['content']
    assert 'term_not_in_quote' in calls[1]['messages'][0]['content']
    assert marker not in json.dumps(calls)
    for body in calls:
        schema=body['format']['$defs']['RequirementTerm']['properties']
        assert 'substring' in schema['value']['description'] and 'containing' in schema['quote']['description']
