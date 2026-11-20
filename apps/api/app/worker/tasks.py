from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import Application, MatchResult, DiscoverySource, Job, Document, FactCandidate, Preferences, Schedule, SheetConfig, Task, now
from app.integrations.llm.provider import configured_provider
from app.integrations.discovery.greenhouse import read_board
from app.integrations.discovery.ashby import read_board as read_ashby_board
from app.integrations.discovery.lever import read_board as read_lever_board
from app.integrations.sheets.client import GoogleSheet
from app.integrations.sheets.sync import import_sheet
from app.schemas import as_utc
from app.services.backups import backup
from app.services.cv import candidates, extract_text
from app.services.errors import NeedsInput
from app.services.extraction import extract_job
from app.services.fetching import fetch_page
from app.services.jobs import ensure_job
from app.services.sponsor_register import import_register
from app.services.requirements import save as save_requirements
from app.services.sponsorship import snapshot
from app.services.matching import save_match, shared_inputs, inputs, fingerprint, ready, active_for_matching


def catch_up(session, current=None):
    current = current or now()
    queued = []
    for schedule in session.scalars(select(Schedule).where(Schedule.next_due <= current)):
        # Advance to the next future occurrence, enqueueing only once after a laptop sleep.
        due = as_utc(schedule.next_due)
        intervals = int((current - due).total_seconds()) // schedule.interval_seconds + 1
        claimed = session.execute(update(Schedule).where(Schedule.name == schedule.name, Schedule.next_due == schedule.next_due).values(next_due=due + timedelta(seconds=intervals * schedule.interval_seconds)), execution_options={"synchronize_session": False})
        if claimed.rowcount:
            existing = session.scalar(select(Task).where(Task.kind == schedule.kind, Task.status.in_(["QUEUED", "RUNNING"])))
            if not existing:
                task = Task(kind=schedule.kind, payload=schedule.payload)
                session.add(task)
                queued.append(task)
    session.commit()
    return queued


def execute(session, task, settings):
    if task.kind == "import_sponsor_register":
        return import_register(session, settings, task.payload)
    if task.kind == "extract_requirements":
        job = session.get(Job, task.payload.get("job_id"))
        if not job or snapshot(job) != task.payload.get("snapshot"):
            raise NeedsInput("Vacancy changed or was removed. Request fresh requirements extraction.")
        return save_requirements(session, job)
    if task.kind == "match_jobs":
        if "job_ids" in task.payload:
            ids = task.payload["job_ids"]
            if not isinstance(ids, list) or len(ids) > 500:
                raise NeedsInput("Invalid scoring batch; request a fresh bounded batch.")
            shared = shared_inputs(session)
            rows = session.execute(select(Job, Application).join(Application).where(Job.id.in_(ids))).all()
            counts = {"matched": 0, "current": 0, "skipped": len(ids) - len(rows)}
            for job, application in rows:
                if not ready(job) or not active_for_matching(job, application):
                    counts["skipped"] += 1
                    continue
                previous = session.get(MatchResult, job.id)
                if previous and previous.inputs_hash == fingerprint(inputs(session, job, shared)):
                    counts["current"] += 1
                    continue
                save_match(session, job, shared=shared, commit=False)
                counts["matched"] += 1
            session.commit()
            return counts
        job = session.get(Job, task.payload.get("job_id"))
        if not job:
            raise NeedsInput("The job no longer exists.")
        return {"job_id": job.id, **save_match(session, job)}
    if task.kind == "discover":
        source = session.get(DiscoverySource, task.payload.get("source_id"))
        if not source or not source.enabled or source.provider not in {"greenhouse", "lever", "ashby"}:
            raise NeedsInput("The discovery source is missing, disabled or unsupported.")
        if source.provider == "lever":
            jobs, warnings = read_lever_board(source.board, source.employer, source.region)
        elif source.provider == "ashby":
            jobs, warnings = read_ashby_board(source.board, source.employer)
        else:
            jobs, warnings = read_board(source.board)
        if source.provider == "greenhouse" and source.employer:
            for data in jobs:
                if data.company == "Employer not provided":
                    data.company = source.employer
        created = 0
        for data in jobs:
            _, added = ensure_job(session, data, enrich=True)
            created += int(added)
        session.commit()
        return {"postings_read": len(jobs), "jobs_created": created, "duplicates": len(jobs) - created, "warnings": warnings}
    if task.kind == "extract_url":
        html = task.payload.get("page_html") or fetch_page(task.payload["url"])
        data = extract_job(task.payload["url"], html, configured_provider())
        job, created = ensure_job(session, data, enrich=True)
        session.commit()
        return {"job_id": job.id, "created": created}
    if task.kind == "parse_cv":
        document = session.get(Document, task.payload["document_id"])
        if not document:
            raise NeedsInput("The uploaded document could not be found.")
        existing = session.scalars(select(FactCandidate).where(FactCandidate.document_id == document.id)).all()
        if not existing:
            data = (settings.storage_dir / "documents" / document.id).read_bytes()
            for candidate in candidates(extract_text(data, document.format)):
                session.add(FactCandidate(document_id=document.id, **candidate))
            session.commit()
        count = len(session.scalars(select(FactCandidate).where(FactCandidate.document_id == document.id)).all())
        if not count:
            raise NeedsInput("No fact candidates were identified. Add facts manually after checking the CV.")
        return {"document_id": document.id, "candidates": count}
    if task.kind in {"sheets_import", "sheets_sync"}:
        config = session.get(SheetConfig, 1)
        if not config:
            raise NeedsInput("Configure a test-copy spreadsheet and its header mapping first.")
        sheet = GoogleSheet(session, config, write=task.kind == "sheets_sync")
        try:
            return import_sheet(session, config, sheet, write=task.kind == "sheets_sync")
        finally:
            sheet.close()
    if task.kind == "backup":
        preferences = session.get(Preferences, 1)
        if not preferences or not preferences.backup_dir:
            raise NeedsInput("Choose a backup destination in Settings first.")
        return backup(settings, Path(preferences.backup_dir))
    raise NeedsInput("This task type is not supported.")


def run_once(engine, settings):
    with Session(engine) as session:
        task = session.scalar(select(Task).where(Task.status == "QUEUED").order_by(Task.created_at, Task.id))
        if not task:
            return False
        claimed = session.execute(update(Task).where(Task.id == task.id, Task.status == "QUEUED").values(status="RUNNING", started_at=now()))
        session.commit()
        if claimed.rowcount != 1:
            return False
        try:
            result = execute(session, task, settings)
            task.status, task.result, task.message = "SUCCEEDED", result, None
        except NeedsInput as error:
            session.rollback()
            task.status, task.message = "NEEDS_INPUT", str(error)
        except Exception:
            session.rollback()
            # Never log task payloads, CVs, HTTP bodies, OAuth secrets or SQL parameters.
            task.status, task.message = "FAILED", "The task failed safely. Check configuration and input; no automatic retry was scheduled."
        task.finished_at = now()
        session.commit()
        return True
