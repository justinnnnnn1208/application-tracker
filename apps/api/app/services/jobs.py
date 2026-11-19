from sqlalchemy import select
from app.db.models import Application, ApplicationEvent, Job, SheetLink
from app.schemas import JobData
from app.services.identity import find_existing, remember_source


def ensure_job(session, data: JobData, enrich=False):
    existing = find_existing(session, data.url)
    if existing:
        if enrich:
            # Fill imported stubs, never overwrite existing owner content/history.
            note_fields = {}
            for link in session.scalars(select(SheetLink).where(SheetLink.job_id == existing.id)):
                note_fields.update((link.last_db_values or {}).get("_notes_fields", {}))
            if existing.title == "Role not provided" or note_fields.get("title") == existing.title:
                existing.title = data.title
            if existing.company == "Employer not provided":
                existing.company = data.company
            for field in ("location", "description", "eligibility_requirements", "start_date", "deadline"):
                if (not getattr(existing, field) or note_fields.get(field) == getattr(existing, field)) and getattr(data, field):
                    setattr(existing, field, getattr(data, field))
        return existing, False
    job = Job(**data.model_dump())
    session.add(job)
    session.flush()
    remember_source(session, job, data.url, "primary")
    application = Application(job_id=job.id, status="DISCOVERED")
    session.add(application)
    session.flush()
    session.add(ApplicationEvent(application_id=application.id, from_status=None, to_status="DISCOVERED"))
    return job, True
