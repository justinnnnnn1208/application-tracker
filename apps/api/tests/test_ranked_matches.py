from sqlalchemy.orm import Session
from app.db.models import Job
from app.worker.tasks import run_once


def add(client, name, **extra):
    return client.post('/api/jobs', json={'company': name, 'title': 'Graduate Software Engineer', 'url': f'https://example.org/rank/{name}', 'location': 'London', 'notes': 'Python vacancy summary', **extra}).json()


def test_batch_ranking_skips_closed_missing_and_past_deadline_and_hides_stale_scores(client):
    good = add(client, 'good')
    senior = add(client, 'senior', title='Senior Software Engineer')
    missing = add(client, 'missing', title='Role not provided', notes='Company only')
    applied = add(client, 'applied')
    past = add(client, 'past', deadline='2000-01-01')
    withdrawn = add(client, 'withdrawn')
    client.patch(f"/api/jobs/{withdrawn['id']}/status", json={'status': 'WITHDRAWN', 'expected_status': 'DISCOVERED'})
    with Session(client.app.state.engine) as session:
        session.get(Job, applied['id']).tracker_status = 'Applied'
        session.commit()
    initial = client.get('/api/matches').json()
    assert initial[missing['id']] == {'state': 'needs_details', 'score': None}
    first = client.post('/api/tasks/match', json={})
    assert first.status_code == 202
    assert client.post('/api/tasks/match', json={}).json()['id'] == first.json()['id']
    assert len(client.get('/api/tasks').json()) == 1
    assert run_once(client.app.state.engine, client.app.state.settings)
    result = client.get('/api/tasks').json()[0]['result']
    assert result == {'matched': 2, 'current': 0, 'skipped': 0}
    scores = client.get('/api/matches').json()
    assert scores[good['id']]['score'] > scores[senior['id']]['score']
    assert all(scores[job['id']]['score'] is None for job in [missing, applied, past, withdrawn])
    # A repeat request uses current scores rather than recalculating unchanged facts.
    queued = client.post('/api/tasks/match', json={}).json()
    run_once(client.app.state.engine, client.app.state.settings)
    task = next(t for t in client.get('/api/tasks').json() if t['id'] == queued['id'])
    assert task['result'] == {'matched': 0, 'current': 2, 'skipped': 0}
    # A changed Notes source must never keep an old score visible in the ranked list.
    data = {key: good[key] for key in ['company', 'title', 'url', 'location', 'notes']}
    data['notes'] += ' Updated owner summary'
    client.put(f"/api/jobs/{good['id']}", json=data)
    assert client.get('/api/matches').json()[good['id']] == {'state': 'stale', 'score': None}
    assert client.get('/api/matches').json()[senior['id']]['state'] == 'current'


def test_worker_rechecks_jobs_after_batch_was_queued(client):
    job = add(client, 'changed')
    assert client.post('/api/tasks/match', json={}).status_code == 202
    client.patch(f"/api/jobs/{job['id']}/status", json={'status': 'SKIPPED', 'expected_status': 'DISCOVERED'})
    assert run_once(client.app.state.engine, client.app.state.settings)
    assert client.get('/api/tasks').json()[0]['result'] == {'matched': 0, 'current': 0, 'skipped': 1}
    assert client.get('/api/matches').json()[job['id']]['score'] is None


def test_closed_rows_never_show_old_scores_in_ranked_list(client):
    job = add(client, 'closed-later')
    client.post('/api/tasks/match', json={'job_id': job['id']})
    run_once(client.app.state.engine, client.app.state.settings)
    assert client.get('/api/matches').json()[job['id']]['score'] is not None
    client.patch(f"/api/jobs/{job['id']}/status", json={'status': 'WITHDRAWN', 'expected_status': 'DISCOVERED'})
    assert client.get('/api/matches').json()[job['id']] == {'state': 'inactive', 'score': None}
