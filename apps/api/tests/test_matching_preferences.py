from app.services.matching import WEIGHTS
from app.worker.tasks import run_once


def test_effective_defaults_and_manual_weight_changes_invalidate_scores_and_ratings(client, tmp_path):
    defaults = client.get('/api/settings').json()
    assert defaults['weights'] == WEIGHTS and sum(defaults['weights'].values()) == 100
    assert 'sponsorship' not in defaults['weights']
    backup = str(tmp_path / 'owner-backups')
    assert client.put('/api/settings', json={**defaults, 'backup_dir': backup}).status_code == 200
    job = client.post('/api/jobs', json={'company': 'Fixture', 'title': 'Graduate Software Engineer', 'url': 'https://example.org/preferences', 'description': 'Python vacancy', 'location': 'London'}).json()
    client.post('/api/tasks/match', json={'job_id': job['id']})
    run_once(client.app.state.engine, client.app.state.settings)
    assert client.post(f"/api/jobs/{job['id']}/feedback", json={'value': 'good'}).status_code == 200
    assert client.get('/api/matches/feedback').json() == {'good': 1, 'bad': 0, 'stale': 0}
    settings = client.get('/api/settings').json()
    weights = {**settings['weights'], 'role': 30, 'graduate': 15}
    assert client.put('/api/settings', json={**settings, 'weights': weights, 'target_roles': ['data engineer']}).status_code == 200
    assert client.get('/api/settings').json()['backup_dir'] == backup
    assert client.get('/api/matches').json()[job['id']]['state'] == 'stale'
    assert client.get('/api/matches/feedback').json() == {'good': 0, 'bad': 0, 'stale': 1}
    client.post('/api/tasks/match', json={'job_id': job['id']})
    run_once(client.app.state.engine, client.app.state.settings)
    result = client.get(f"/api/jobs/{job['id']}/match").json()
    assert result['feedback'] is None and result['stale'] is False
    assert next(row for row in result['breakdown'] if row['criterion'] == 'role')['maximum'] == 30
    assert next(row for row in result['breakdown'] if row['criterion'] == 'role')['points'] == 0


def test_invalid_weights_and_sponsorship_penalties_are_rejected(client):
    settings = client.get('/api/settings').json()
    for invalid in [{**WEIGHTS, 'role': 0}, {**WEIGHTS, 'sponsorship': 5}, {'role': 100}, {**WEIGHTS, 'role': -1, 'graduate': 46}]:
        assert client.put('/api/settings', json={**settings, 'weights': invalid}).status_code == 422
    assert client.get('/api/settings').json()['weights'] == WEIGHTS
