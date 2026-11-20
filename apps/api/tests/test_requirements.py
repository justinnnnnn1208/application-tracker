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
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
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
        with httpx.Client(transport=httpx.MockTransport(handle)) as client:
            with pytest.raises(NeedsInput,match='three attempts'):
                requirements.extract('Elixir and PostgreSQL required. JavaScript required. React required.',client=client)
        assert len(calls)==3
    calls.clear()
    def cut_off(request):
        calls.append(request)
        return httpx.Response(200,json={'done':True,'done_reason':'length','message':{'content':json.dumps(output())}})
    with httpx.Client(transport=httpx.MockTransport(cut_off)) as client:
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
    with httpx.Client(transport=httpx.MockTransport(empty)) as client:
        data,_,chars,truncated=requirements.extract(text,client=client)
    assert truncated is True and chars==requirements.MAX_CHARS and len(seen[0])==chars
    def invented_tail(_):
        return httpx.Response(200,json={'done':True,'message':{'content':json.dumps({'skills':[{'value':'Kubernetes','quote':'Kubernetes required.'}]})}})
    with httpx.Client(transport=httpx.MockTransport(invented_tail)) as client:
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


def test_misclassified_sponsorship_terms_never_penalise_preference_scores(client,monkeypatch):
    configure(monkeypatch)
    job=create(client,description='Python required. Visa sponsorship available.')
    client.post('/api/facts',json={'category':'skill','content':'Python','source':'Fixture reviewed fact','verified':True})
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    before=client.get(f"/api/jobs/{job['id']}/match").json()
    data=RequirementsData.model_validate({'skills':[{'value':'Python','quote':'Python required.'},{'value':'Visa sponsorship','quote':'Visa sponsorship available.'}]})
    monkeypatch.setattr(requirements,'extract',lambda text:(data.grounded(text),'fixture-local',len(text),False))
    client.post('/api/tasks/requirements',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    client.post('/api/tasks/match',json={'job_id':job['id']});run_once(client.app.state.engine,client.app.state.settings)
    after=client.get(f"/api/jobs/{job['id']}/match").json()
    assert after['score']==before['score']
    numeric=lambda result:[(row['criterion'],row['points'],row['maximum'],row['fact_ids']) for row in result['breakdown']]
    assert numeric(after)==numeric(before)
    assert client.get('/api/jobs').json()[0]['sponsorship']=='UNVERIFIED'
