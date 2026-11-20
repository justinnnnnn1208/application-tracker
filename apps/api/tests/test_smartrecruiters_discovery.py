import json

import pytest

from app.integrations.discovery import smartrecruiters as sr
from app.services.errors import NeedsInput
from app.services.identity import ats_identity
from app.worker.tasks import run_once


# Synthetic contract data, not a real vacancy or an evaluation-set addition.
def detail():
    return {'id':'opaque-api-id','name':'Graduate Software Engineer — synthetic fixture',
            'company':{'identifier':'FixtureCompany'},
            'applyUrl':'https://jobs.smartrecruiters.com/FixtureCompany/743999123456789-graduate?utm_source=fixture',
            'location':{'city':'London','country':'gb','remote':False},'releasedDate':'2026-11-01',
            'jobAd':{'sections':{'jobDescription':{'text':'<p>Python required. Start date: September 6th 2027.</p><script>submit()</script>'},
                                 'qualifications':{'text':'<p>Graduate applicants.</p>'},
                                 'companyDescription':{'text':'Company marketing mentions Java.'}}}}


def fake_api(monkeypatch, data=None):
    calls=[]
    def fetch(url):
        calls.append(url)
        if '?' in url:return json.dumps({'content':[{'id':'opaque-api-id','ref':'https://evil.example/private'}],'totalFound':1000})
        return json.dumps(data if data is not None else detail())
    monkeypatch.setattr(sr,'fetch_page',fetch)
    return calls


def test_first_twenty_detailed_postings_use_literal_text_not_company_background(monkeypatch):
    calls=fake_api(monkeypatch)
    jobs,skipped=sr.read_board('FixtureCompany','Fixture Employer')
    assert calls==['https://api.smartrecruiters.com/v1/companies/FixtureCompany/postings?limit=20&offset=0','https://api.smartrecruiters.com/v1/companies/FixtureCompany/postings/opaque-api-id']
    assert len(jobs)==1 and skipped==0
    job=jobs[0]
    assert job.company=='Fixture Employer' and job.location=='London, gb'
    assert job.description=='Python required. Start date: September 6th 2027.\n\nGraduate applicants.'
    assert job.start_date.isoformat()=='2027-09-06' and job.deadline is None
    assert 'utm_source' not in job.url


def test_repeat_intake_uses_public_numeric_id_not_opaque_api_id(client,monkeypatch):
    fake_api(monkeypatch)
    old=client.post('/api/jobs',json={'url':'https://jobs.smartrecruiters.com/FixtureCompany/743999123456789-old-title','title':'Owner title','company':'Owner company','notes':'Owner note'}).json()
    source=client.post('/api/discovery',json={'provider':'smartrecruiters','board':'FixtureCompany','employer':'Fixture Employer','enabled':True})
    assert source.status_code==201
    for _ in range(2):
        assert client.post('/api/tasks/discover',json={'source_id':source.json()['id']}).status_code==202
        run_once(client.app.state.engine,client.app.state.settings)
    rows=client.get('/api/jobs').json()
    assert len(rows)==1 and rows[0]['id']==old['id'] and rows[0]['title']=='Owner title'
    assert rows[0]['company']=='Owner company' and rows[0]['notes']=='Owner note'
    assert rows[0]['sponsorship']=='UNVERIFIED' and rows[0]['status']=='DISCOVERED'
    assert len(client.get(f"/api/jobs/{old['id']}/sources").json())==2
    assert all(task['result']['duplicates']==1 for task in client.get('/api/tasks').json())


@pytest.mark.parametrize('extra',[{'employer':''},{'region':'eu'},{'board':'https://jobs.smartrecruiters.com/FixtureCompany'}])
def test_source_requires_explicit_company_scope(client,extra):
    assert client.post('/api/discovery',json={'provider':'smartrecruiters','board':'FixtureCompany','employer':'Fixture Employer',**extra}).status_code==422


@pytest.mark.parametrize('extra',[{'id':'wrong-id'},{'company':{'identifier':'OtherCompany'}},{'applyUrl':'https://evil.example/FixtureCompany/743999123456789-job'},{'applyUrl':'https://jobs.smartrecruiters.com/OtherCompany/743999123456789-job'},{'applyUrl':'https://jobs.smartrecruiters.com/FixtureCompany/743999123456789-job/application'},{'applyUrl':'http://jobs.smartrecruiters.com/FixtureCompany/743999123456789-job'},{'jobAd':{'sections':{'qualifications':{'text':'Not a full job description'}}}}])
def test_mismatched_or_incomplete_details_are_not_imported(monkeypatch,extra):
    calls=fake_api(monkeypatch,{**detail(),**extra})
    assert sr.read_board('FixtureCompany','Fixture Employer')==([],1)
    assert len(calls)==2


@pytest.mark.parametrize('payload',[{},[],{'content':'wrong'},{'content':[{}]*21}])
def test_invalid_oversized_page_fails_before_details(monkeypatch,payload):
    monkeypatch.setattr(sr,'fetch_page',lambda _:json.dumps(payload))
    with pytest.raises(NeedsInput):sr.read_board('FixtureCompany','Fixture Employer')


def test_later_detail_denial_does_not_save_partial_board(client,monkeypatch):
    def fetch(url):
        if '?' in url:return json.dumps({'content':[{'id':'opaque-api-id'},{'id':'second-id'}]})
        if url.endswith('/opaque-api-id'):return json.dumps(detail())
        raise NeedsInput('Public API access denied')
    monkeypatch.setattr(sr,'fetch_page',fetch)
    source=client.post('/api/discovery',json={'provider':'smartrecruiters','board':'FixtureCompany','employer':'Fixture Employer','enabled':True}).json()
    client.post('/api/tasks/discover',json={'source_id':source['id']})
    run_once(client.app.state.engine,client.app.state.settings)
    assert client.get('/api/jobs').json()==[]
    assert client.get('/api/tasks').json()[0]['status']=='NEEDS_INPUT'


def test_invalid_ids_never_reach_arbitrary_detail_paths_and_repeats_skip(monkeypatch):
    calls=[]
    def fetch(url):
        calls.append(url)
        return json.dumps({'content':[{'id':'../../private'},{'id':'opaque-api-id'},{'id':'opaque-api-id'},None]}) if '?' in url else json.dumps(detail())
    monkeypatch.setattr(sr,'fetch_page',fetch)
    jobs,skipped=sr.read_board('FixtureCompany','Fixture Employer')
    assert len(jobs)==1 and skipped==3 and len(calls)==2
    assert ats_identity(jobs[0].url)=='smartrecruiters:FixtureCompany:743999123456789'
    assert ats_identity(jobs[0].url.replace('FixtureCompany','OtherCompany'))!='smartrecruiters:FixtureCompany:743999123456789'


def test_migration_indexes_old_alias_without_changing_history(tmp_path,monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text
    from app.db.session import make_engine
    url=f'sqlite:///{tmp_path}/old-sr.db';monkeypatch.setenv('DATABASE_URL',url)
    config=Config('alembic.ini');command.upgrade(config,'da70f481b276')
    engine=make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO jobs (id,url,company,title,location,description,notes,sponsorship,created_at) VALUES ('owner','https://jobs.smartrecruiters.com/FixtureCompany/743999123456789-old','Owner company','Owner title','','','Owner note','UNVERIFIED','2026-11-20')"))
        connection.execute(text("INSERT INTO job_sources (id,job_id,url,identity_key,method,created_at) VALUES ('source','owner','https://jobs.smartrecruiters.com/FixtureCompany/743999123456789-old','','primary','2026-11-20')"))
    command.upgrade(config,'head')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT identity_key FROM job_sources WHERE id='source'")).scalar()=='smartrecruiters:FixtureCompany:743999123456789'
        assert connection.execute(text("SELECT notes FROM jobs WHERE id='owner'")).scalar()=='Owner note'
    command.downgrade(config,'da70f481b276')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT identity_key FROM job_sources WHERE id='source'")).scalar()==''
    command.upgrade(config,'head');engine.dispose()
