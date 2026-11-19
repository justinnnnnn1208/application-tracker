import pytest
from sqlalchemy.orm import Session

from app.db.models import Job, JobEligibility
from app.worker.tasks import run_once


def vacancy(client, **extra):
    return client.post('/api/jobs', json={'url': 'https://example.org/review', 'company': 'Fixture', 'title': 'Graduate Engineer', 'description': 'This role is in London. We offer visa sponsorship for this role.', **extra}).json()


def body(client, job, **extra):
    return {'status': 'CONFIRMED_YES', 'evidence_quote': 'We offer visa sponsorship for this role.', 'source_url': job['url'], 'snapshot': client.get(f"/api/jobs/{job['id']}/eligibility").json()['snapshot'], 'confirmed': True, **extra}


def test_review_is_explicit_traced_and_score_independent(client):
    job = vacancy(client)
    path = f"/api/jobs/{job['id']}/eligibility"
    assert job['sponsorship'] == 'UNVERIFIED'
    client.post('/api/tasks/match', json={'job_id': job['id']})
    run_once(client.app.state.engine, client.app.state.settings)
    before = client.get(f"/api/jobs/{job['id']}/match").json()
    result = client.put(path, json=body(client, job))
    assert result.status_code == 200
    assert result.json()['status'] == 'CONFIRMED_YES' and result.json()['reviewed_at']
    assert result.json()['evidence_quote'] == 'We offer visa sponsorship for this role.'
    assert client.get(f"/api/jobs/{job['id']}").json()['sponsorship'] == 'CONFIRMED_YES'
    assert client.get('/api/jobs').json()[0]['sponsorship'] == 'CONFIRMED_YES'
    assert client.get(f"/api/jobs/{job['id']}/match").json() == before
    with Session(client.app.state.engine) as session:
        # Intake field stays fail-closed; confirmation exists only in reviewed evidence.
        assert session.get(Job, job['id']).sponsorship == 'UNVERIFIED'
    assert client.delete(path).status_code == 204
    assert client.get(path).json()['status'] == 'UNVERIFIED'
    assert client.get(path).json()['evidence_quote'] is None


def test_changed_source_content_invalidates_review_and_stale_browser_is_rejected(client):
    job = vacancy(client)
    path = f"/api/jobs/{job['id']}/eligibility"
    reviewed = body(client, job)
    assert client.put(path, json=reviewed).status_code == 200
    payload = {key: job[key] for key in ('url', 'company', 'title', 'location', 'description', 'notes', 'deadline', 'start_date', 'eligibility_requirements')}
    assert client.put(f"/api/jobs/{job['id']}", json={**payload, 'description': 'This role cannot offer sponsorship.'}).status_code == 200
    assert client.get(path).json()['stale'] is True
    assert client.get('/api/jobs').json()[0]['sponsorship'] == 'UNVERIFIED'
    assert client.put(path, json=reviewed).status_code == 409
    no = body(client, job, status='CONFIRMED_NO', evidence_quote='This role cannot offer sponsorship.')
    assert client.put(path, json=no).json()['status'] == 'CONFIRMED_NO'


def test_unknown_evidence_and_notes_cannot_confirm(client):
    job = vacancy(client, notes='This employer offers sponsorship.', description='A role in London.')
    path = f"/api/jobs/{job['id']}/eligibility"
    for extra in ({'confirmed': False}, {'confirmed': None}, {'evidence_quote': 'This employer offers sponsorship.'}, {'source_url': 'https://example.org/company-policy'}, {'evidence_quote': 'A role in London.'}, {'status': 'MAYBE'}):
        assert client.put(path, json=body(client, job, **extra)).status_code == 422
    assert client.get(path).json()['status'] == 'UNVERIFIED'
    assert client.get('/api/jobs').json()[0]['sponsorship'] == 'UNVERIFIED'


def test_legacy_unbound_confirmation_is_not_trusted(client):
    job = vacancy(client)
    with Session(client.app.state.engine) as session:
        session.add(JobEligibility(job_id=job['id'], status='CONFIRMED_YES', evidence_quote='Historic claim', source_url=job['url']))
        session.commit()
    assert client.get('/api/jobs').json()[0]['sponsorship'] == 'UNVERIFIED'
    assert client.get(f"/api/jobs/{job['id']}/eligibility").json()['stale'] is True


def test_known_alias_evidence_and_notes_edit_preserve_review(client):
    job = vacancy(client, url='https://job-boards.greenhouse.io/fixture/jobs/123')
    alias = 'https://boards.greenhouse.io/fixture/jobs/123'
    assert client.post('/api/jobs', json={'url': alias, 'company': 'Fixture', 'title': 'Graduate Engineer'}).json()['id'] == job['id']
    path = f"/api/jobs/{job['id']}/eligibility"
    assert client.put(path, json=body(client, job, source_url=alias)).status_code == 200
    payload = {key: job[key] for key in ('url', 'company', 'title', 'location', 'description', 'notes', 'deadline', 'start_date', 'eligibility_requirements')}
    assert client.put(f"/api/jobs/{job['id']}", json={**payload, 'notes': 'Owner personal reminder'}).json()['sponsorship'] == 'CONFIRMED_YES'
    assert client.get(path).json()['stale'] is False


def test_review_migration_round_trip_preserves_legacy_evidence_without_trusting_it(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from app.db.session import make_engine
    from sqlalchemy import text
    url = f'sqlite:///{tmp_path}/legacy-review.db'
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config('alembic.ini')
    command.upgrade(config, '7419a825bc10')
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO jobs (id,url,company,title,location,description,notes,sponsorship,created_at) VALUES ('legacy','https://example.org/legacy','Owner','Engineer','','','Owner notes','UNVERIFIED','2026-11-19')"))
        connection.execute(text("INSERT INTO job_eligibility (job_id,status,evidence_quote,source_url) VALUES ('legacy','CONFIRMED_YES','Owner quote','https://example.org/legacy')"))
    command.upgrade(config, 'head')
    with Session(engine) as session:
        row = session.get(JobEligibility, 'legacy')
        assert row.evidence_quote == 'Owner quote' and row.source_hash is None
        from app.services.sponsorship import evidence
        assert evidence(session.get(Job, 'legacy'), row)['status'] == 'UNVERIFIED'
    command.downgrade(config, '7419a825bc10')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT evidence_quote FROM job_eligibility WHERE job_id='legacy'")).scalar() == 'Owner quote'
    command.upgrade(config, 'head')
    engine.dispose()


@pytest.mark.parametrize('field,value', [('company', 'Changed employer'), ('title', 'Different role'), ('location', 'Manchester'), ('deadline', '2026-12-30'), ('start_date', '2027-09-01'), ('url', 'https://example.org/different-role')])
def test_role_context_changes_also_require_fresh_review(client, field, value):
    job = vacancy(client)
    path = f"/api/jobs/{job['id']}/eligibility"
    assert client.put(path, json=body(client, job)).status_code == 200
    payload = {key: job[key] for key in ('url', 'company', 'title', 'location', 'description', 'notes', 'deadline', 'start_date', 'eligibility_requirements')}
    assert client.put(f"/api/jobs/{job['id']}", json={**payload, field: value}).json()['sponsorship'] == 'UNVERIFIED'
    assert client.get(path).json()['stale'] is True
