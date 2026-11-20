import base64
import json
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.integrations.discovery import reed
from app.services.errors import NeedsInput
from app.worker.tasks import run_once


def detail(id=12345):
    return {'jobId':id,'jobTitle':'Graduate Software Engineer — synthetic fixture','employerName':'Fixture Employer','locationName':'London','jobUrl':f'https://www.reed.co.uk/jobs/graduate-engineer/{id}?utm_source=test','jobDescription':'<p>Python required. Start date: September 6th 2027.</p>','expirationDate':'30/11/2026','date':'01/11/2026'}


def fake_api(monkeypatch,**extra):
    calls=[]
    def fetch(url,**kwargs):
        calls.append((url,kwargs))
        if '/search?' in url:return json.dumps({'results':[{'jobId':12345,'jobDescription':'Search excerpt must not be used'}],'totalResults':150})
        return json.dumps({**detail(),**extra})
    monkeypatch.setenv('REED_API_KEY','fixture-private-api-key')
    monkeypatch.setattr(reed,'fetch_page',fetch)
    return calls


def test_bounded_search_uses_detailed_fields_without_expiry_or_publish_date_guess(monkeypatch):
    calls=fake_api(monkeypatch)
    jobs,skipped=reed.read_search('graduate software')
    assert len(jobs)==1 and skipped==0
    query=parse_qs(urlsplit(calls[0][0]).query)
    assert query=={'keywords':['graduate software'],'resultsToTake':['20'],'resultsToSkip':['0']}
    assert calls[1][0]=='https://www.reed.co.uk/api/1.0/jobs/12345'
    assert all('fixture-private-api-key' not in url for url,_ in calls)
    assert all(data['auth']==('fixture-private-api-key','') for _,data in calls)
    assert jobs[0].description=='Python required. Start date: September 6th 2027.'
    assert jobs[0].start_date.isoformat()=='2027-09-06' and jobs[0].deadline is None


def test_source_worker_dedupes_slug_variants_and_never_returns_credentials(client,monkeypatch):
    calls=fake_api(monkeypatch)
    old=client.post('/api/jobs',json={'url':'https://reed.co.uk/jobs/old-title/12345','company':'Owner company','title':'Owner title','notes':'Keep owner note'}).json()
    source=client.post('/api/discovery',json={'provider':'reed','search_query':'graduate software','enabled':True})
    assert source.status_code==201 and source.json()['credentials_configured'] is True
    assert 'fixture-private-api-key' not in source.text and 'fixture-private-api-key' not in client.get('/api/discovery').text
    assert client.post('/api/discovery',json={'provider':'reed','search_query':'graduate software'}).status_code==409
    task=client.post('/api/tasks/discover',json={'source_id':source.json()['id']})
    assert task.status_code==202
    run_once(client.app.state.engine,client.app.state.settings)
    rows=client.get('/api/jobs').json()
    assert len(rows)==1 and rows[0]['id']==old['id'] and rows[0]['company']=='Owner company'
    assert rows[0]['notes']=='Keep owner note' and rows[0]['status']=='DISCOVERED' and rows[0]['sponsorship']=='UNVERIFIED'
    assert len(client.get(f"/api/jobs/{old['id']}/sources").json())==2
    assert 'fixture-private-api-key' not in client.get('/api/tasks').text


def test_missing_key_does_not_make_requests_or_expose_key_entry_in_api(client,monkeypatch):
    monkeypatch.delenv('REED_API_KEY',raising=False)
    source=client.post('/api/discovery',json={'provider':'reed','search_query':'graduate','enabled':True}).json()
    assert source['credentials_configured'] is False
    assert client.post('/api/tasks/discover',json={'source_id':source['id']}).status_code==409
    assert client.post('/api/discovery',json={'provider':'reed','search_query':'graduate','api_key':'do-not-send'}).status_code==422
    with pytest.raises(NeedsInput,match='privately'):reed.read_search('graduate')


@pytest.mark.parametrize('extra',[{'search_query':''},{'region':'eu'},{'employer':'Invented company'},{'search_query':'x'*301}])
def test_search_configuration_validation(client,extra):
    assert client.post('/api/discovery',json={'provider':'reed','search_query':'graduate',**extra}).status_code==422


@pytest.mark.parametrize('extra',[{'jobId':999},{'jobUrl':'https://evil.example/jobs/a/12345'},{'jobUrl':'http://www.reed.co.uk/jobs/a/12345'},{'jobDescription':''}])
def test_bad_details_are_skipped_without_following_external_links(monkeypatch,extra):
    calls=fake_api(monkeypatch,**extra)
    jobs,skipped=reed.read_search('graduate')
    assert not jobs and skipped==1 and len(calls)==2


def test_later_detail_denial_does_not_save_partial_search(client,monkeypatch):
    monkeypatch.setenv('REED_API_KEY','fixture-key')
    def fetch(url,**kwargs):
        if '/search?' in url:return json.dumps({'results':[{'jobId':12345},{'jobId':12346}]})
        if url.endswith('/12345'):return json.dumps(detail())
        raise NeedsInput('API denied access')
    monkeypatch.setattr(reed,'fetch_page',fetch)
    source=client.post('/api/discovery',json={'provider':'reed','search_query':'graduate','enabled':True}).json()
    client.post('/api/tasks/discover',json={'source_id':source['id']})
    run_once(client.app.state.engine,client.app.state.settings)
    assert client.get('/api/jobs').json()==[] and client.get('/api/tasks').json()[0]['status']=='NEEDS_INPUT'


def test_api_credentials_are_not_sent_to_robots_and_keep_existing_fetch_guards(monkeypatch):
    from app.services import fetching
    monkeypatch.setenv('URL_FETCH_ALLOWED_HOSTS','www.reed.co.uk')
    monkeypatch.setattr(fetching.socket,'getaddrinfo',lambda *args:[(2,1,6,'',('8.8.8.8',443))])
    monkeypatch.setattr(fetching,'sleep',lambda _:None)
    calls=[]
    original=httpx.Client
    def handle(request):
        calls.append((str(request.url),request.headers.get('authorization')))
        if request.url.path=='/robots.txt':return httpx.Response(200,text='User-agent: *\nAllow: /api/1.0/\n')
        return httpx.Response(200,json={'results':[]})
    monkeypatch.setattr(fetching.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    fetching.fetch_page('https://www.reed.co.uk/api/1.0/search?keywords=graduate',auth=('fixture-key',''))
    assert calls[0][1] is None and calls[1][1]=='Basic '+base64.b64encode(b'fixture-key:').decode()
    assert all('fixture-key' not in url for url,_ in calls)


@pytest.mark.parametrize('url',['https://evil.example/api/1.0/search','http://www.reed.co.uk/api/1.0/search','https://www.reed.co.uk/api/1.0/jobs/../private','https://www.reed.co.uk/jobs/advert/12345'])
def test_credential_scope_denies_other_destinations_before_network(monkeypatch,url):
    from app.services import fetching
    def should_not_resolve(*_):raise AssertionError('Scope must be checked before network')
    monkeypatch.setattr(fetching.socket,'getaddrinfo',should_not_resolve)
    with pytest.raises(NeedsInput,match='Credential scope'):
        fetching.fetch_page(url,auth=('fixture-key',''))


def test_migration_preserves_legacy_sources_and_indexes_existing_reed_urls(tmp_path,monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text
    from app.db.session import make_engine
    url=f'sqlite:///{tmp_path}/old-reed.db';monkeypatch.setenv('DATABASE_URL',url)
    config=Config('alembic.ini');command.upgrade(config,'c96ef370a165')
    engine=make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO discovery_sources (id,provider,board,enabled,employer,region) VALUES ('owner','greenhouse','owner-board',1,'Owner employer','global')"))
        connection.execute(text("INSERT INTO jobs (id,url,company,title,location,description,notes,sponsorship,created_at) VALUES ('owner','https://www.reed.co.uk/jobs/owner-title/12345','Owner company','Owner title','','','Owner note','UNVERIFIED','2026-11-19')"))
        connection.execute(text("INSERT INTO job_sources (id,job_id,url,identity_key,method,created_at) VALUES ('source','owner','https://www.reed.co.uk/jobs/owner-title/12345','','primary','2026-11-19')"))
    command.upgrade(config,'head')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT search_query FROM discovery_sources WHERE id='owner'")).scalar()==''
        assert connection.execute(text("SELECT identity_key FROM job_sources WHERE id='source'")).scalar()=='reed:jobs:12345'
        assert connection.execute(text("SELECT notes FROM jobs WHERE id='owner'")).scalar()=='Owner note'
    command.downgrade(config,'c96ef370a165')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT identity_key FROM job_sources WHERE id='source'")).scalar()==''
        assert connection.execute(text("SELECT employer FROM discovery_sources WHERE id='owner'")).scalar()=='Owner employer'
    command.upgrade(config,'head');engine.dispose()
