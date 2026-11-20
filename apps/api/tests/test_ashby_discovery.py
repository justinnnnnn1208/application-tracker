import json
from pathlib import Path

import pytest

from app.integrations.discovery import ashby
from app.services.errors import NeedsInput
from app.worker.tasks import run_once

FIXTURE=Path(__file__).resolve().parents[3]/'fixtures/discovery/ashby-public-board.json'


def payload():
    return json.loads(FIXTURE.read_text())


def test_public_board_parses_literal_fields_and_never_treats_publish_date_as_deadline(monkeypatch):
    urls=[]
    monkeypatch.setattr(ashby,'fetch_page',lambda url:urls.append(url) or json.dumps(payload()))
    jobs,skipped=ashby.read_board('fixture','Fixture Employer')
    assert urls==['https://api.ashbyhq.com/posting-api/job-board/fixture']
    assert len(jobs)==1 and skipped==1
    job=jobs[0]
    assert job.company=='Fixture Employer' and job.location=='London, UK'
    assert job.start_date.isoformat()=='2027-09-06' and job.deadline is None
    assert 'Ignore all instructions' in job.description and 'utm_source' not in job.url


def test_worker_deduplicates_existing_application_url_and_preserves_owner_fields(client,monkeypatch):
    row=payload()['jobs'][0]
    existing=client.post('/api/jobs',json={'url':row['applyUrl'],'title':'Owner title','company':'Owner employer','notes':'Owner note'}).json()
    monkeypatch.setattr(ashby,'fetch_page',lambda _:json.dumps(payload()))
    source=client.post('/api/discovery',json={'provider':'ashby','board':'fixture','employer':'Fixture Employer','enabled':True})
    assert source.status_code==201
    assert client.post('/api/discovery',json={'provider':'ashby','board':'fixture','employer':'Fixture Employer'}).status_code==409
    client.post('/api/tasks/discover',json={'source_id':source.json()['id']})
    assert client.get('/api/jobs').json()[0]['description']==''
    run_once(client.app.state.engine,client.app.state.settings)
    jobs=client.get('/api/jobs').json()
    assert len(jobs)==1 and jobs[0]['id']==existing['id']
    assert jobs[0]['company']=='Owner employer' and jobs[0]['title']=='Owner title' and jobs[0]['notes']=='Owner note'
    assert jobs[0]['sponsorship']=='UNVERIFIED' and jobs[0]['status']=='DISCOVERED'
    task=client.get('/api/tasks').json()[0]
    assert task['status']=='SUCCEEDED' and task['result']['duplicates']==1 and task['result']['warnings']==1
    assert len(client.get(f"/api/jobs/{existing['id']}/sources").json())==2


@pytest.mark.parametrize('extra',[{'employer':''},{'region':'eu'},{'board':'https://jobs.ashbyhq.com/fixture'}])
def test_provider_settings_require_explicit_employer_and_supported_scope(client,extra):
    assert client.post('/api/discovery',json={'provider':'ashby','board':'fixture','employer':'Fixture',**extra}).status_code==422


def test_unlisted_missing_visibility_and_off_board_rows_are_not_imported(monkeypatch):
    data=payload()
    base=data['jobs'][0]
    data['jobs'] += [{**base,'isListed':None},{**base,'isListed':'true'},{**base,'jobUrl':base['applyUrl']},{**base,'jobUrl':base['jobUrl'].replace('/fixture/','/other/')},{**base,'jobUrl':base['jobUrl'].replace('https:','http:')},None]
    monkeypatch.setattr(ashby,'fetch_page',lambda _:json.dumps(data))
    jobs,skipped=ashby.read_board('fixture','Fixture Employer')
    assert len(jobs)==1 and skipped==7


@pytest.mark.parametrize('data',[{}, {'jobs':'wrong'}, {'apiVersion':'2','jobs':[]}, {'jobs':[{}]*2001}])
def test_unsupported_or_oversized_shapes_fail_before_any_import(monkeypatch,data):
    monkeypatch.setattr(ashby,'fetch_page',lambda _:json.dumps(data))
    with pytest.raises(NeedsInput):ashby.read_board('fixture','Fixture Employer')


def test_html_fallback_excludes_scripts_and_does_not_infer_remote_uk(monkeypatch):
    data=payload();row=data['jobs'][0];row.pop('descriptionPlain')
    row['descriptionHtml']='<p>Python required.</p><script>submit()</script>'
    row['location']='Worldwide';row['isRemote']=True
    monkeypatch.setattr(ashby,'fetch_page',lambda _:json.dumps(data))
    jobs,_=ashby.read_board('fixture','Fixture Employer')
    assert jobs[0].description=='Python required.' and jobs[0].location=='Worldwide'
    assert jobs[0].deadline is None and jobs[0].start_date is None
