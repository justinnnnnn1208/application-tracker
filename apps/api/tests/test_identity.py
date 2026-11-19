import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.models import Job, JobSource, Application, ApplicationEvent
from app.services.identity import ats_identity


def payload(url, **extra):
    return {'company': 'Fixture Company', 'title': 'Graduate Software Engineer', 'location': 'London, UK', 'description': 'Fixture vacancy', 'url': url, **extra}


def test_same_posting_across_official_source_forms_keeps_one_application(client):
    original = client.post('/api/jobs', json=payload('https://job-boards.greenhouse.io/fixture/jobs/123')).json()
    for url in ['https://boards.greenhouse.io/fixture/jobs/123?utm_source=aggregate', 'https://boards.greenhouse.io/embed/job_app?for=fixture&token=123']:
        result = client.post('/api/jobs', json=payload(url, company='Different supplied text', notes='Must not replace owner notes'))
        assert result.status_code == 200 and result.json()['id'] == original['id']
    assert len(client.get('/api/jobs').json()) == 1
    assert len(client.get(f"/api/jobs/{original['id']}/events").json()) == 1
    sources = client.get(f"/api/jobs/{original['id']}/sources").json()
    assert len(sources) == 3 and sum(source['method'] == 'ats_id' for source in sources) == 2
    assert client.get('/api/jobs').json()[0]['company'] == 'Fixture Company'
    with Session(client.app.state.engine) as session:
        assert session.scalar(select(func.count()).select_from(Application)) == 1


@pytest.mark.parametrize('provider,first,second', [
    ('lever', 'https://jobs.lever.co/fixture/12345678-1234-1234-1234-123456789abc', 'https://jobs.eu.lever.co/fixture/12345678-1234-1234-1234-123456789abc/apply'),
    ('ashby', 'https://jobs.ashbyhq.com/fixture/12345678-1234-1234-1234-123456789abc', 'https://jobs.ashbyhq.com/fixture/12345678-1234-1234-1234-123456789abc/application'),
])
def test_supported_identity_forms(provider, first, second):
    assert ats_identity(first) == ats_identity(second)
    assert ats_identity(first).startswith(provider + ':')


@pytest.mark.parametrize('url', ['https://evil.example/fixture/jobs/123', 'https://boards.greenhouse.io/not-fixture/jobs/123', 'https://job-boards.greenhouse.io/fixture/jobs/124', 'https://example.org/?gh_jid=123'])
def test_similar_titles_or_unscoped_ids_do_not_auto_merge(client, url):
    client.post('/api/jobs', json=payload('https://job-boards.greenhouse.io/fixture/jobs/123'))
    assert client.post('/api/jobs', json=payload(url)).status_code == 201
    assert len(client.get('/api/jobs').json()) == 2


def test_fuzzy_candidates_are_hints_not_merges_and_different_years_are_excluded(client):
    first = client.post('/api/jobs', json=payload('https://example.org/a', title='Graduate Software Engineer - Platform 2027')).json()
    near = client.post('/api/jobs', json=payload('https://example.org/b', title='Graduate Software Engineer, Platform 2027')).json()
    client.post('/api/jobs', json=payload('https://example.org/c', title='Graduate Software Engineer, Platform 2026'))
    hints = client.get(f"/api/jobs/{first['id']}/duplicates").json()
    assert [row['id'] for row in hints] == [near['id']]
    assert len(client.get('/api/jobs').json()) == 3


def test_changing_primary_url_retains_old_source_and_cannot_steal_another_job_alias(client):
    first = client.post('/api/jobs', json=payload('https://job-boards.greenhouse.io/fixture/jobs/123')).json()
    old = first['url']
    updated = client.put(f"/api/jobs/{first['id']}", json=payload('https://example.org/new-canonical'))
    assert updated.status_code == 200
    assert client.post('/api/jobs', json=payload(old)).json()['id'] == first['id']
    second = client.post('/api/jobs', json=payload('https://example.org/other')).json()
    assert client.put(f"/api/jobs/{second['id']}", json=payload(old)).status_code == 409
    assert len(client.get('/api/jobs').json()) == 2


def test_invalid_authority_or_unbounded_identifiers_are_not_ats_keys():
    for url in ['https://boards.greenhouse.io:8443/fixture/jobs/123', 'https://boards.greenhouse.io/' + 'a' * 101 + '/jobs/123', 'https://boards.greenhouse.io/fixture/jobs/' + '1' * 31]:
        assert ats_identity(url) is None


def test_migration_preserves_old_jobs_and_histories_and_backfills_primary_sources(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from app.db.session import make_engine
    from app.schemas import JobData
    from app.services.jobs import ensure_job
    url = f'sqlite:///{tmp_path}/legacy.db'
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config('alembic.ini')
    command.upgrade(config, '5103adc629a6')
    engine = make_engine(url)
    with Session(engine) as session:
        job = Job(company='Owner employer', title='Owner title', url='https://job-boards.greenhouse.io/fixture/jobs/123', notes='Owner notes', tracker_status='Applied')
        session.add(job)
        session.flush()
        app = Application(job_id=job.id, status='SHORTLISTED')
        session.add(app)
        session.flush()
        session.add(ApplicationEvent(application_id=app.id, from_status='DISCOVERED', to_status='SHORTLISTED'))
        session.commit()
        job_id, app_id = job.id, app.id
    command.upgrade(config, 'head')
    command.check(config)
    with Session(engine) as session:
        source = session.scalar(select(JobSource))
        assert source.job_id == job_id and source.url.endswith('/123')
        job, created = ensure_job(session, JobData(**payload('https://boards.greenhouse.io/fixture/jobs/123')))
        session.commit()
        assert not created and job.id == job_id
        assert (job.title, job.notes, job.tracker_status) == ('Owner title', 'Owner notes', 'Applied')
        assert session.get(Application, app_id).status == 'SHORTLISTED'
        assert session.scalar(select(func.count()).select_from(ApplicationEvent)) == 1
    engine.dispose()


def test_ambiguous_preexisting_ats_records_are_not_merged(client):
    with Session(client.app.state.engine) as session:
        for host in ['boards.greenhouse.io', 'job-boards.greenhouse.io']:
            job = Job(**payload(f'https://{host}/fixture/jobs/123'))
            session.add(job)
            session.flush()
            session.add(JobSource(job_id=job.id, url=job.url, method='primary', identity_key=None))
            session.add(Application(job_id=job.id, status='DISCOVERED'))
        session.commit()
    result = client.post('/api/jobs', json=payload('https://boards.greenhouse.io/embed/job_app?for=fixture&token=123'))
    assert result.status_code == 409
    assert len(client.get('/api/jobs').json()) == 2
    with Session(client.app.state.engine) as session:
        assert session.scalar(select(func.count()).select_from(Application)) == 2


def test_sheet_alias_row_writes_only_its_status_cell(client, monkeypatch):
    from copy import deepcopy
    from app.db.models import SheetConfig
    from app.integrations.sheets.sync import import_sheet, DEFAULT_MAPPING, set_status
    from app.schemas import JobData
    from app.services.jobs import ensure_job
    class Sheet:
        def __init__(self):
            self.values = [list(DEFAULT_MAPPING.values()) + ['Days left'], ['Fixture Company', '-', 'https://boards.greenhouse.io/fixture/jobs/123', 'Not Started', 'Owner notes', '30']]
            self.formulas = deepcopy(self.values)
            self.formulas[1][-1] = '=B2-TODAY()'
            self.writes = []
        def read(self):
            return deepcopy(self.values), deepcopy(self.formulas)
        def cell(self, row, column, formula=False):
            return (self.formulas if formula else self.values)[row-1][column-1]
        def write_cell(self, row, column, value):
            self.writes.append((row, column, value))
            self.values[row-1][column-1] = self.formulas[row-1][column-1] = value
    sheet = Sheet()
    monkeypatch.setenv('SHEETS_WRITE_COPY_ID', 'fixture-copy-id')
    with Session(client.app.state.engine) as session:
        job, _ = ensure_job(session, JobData(**payload('https://job-boards.greenhouse.io/fixture/jobs/123')))
        config = SheetConfig(id=1, spreadsheet_id='fixture-copy-id', tab='Tracker', header_row=1, mapping=DEFAULT_MAPPING)
        session.add(config)
        session.commit()
        import_sheet(session, config, sheet)
        set_status(session, job, 'SHORTLISTED')
        session.commit()
        result = import_sheet(session, config, sheet, write=True)
        assert result['cells_written'] == 1 and sheet.writes == [(2, 4, 'Shortlisted')]
        assert sheet.values[1][4] == 'Owner notes' and sheet.formulas[1][-1] == '=B2-TODAY()'
        assert len(session.scalars(select(Job)).all()) == 1
