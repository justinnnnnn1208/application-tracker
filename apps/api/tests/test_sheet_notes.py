from copy import deepcopy

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.models import Job, SheetLink
from app.integrations.sheets.sync import DEFAULT_MAPPING, import_sheet
from app.main import create_app
from app.services.sheet_notes import role_from_notes, backfill_sheet_details

# Public role summaries supplied by the owner; no credentials/applicant facts.
NOTES = [
    'Software Engineering / SRE Intern, London. Final-year BSc students eligible, but no immigration sponsorship.',
    '2027 Technology Graduate Programme. Sponsorship reported available.',
    '2027 Software Engineer Programme. Sponsorship reported available.',
    'Information & Digital Technology Graduate Programme. Sponsorship reported available.',
    'Software/Infrastructure Graduate, London. Sponsorship confirmed.',
    'Graduate Consultant Software Engineer, London/Manchester/Cambridge. Skilled Worker sponsorship confirmed',
    'Graduate Software Engineer, London. Sponsorship offered; choose graduate vacancy.',
    'Software Engineer, New Grad, London. Sponsorship policy requires final confirmation.',
    'Forward Deployed Software Engineer, London. Sponsorship requires confirmation.',
    'Graduate Programme 2027: Software Engineer (Java)',
    'Graduate Programme 2027: Applied AI Engineer',
    'Graduate Programme 2027: Software Engineer (Frontend)',
    'Graduate Programme 2027: Product Owner (Technical)',
    'Enterprise Data Graduate 2027, London. Sponsorship reported; verify for role.',
    'Graduate Technology / Software Engineering 2027. Sponsorship may depend on office and role.',
    'Technology Graduate Programme 2027. Sponsorship eligibility must be checked per vacancy.',
    'Graduate Software Developer, Leeds. Employer reports Skilled Worker sponsorship support.',
    'London AI/FinTech startup. Check junior engineering opportunities and visa sponsorship.',
    '2027 Software Development Engineer Intern, London and other UK cities. Python/Java relevant; sponsorship not confirmed.',
    'Graduate Software Development Engineer, London/Cambridge/Swansea/Edinburgh. Listed for 2026 rather than 2027; start-date eligibility needs checking.',
]


class NotesSheet:
    def __init__(self):
        self.values = [list(DEFAULT_MAPPING.values())] + [[f'Company {i}', '-', f'https://example.org/notes/{i}', 'Applied' if i % 5 == 0 else 'Not Started', note] for i, note in enumerate(NOTES)]
    def read(self):
        return deepcopy(self.values), deepcopy(self.values)
    def write_cell(self, *args):
        pytest.fail('Notes backfill/import must never write to Google')


def test_all_twenty_notes_import_and_reimport_without_status_or_note_changes(client):
    from app.db.models import SheetConfig
    sheet = NotesSheet()
    with Session(client.app.state.engine) as session:
        config = SheetConfig(id=1, spreadsheet_id='fixture-development-copy', tab='Tracker', header_row=1, mapping=DEFAULT_MAPPING)
        session.add(config)
        session.commit()
        first = import_sheet(session, config, sheet)
        jobs = session.scalars(select(Job).order_by(Job.url)).all()
        before = {job.id: (job.notes, job.tracker_status) for job in jobs}
        assert first['rows_preserved'] == first['jobs_created'] == 20 and first['cells_written'] == 0
        assert sum(job.title != 'Role not provided' for job in jobs) == 19
        assert all(job.sponsorship == 'UNVERIFIED' for job in jobs)
        assert next(job for job in jobs if job.url.endswith('/17')).title == 'Role not provided'
        assert next(job for job in jobs if job.url.endswith('/9')).title == 'Graduate Programme 2027: Software Engineer (Java)'
        again = import_sheet(session, config, sheet)
        assert again['rows_preserved'] == 20 and again['jobs_created'] == again['cells_written'] == 0
        assert {job.id: (job.notes, job.tracker_status) for job in jobs} == before
        # Simulate a title the owner has deliberately supplied.
        jobs[0].title = 'Owner edited title'
        session.commit()
        import_sheet(session, config, sheet)
        assert jobs[0].title == 'Owner edited title'
        # Changed Notes refresh only fields this importer derived, never manual edits.
        sheet.values[1][4] = 'Graduate Data Engineer, Manchester. Updated owner summary.'
        import_sheet(session, config, sheet)
        row_zero = session.scalar(select(Job).where(Job.url.endswith('/0')))
        assert row_zero.title == 'Owner edited title' and row_zero.location == 'Manchester'
        sheet.values[10][4] = 'Graduate Frontend Engineer, Leeds. Changed role summary.'
        import_sheet(session, config, sheet)
        row_nine = session.scalar(select(Job).where(Job.url.endswith('/9')))
        assert row_nine.title == 'Graduate Frontend Engineer, Leeds' and row_nine.location == 'Leeds'


def test_existing_imports_are_backfilled_automatically_at_api_restart(client):
    with Session(client.app.state.engine) as session:
        for index, notes in enumerate(NOTES):
            job = Job(company=f'Company {index}', title='Role not provided', url=f'https://example.org/old/{index}', notes=notes, tracker_status='Applied')
            session.add(job)
            session.flush()
            session.add(SheetLink(spreadsheet_id='fixture-development-copy', tab='Tracker', row_number=index + 2, job_id=job.id, row_hash='fixture', raw_values=[], raw_formulas=[], last_db_values={}))
        owner = Job(company='Manual', title='Owner edited role', url='https://example.org/manual', notes='Graduate Developer, Leeds.')
        session.add(owner)
        session.commit()
        owner_id = owner.id
    # Startup repair uses only already-imported local Notes, no OAuth/network needed.
    with TestClient(create_app(client.app.state.settings)):
        with Session(client.app.state.engine) as session:
            imported = session.scalars(select(Job).where(Job.company != 'Manual')).all()
            assert sum(job.title != 'Role not provided' for job in imported) == 19
            assert all(job.tracker_status == 'Applied' and job.description == '' for job in imported)
            assert backfill_sheet_details(session) == 0
            assert session.get(Job, owner_id).title == 'Owner edited role'


@pytest.mark.parametrize('notes', ['Sponsorship available for graduate roles.', 'Check junior engineering opportunities.', 'Notes only.', 'London AI startup. See careers page.', ''])
def test_generic_or_instruction_notes_do_not_invent_a_role(notes):
    assert role_from_notes(notes) is None


def test_notes_summary_can_be_matched_locally_and_edits_make_score_stale(client):
    from app.worker.tasks import run_once
    job = client.post('/api/jobs', json={'url': 'https://example.org/summary', 'company': 'Fixture', 'title': 'Graduate Software Engineer', 'notes': 'Graduate Software Engineer, London. Python relevant; sponsorship not confirmed.'}).json()
    assert client.post('/api/tasks/match', json={'job_id': job['id']}).status_code == 202
    assert run_once(client.app.state.engine, client.app.state.settings)
    assert client.get(f"/api/jobs/{job['id']}/match").json()['stale'] is False
    payload = {key: job[key] for key in ['url', 'company', 'title', 'notes']}
    payload['notes'] += ' Updated owner summary.'
    client.put(f"/api/jobs/{job['id']}", json=payload)
    assert client.get(f"/api/jobs/{job['id']}/match").json()['stale'] is True


def test_listing_enriches_notes_fields_without_next_import_reverting_them(client):
    from app.db.models import SheetConfig
    from app.schemas import JobData
    from app.services.jobs import ensure_job
    sheet = NotesSheet()
    with Session(client.app.state.engine) as session:
        config = SheetConfig(id=1, spreadsheet_id='fixture-development-copy', tab='Tracker', header_row=1, mapping=DEFAULT_MAPPING)
        session.add(config)
        session.commit()
        import_sheet(session, config, sheet)
        job = session.scalar(select(Job).where(Job.url.endswith('/0')))
        assert job.title == 'Software Engineering / SRE Intern, London'
        original_notes, original_status = job.notes, job.tracker_status
        ensure_job(session, JobData(url=job.url, company='Fetched company', title='Official Engineering Intern', location='London, United Kingdom', description='Full source vacancy description'), enrich=True)
        session.commit()
        import_sheet(session, config, sheet)
        assert job.title == 'Official Engineering Intern' and job.location == 'London, United Kingdom'
        assert job.description == 'Full source vacancy description'
        assert (job.notes, job.tracker_status) == (original_notes, original_status)
