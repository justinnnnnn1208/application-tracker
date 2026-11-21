"""Owner-reviewed cross-source links preserve one application; existing jobs never merge."""
import json
from sqlalchemy import select,func
from sqlalchemy.orm import Session

from app.db.models import Application,JobSource,Task
from app.worker.tasks import run_once


def create(client,url='https://careers.example.org/original'):
    return client.post('/api/jobs',json={'url':url,'company':'Fixture Employer','title':'Graduate Engineer','location':'London','description':'Python required.','notes':'Owner note'}).json()


def review(job,url,**extra):
    return {'url':url,'snapshot':job['sponsorship_snapshot'],'confirmed':True,**extra}


def test_reviewed_new_source_reuses_history_during_real_worker_intake(client):
    job=create(client);url='https://another.example.org/listing'
    before=client.get(f"/api/jobs/{job['id']}/events").json()
    path=f"/api/jobs/{job['id']}/sources"
    linked=client.post(path,json=review(job,url))
    assert linked.status_code==201 and linked.json()['method']=='owner_confirmed'
    assert client.post(path,json=review(job,url)).status_code==200
    page={'@type':'JobPosting','title':'Source title','hiringOrganization':{'name':'Source company'},'description':'New source text'}
    client.post('/api/tasks/extract',json={'url':url,'page_html':'<script type="application/ld+json">'+json.dumps(page)+'</script>'})
    run_once(client.app.state.engine,client.app.state.settings)
    rows=client.get('/api/jobs').json()
    assert len(rows)==1 and rows[0]['id']==job['id'] and rows[0]['notes']=='Owner note'
    assert rows[0]['title']=='Graduate Engineer' and rows[0]['description']=='Python required.'
    assert rows[0]['status']=='DISCOVERED' and rows[0]['sponsorship']=='UNVERIFIED'
    assert client.get(f"/api/jobs/{job['id']}/events").json()==before
    with Session(client.app.state.engine) as session:
        assert session.scalar(select(func.count()).select_from(Application))==1
    assert client.get('/api/tasks').json()[0]['result']['created'] is False


def test_confirmation_snapshot_and_source_ownership_are_required(client):
    first=create(client);other=create(client,'https://example.org/other')
    path=f"/api/jobs/{first['id']}/sources"
    assert client.post(path,json=review(first,'https://example.org/a',confirmed=False)).status_code==422
    assert client.post(path,json=review(first,'https://example.org/a',confirmed='true')).status_code==422
    assert client.post(path,json=review(first,'https://example.org/a',snapshot='0'*64)).status_code==409
    assert client.post(path,json=review(first,other['url'])).status_code==409
    assert len(client.get('/api/jobs').json())==2
    assert len(client.get(path).json())==1


def test_distinct_known_requisitions_or_regions_cannot_be_manually_folded(client):
    job=create(client,'https://job-boards.greenhouse.io/fixture/jobs/123')
    path=f"/api/jobs/{job['id']}/sources"
    for url in ['https://job-boards.greenhouse.io/fixture/jobs/456','https://job-boards.eu.greenhouse.io/fixture/jobs/123']:
        assert client.post(path,json=review(job,url)).status_code==422
    assert len(client.get(path).json())==1


def test_known_posting_claim_on_another_job_is_not_stolen(client):
    first=create(client);other=create(client,'https://job-boards.greenhouse.io/fixture/jobs/123')
    path=f"/api/jobs/{first['id']}/sources"
    assert client.post(path,json=review(first,'https://boards.greenhouse.io/fixture/jobs/123')).status_code==409
    assert len(client.get('/api/jobs').json())==2
    assert len(client.get(f"/api/jobs/{other['id']}/events").json())==1


def test_only_reviewed_secondary_links_can_be_removed_and_pending_intake_is_protected(client):
    job=create(client);path=f"/api/jobs/{job['id']}/sources"
    linked=client.post(path,json=review(job,'https://example.org/secondary')).json()
    primary=next(row for row in client.get(path).json() if row['url']==job['url'])
    body={'snapshot':job['sponsorship_snapshot'],'confirmed':True}
    assert client.request('DELETE',path+'/'+primary['id'],json=body).status_code==409
    with Session(client.app.state.engine) as session:
        task=Task(kind='extract_url',payload={'url':linked['url']});session.add(task);session.commit();task_id=task.id
    assert client.request('DELETE',path+'/'+linked['id'],json=body).status_code==409
    with Session(client.app.state.engine) as session:
        session.get(Task,task_id).status='NEEDS_INPUT';session.commit()
    assert client.request('DELETE',path+'/'+linked['id'],json=body).status_code==204
    assert len(client.get(path).json())==1 and len(client.get('/api/jobs').json())==1
    assert len(client.get(f"/api/jobs/{job['id']}/events").json())==1


def test_evidence_source_cannot_be_unlinked_silently(client):
    job=create(client);path=f"/api/jobs/{job['id']}/sources"
    linked=client.post(path,json=review(job,'https://example.org/secondary')).json()
    from app.db.models import JobEligibility
    with Session(client.app.state.engine) as session:
        session.add(JobEligibility(job_id=job['id'],status='CONFIRMED_NO',evidence_quote='Fixture sponsorship quote',source_url=linked['url'],source_hash='0'*64));session.commit()
    body={'snapshot':job['sponsorship_snapshot'],'confirmed':True}
    assert client.request('DELETE',path+'/'+linked['id'],json=body).status_code==409
    assert len(client.get(path).json())==2


def test_secondary_known_id_also_prevents_combining_distinct_requisitions(client):
    job=create(client);path=f"/api/jobs/{job['id']}/sources"
    assert client.post(path,json=review(job,'https://job-boards.greenhouse.io/fixture/jobs/123')).status_code==201
    for url in ['https://job-boards.greenhouse.io/fixture/jobs/456','https://job-boards.eu.greenhouse.io/fixture/jobs/123']:
        assert client.post(path,json=review(job,url)).status_code==422
    assert len(client.get(path).json())==2
    assert len(client.get('/api/jobs').json())==1


def test_pending_known_alias_also_protects_a_reviewed_link_from_removal(client):
    job=create(client);path=f"/api/jobs/{job['id']}/sources"
    linked=client.post(path,json=review(job,'https://job-boards.greenhouse.io/fixture/jobs/123')).json()
    alias='https://boards.greenhouse.io/fixture/jobs/123'
    page={'@type':'JobPosting','title':'Source role','hiringOrganization':{'name':'Fixture Employer'},'description':'Source text'}
    task=client.post('/api/tasks/extract',json={'url':alias,'page_html':'<script type="application/ld+json">'+json.dumps(page)+'</script>'}).json()
    body={'snapshot':job['sponsorship_snapshot'],'confirmed':True}
    assert client.request('DELETE',path+'/'+linked['id'],json=body).status_code==409
    run_once(client.app.state.engine,client.app.state.settings)
    finished=next(row for row in client.get('/api/tasks').json() if row['id']==task['id'])
    assert finished['status']=='SUCCEEDED' and finished['result']=={'job_id':job['id'],'created':False}
    assert len(client.get('/api/jobs').json())==1
    assert len(client.get(f"/api/jobs/{job['id']}/events").json())==1


def test_simultaneous_distinct_source_reviews_cannot_both_claim_one_vacancy(client,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, BrokenBarrierError
    from app.routers import tracker
    job=create(client);path=f"/api/jobs/{job['id']}/sources"
    original=tracker.find_existing;boundary=Barrier(2)
    def paused(session,url):
        # Reproduce overlapping requests after their initial source validation.
        # With serialised review, only one reaches this point; bounded wait exits.
        try:boundary.wait(timeout=1)
        except BrokenBarrierError:pass
        return original(session,url)
    monkeypatch.setattr(tracker,'find_existing',paused)
    def link(id):
        return client.post(path,json=review(job,f'https://job-boards.greenhouse.io/fixture/jobs/{id}')).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(link,[123,456]))
    assert sorted(results)==[201,422]
    assert len(client.get(path).json())==2
    assert len(client.get('/api/jobs').json())==1
