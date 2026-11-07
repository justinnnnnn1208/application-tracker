from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import Document, FactCandidate, Preferences, Schedule, SheetConfig, Task, now
from app.integrations.llm.provider import configured_provider
from app.integrations.sheets.client import GoogleSheet
from app.integrations.sheets.sync import import_sheet
from app.schemas import as_utc
from app.services.backups import backup
from app.services.cv import candidates, extract_text
from app.services.errors import NeedsInput
from app.services.extraction import extract_job
from app.services.fetching import fetch_page
from app.services.jobs import ensure_job


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
    if task.kind == "extract_url":
        html = task.payload.get("page_html") or fetch_page(task.payload["url"])
        data = extract_job(task.payload["url"], html, configured_provider())
        job, created = ensure_job(session, data)
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
    if task.kind == "sheets_sync":
        raise NeedsInput("Sheet write-back is disabled. Use read-only import.")
    if task.kind == "sheets_import":
        config = session.get(SheetConfig, 1)
        if not config:
            raise NeedsInput("Configure a test-copy spreadsheet and its header mapping first.")
        sheet = GoogleSheet(session, config)
        try:
            return import_sheet(session, config, sheet)
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
