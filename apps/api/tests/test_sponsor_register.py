import io
import json
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.db.models import Job
from app.services import sponsor_register as registry
from app.services.errors import NeedsInput
from app.worker.tasks import run_once

CSV = 'Organisation Name,Town/City,County,Type & Rating,Route\nFixture Employer Ltd,Leeds,,Worker A,Skilled Worker\nFixture Employer Ltd,London,,Worker A,Global Business Mobility\nAnother Fixture,Leeds,,Worker A,Skilled Worker\n'
META = {'source_url':'https://assets.publishing.service.gov.uk/media/fixture/register.csv', 'as_of':'2026-11-19', 'organisation_header':'Organisation Name', 'route_header':'Route', 'town_header':'Town/City', 'confirmed':True}


def upload(client,content=CSV,metadata=None):
    return client.post('/api/sponsors/register',content=content,headers={'X-Register-Metadata':json.dumps(metadata or META),'Content-Type':'text/csv'})


def job(client,company='Fixture Employer Ltd',**extra):
    return client.post('/api/jobs',json={'url':'https://example.org/registry','company':company,'title':'Graduate Engineer','description':'Python role',**extra}).json()


def test_exact_name_csv_import_is_separate_dated_and_never_confirms_sponsorship(client):
    one=job(client)
    assert client.get('/api/sponsors/register').json() is None
    assert one['licensed_sponsor'] is None
    client.post('/api/tasks/match',json={'job_id':one['id']});run_once(client.app.state.engine,client.app.state.settings)
    before=client.get(f"/api/jobs/{one['id']}/match").json()
    queued=upload(client)
    assert queued.status_code==202
    assert client.get('/api/sponsors/register').json() is None
    assert run_once(client.app.state.engine,client.app.state.settings)
    meta=client.get('/api/sponsors/register').json()
    assert meta['as_of']=='2026-11-19' and meta['rows_read']==3 and meta['organisations']==2
    assert meta['verification']=='owner_confirmed_upload' and len(meta['sha256'])==64
    status=client.get(f"/api/jobs/{one['id']}/sponsor-register").json()
    assert status['match'] is True and status['organisation']['routes']==['Global Business Mobility','Skilled Worker']
    assert status['organisation']['towns']==['Leeds','London']
    result=client.get('/api/jobs').json()[0]
    assert result['licensed_sponsor'] is True and result['sponsorship']=='UNVERIFIED' and result['status']=='DISCOVERED'
    assert client.get(f"/api/jobs/{one['id']}/match").json()==before
    with Session(client.app.state.engine) as session:
        assert session.get(Job,one['id']).licensed_sponsor is None
    folder=client.app.state.settings.storage_dir/'registers'
    assert len(list(folder.glob('*.csv')))==len(list(folder.glob('*.json')))==1


@pytest.mark.parametrize('company,expected',[('  FIXTURE   EMPLOYER LTD ',True),('Fixture Employer',False),('Fixture Employer Limited',False),('Fixture Employer Ltd UK',False),('Other Fixture Employer Ltd',False)])
def test_case_whitespace_match_without_fuzzy_brand_or_suffix_guesses(client,company,expected):
    upload(client);run_once(client.app.state.engine,client.app.state.settings)
    one=job(client,company)
    assert one['licensed_sponsor'] is expected


@pytest.mark.parametrize('content',[
    '', 'Wrong,Headers\nFixture,Skilled Worker\n',
    'Organisation Name,Route,Route\nFixture,Skilled Worker,X\n',
    'Organisation Name,Route,Town/City\nFixture,,Leeds\n',
    'Organisation Name,Route,Town/City\nFixture,Skilled Worker,Leeds,EXTRA\n',
    'Organisation Name,Route,Town/City\n"Unclosed,Skilled Worker,Leeds\n',
])
def test_invalid_csv_never_replaces_previous_snapshot(client,content):
    upload(client);run_once(client.app.state.engine,client.app.state.settings)
    before=client.get('/api/sponsors/register').json()
    response=upload(client,content)
    if response.status_code==202:
        run_once(client.app.state.engine,client.app.state.settings)
        task=next(row for row in client.get('/api/tasks').json() if row['id']==response.json()['id'])
        assert task['status']=='NEEDS_INPUT'
    else:
        assert response.status_code==422
    assert client.get('/api/sponsors/register').json()==before


@pytest.mark.parametrize('extra',[{'confirmed':False},{'as_of':'2100-01-01'},{'source_url':'https://evil.example/register.csv'},{'source_url':'http://assets.publishing.service.gov.uk/media/a.csv'},{'source_url':'https://assets.publishing.service.gov.uk/media/a.csv?token=secret'},{'route_header':'Organisation Name'}])
def test_unconfirmed_or_invalid_provenance_rejected_without_upload(client,extra):
    assert upload(client,metadata={**META,**extra}).status_code==422
    assert client.get('/api/sponsors/register').json() is None
    assert not list((client.app.state.settings.storage_dir/'registers').glob('*'))


def test_csv_bom_unicode_quotes_and_row_limit():
    metadata=registry.RegisterImport.model_validate(META)
    content='\ufeffOrganisation Name,Route,Town/City\n"Fixture, Café Ltd",Skilled Worker,Leeds\n'
    stream=io.TextIOWrapper(io.BytesIO(content.encode('utf-8')),encoding='utf-8-sig',newline='')
    rows,count=registry.parse(stream,metadata)
    assert count==1 and rows[0]['name']=='Fixture, Café Ltd'


def test_oversize_stream_cleans_partial_upload(client,monkeypatch):
    monkeypatch.setattr('app.routers.sponsors.MAX_BYTES',10)
    assert upload(client).status_code==413
    assert not list((client.app.state.settings.storage_dir/'registers').glob('*'))
    assert client.get('/api/tasks').json()==[]


def test_bounded_row_count_fails_before_any_partial_replacement(client,monkeypatch):
    monkeypatch.setattr(registry,'MAX_ROWS',1)
    response=upload(client)
    run_once(client.app.state.engine,client.app.state.settings)
    task=next(row for row in client.get('/api/tasks').json() if row['id']==response.json()['id'])
    assert task['status']=='NEEDS_INPUT' and client.get('/api/sponsors/register').json() is None


def test_legacy_boolean_without_register_provenance_is_not_reported_as_a_checked_match(client):
    one=job(client)
    with Session(client.app.state.engine) as session:
        row=session.get(Job,one['id']);row.licensed_sponsor=True;session.commit()
    assert client.get('/api/jobs').json()[0]['licensed_sponsor'] is None
    assert client.get(f"/api/jobs/{one['id']}/sponsor-register").json()['match'] is None


def test_unicode_composition_matches_but_accents_and_punctuation_are_not_guessed():
    assert registry.name_key('Café Ltd')==registry.name_key('  CAFE\u0301   LTD ')
    assert registry.name_key('Cafe Ltd')!=registry.name_key('Café Ltd')
    assert registry.name_key('A&B Ltd')!=registry.name_key('A and B Ltd')
