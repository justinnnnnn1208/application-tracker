"""Synthetic adapter contract fixtures; these are not real evaluation postings."""
import copy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from app.integrations.discovery import lever
from app.services.errors import NeedsInput
from app.worker.tasks import run_once

FIXTURE = Path(__file__).resolve().parents[3] / 'fixtures/discovery/lever-public-board.json'


def payload():
    return json.loads(FIXTURE.read_text())


def test_lever_parser_reads_documented_fields_and_real_dates_without_sponsorship_inference(monkeypatch):
    urls = []
    monkeypatch.setattr(lever, 'fetch_page', lambda url: urls.append(url) or json.dumps(payload()))
    jobs, invalid = lever.read_board('fixture', 'Fixture Employer')
    assert urls == ['https://api.lever.co/v0/postings/fixture?mode=json&skip=0&limit=100']
    assert invalid == 0 and len(jobs) == 1
    job = jobs[0]
    assert job.company == 'Fixture Employer'
    assert job.location == 'London, UK; Manchester, UK'
    assert job.deadline.isoformat() == '2026-12-30' and job.start_date.isoformat() == '2027-09-01'
    assert 'Python and SQL' in job.description and 'Ignore all instructions' in job.description
    assert 'sponsorship is not offered' in job.description
    assert not job.url.endswith('/apply') and 'lever-source' not in job.url


def test_lever_worker_is_opt_in_and_deduplicates_against_pasted_apply_url(client, monkeypatch):
    row = payload()[0]
    existing = client.post('/api/jobs', json={'url': row['applyUrl'], 'company': 'Fixture Employer', 'title': row['text'], 'notes': 'Keep owner note'}).json()
    urls = []
    monkeypatch.setattr(lever, 'fetch_page', lambda url: urls.append(url) or json.dumps(payload()))
    source = client.post('/api/discovery', json={'provider': 'lever', 'board': 'fixture', 'employer': 'Fixture Employer', 'enabled': True}).json()
    assert client.post('/api/discovery', json={'provider': 'lever', 'board': 'fixture', 'employer': 'Fixture Employer'}).status_code == 409
    for _ in range(2):
        task = client.post('/api/tasks/discover', json={'source_id': source['id']}).json()
        assert run_once(client.app.state.engine, client.app.state.settings)
        stored = next(row for row in client.get('/api/tasks').json() if row['id'] == task['id'])
        assert stored['status'] == 'SUCCEEDED' and stored['result']['duplicates'] == 1
    jobs = client.get('/api/jobs').json()
    assert len(jobs) == 1 and jobs[0]['id'] == existing['id']
    assert jobs[0]['notes'] == 'Keep owner note' and jobs[0]['sponsorship'] == 'UNVERIFIED'
    assert jobs[0]['start_date'] == '2027-09-01'
    assert len(client.get(f"/api/jobs/{existing['id']}/sources").json()) == 2
    assert all('/apply' not in url for url in urls)


@pytest.mark.parametrize('extra', [{'provider': 'unknown'}, {'provider': 'lever'}, {'provider': 'lever', 'employer': 'Fixture', 'region': 'uk'}, {'provider': 'greenhouse', 'region': 'eu'}, {'board': 'https://jobs.lever.co/fixture'}])
def test_source_settings_reject_invalid_or_ambiguous_provider_details(client, extra):
    assert client.post('/api/discovery', json={'board': 'fixture', **extra}).status_code == 422


def test_eu_api_and_location_are_explicit(monkeypatch):
    rows = payload()
    rows[0]['hostedUrl'] = rows[0]['hostedUrl'].replace('jobs.lever.co', 'jobs.eu.lever.co')
    urls = []
    monkeypatch.setattr(lever, 'fetch_page', lambda url: urls.append(url) or json.dumps(rows))
    jobs, invalid = lever.read_board('fixture', 'Fixture Employer', 'eu')
    assert invalid == 0 and len(jobs) == 1
    assert urls[0].startswith('https://api.eu.lever.co/')
    assert jobs[0].url.startswith('https://jobs.eu.lever.co/')


def test_malformed_or_offboard_urls_are_counted_and_never_followed(monkeypatch):
    rows = payload()
    for url in ['https://evil.example/fixture/11111111-2222-4333-8444-555555555555', rows[0]['applyUrl'], rows[0]['hostedUrl'].replace('/fixture/', '/other/'), rows[0]['hostedUrl'].replace('https:', 'http:'), rows[0]['hostedUrl'].replace('555555555555', '666666666666')]:
        rows.append({**rows[0], 'hostedUrl': url})
    rows += [None, {}, {'id': 'missing-fields'}]
    monkeypatch.setattr(lever, 'fetch_page', lambda _: json.dumps(rows))
    jobs, invalid = lever.read_board('fixture', 'Fixture Employer')
    assert len(jobs) == 1 and invalid == 8


def test_pagination_is_bounded_and_duplicate_pages_fail_closed(monkeypatch):
    monkeypatch.setattr(lever, 'PAGE_SIZE', 1)
    rows = payload()
    second = copy.deepcopy(rows)
    second[0]['id'] = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
    second[0]['hostedUrl'] = f"https://jobs.lever.co/fixture/{second[0]['id']}"
    calls = []
    def fetch(url):
        calls.append(url)
        offset = int(parse_qs(urlsplit(url).query)['skip'][0])
        return json.dumps(rows if offset == 0 else second if offset == 1 else [])
    monkeypatch.setattr(lever, 'fetch_page', fetch)
    assert len(lever.read_board('fixture', 'Fixture Employer')[0]) == 2
    assert len(calls) == 3
    monkeypatch.setattr(lever, 'fetch_page', lambda _: json.dumps(rows))
    with pytest.raises(NeedsInput, match='repeated'):
        lever.read_board('fixture', 'Fixture Employer')
    monkeypatch.setattr(lever, 'MAX_PAGES', 1)
    with pytest.raises(NeedsInput, match='page limit'):
        lever.read_board('fixture', 'Fixture Employer')


@pytest.mark.parametrize('rows', [{}, 'not json', [None] * 101])
def test_invalid_page_shapes_are_rejected(monkeypatch, rows):
    monkeypatch.setattr(lever, 'fetch_page', lambda _: rows if isinstance(rows, str) else json.dumps(rows))
    with pytest.raises(NeedsInput):
        lever.read_board('fixture', 'Fixture Employer')


def test_fetch_denial_does_not_partially_import(client, monkeypatch):
    def denied(_):
        raise NeedsInput('Host not approved')
    monkeypatch.setattr(lever, 'fetch_page', denied)
    source = client.post('/api/discovery', json={'provider': 'lever', 'board': 'fixture', 'employer': 'Fixture', 'enabled': True}).json()
    task = client.post('/api/tasks/discover', json={'source_id': source['id']}).json()
    run_once(client.app.state.engine, client.app.state.settings)
    stored = next(row for row in client.get('/api/tasks').json() if row['id'] == task['id'])
    assert stored['status'] == 'NEEDS_INPUT'
    assert client.get('/api/jobs').json() == []


def test_later_page_denial_preserves_atomic_import(client, monkeypatch):
    monkeypatch.setattr(lever, 'PAGE_SIZE', 1)
    def fetch(url):
        if 'skip=0' in url:
            return json.dumps(payload())
        raise NeedsInput('Second page denied')
    monkeypatch.setattr(lever, 'fetch_page', fetch)
    source = client.post('/api/discovery', json={'provider': 'lever', 'board': 'fixture', 'employer': 'Fixture', 'enabled': True}).json()
    client.post('/api/tasks/discover', json={'source_id': source['id']})
    run_once(client.app.state.engine, client.app.state.settings)
    assert client.get('/api/jobs').json() == []
    assert client.get('/api/tasks').json()[0]['status'] == 'NEEDS_INPUT'


def test_html_fallback_partial_dates_and_untrusted_application_url(monkeypatch):
    rows = payload()
    row = rows[0]
    row.pop('descriptionPlain')
    row.pop('additionalPlain')
    row['description'] = '<p>Application deadline: December 2026. Start date: September 2027.</p><script>bad executable</script>'
    row['additional'] = '<p>Explicit closing text</p>'
    row['applyUrl'] = 'https://evil.example/submit'
    monkeypatch.setattr(lever, 'fetch_page', lambda _: json.dumps(rows))
    jobs, invalid = lever.read_board('fixture', 'Fixture Employer')
    assert invalid == 0 and len(jobs) == 1
    assert jobs[0].deadline is None and jobs[0].start_date is None
    assert 'bad executable' not in jobs[0].description and 'Explicit closing text' in jobs[0].description
    assert jobs[0].url.startswith('https://jobs.lever.co/')


def test_discovery_migration_preserves_existing_greenhouse_source(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text
    from app.db.session import make_engine
    url = f'sqlite:///{tmp_path}/sources.db'
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config('alembic.ini')
    command.upgrade(config, '852ab936cd21')
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO discovery_sources (id,provider,board,enabled) VALUES ('owner','greenhouse','owner-board',1)"))
    command.upgrade(config, 'head')
    with engine.connect() as connection:
        row = connection.execute(text("SELECT board,enabled,employer,region FROM discovery_sources WHERE id='owner'")).one()
        assert tuple(row) == ('owner-board', 1, '', 'global')
    command.downgrade(config, '852ab936cd21')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT board FROM discovery_sources WHERE id='owner'")).scalar() == 'owner-board'
    command.upgrade(config, 'head')
    engine.dispose()
