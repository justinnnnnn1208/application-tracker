from sqlalchemy import select
from app.db.models import Application, ApplicationEvent, Job
from app.schemas import JobData


def ensure_job(session, data: JobData, enrich=False):
    existing = session.scalar(select(Job).where(Job.url == data.url))
    if existing:
        if enrich:
            # Fill imported stubs, never overwrite existing owner content/history.
            if existing.title == "Role not provided":
                existing.title = data.title
            if existing.company == "Employer not provided":
                existing.company = data.company
            for field in ("location", "description", "eligibility_requirements", "start_date", "deadline"):
                if not getattr(existing, field) and getattr(data, field):
                    setattr(existing, field, getattr(data, field))
        return existing, False
    job = Job(**data.model_dump())
    session.add(job)
    session.flush()
    application = Application(job_id=job.id, status="DISCOVERED")
    session.add(application)
    session.flush()
    session.add(ApplicationEvent(application_id=application.id, from_status=None, to_status="DISCOVERED"))
    return job, True
