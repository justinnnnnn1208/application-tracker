from sqlalchemy import select
from app.db.models import Application, ApplicationEvent, Job
from app.schemas import JobData


def ensure_job(session, data: JobData):
    existing = session.scalar(select(Job).where(Job.url == data.url))
    if existing:
        return existing, False
    job = Job(**data.model_dump())
    session.add(job)
    session.flush()
    application = Application(job_id=job.id, status="DISCOVERED")
    session.add(application)
    session.flush()
    session.add(ApplicationEvent(application_id=application.id, from_status=None, to_status="DISCOVERED"))
    return job, True
