"""Repeated clicks reuse pending public imports, never create a hidden schedule."""
import pytest
from sqlalchemy.orm import Session
from app.db.models import Task


@pytest.mark.parametrize('state',['QUEUED','RUNNING'])
def test_pending_import_is_reused_per_source_but_finished_work_can_run_again(client,state):
    source=client.post('/api/discovery',json={'board':'first-board','enabled':True}).json()
    other=client.post('/api/discovery',json={'board':'second-board','enabled':True}).json()
    first=client.post('/api/tasks/discover',json={'source_id':source['id']}).json()
    with Session(client.app.state.engine) as session:
        session.get(Task,first['id']).status=state;session.commit()
    assert client.post('/api/tasks/discover',json={'source_id':source['id']}).json()['id']==first['id']
    assert client.post('/api/tasks/discover',json={'source_id':other['id']}).json()['id']!=first['id']
    assert len(client.get('/api/tasks').json())==2
    with Session(client.app.state.engine) as session:
        session.get(Task,first['id']).status='SUCCEEDED';session.commit()
    assert client.post('/api/tasks/discover',json={'source_id':source['id']}).json()['id']!=first['id']


def test_missing_or_disabled_source_is_not_resurrected_by_pending_task(client):
    source=client.post('/api/discovery',json={'board':'disabled-board','enabled':False}).json()
    with Session(client.app.state.engine) as session:
        session.add(Task(kind='discover',payload={'source_id':source['id']}));session.commit()
    assert client.post('/api/tasks/discover',json={'source_id':source['id']}).status_code==409
    client.delete(f"/api/discovery/{source['id']}")
    assert client.post('/api/tasks/discover',json={'source_id':source['id']}).status_code==404
