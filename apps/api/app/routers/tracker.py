from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationEvent, Fact, Job, Profile
from app.db.session import get_session
from app.schemas import EventOut, FactData, FactOut, JobData, JobOut, ProfileData, StatusChange

router = APIRouter()
DB = Annotated[Session, Depends(get_session)]


def require(session, model, id):
    item = session.get(model, id)
    if item is None:
        raise HTTPException(404, "Record not found")
    return item


def job_out(job, application):
    return JobOut.model_validate({
        **{key: getattr(job, key) for key in JobOut.model_fields if key != "status"},
        "status": application.status,
    })


@router.get("/profile", response_model=ProfileData)
def profile(session: DB):
    return session.get(Profile, 1) or ProfileData()


@router.put("/profile", response_model=ProfileData)
def save_profile(data: ProfileData, session: DB):
    item = session.get(Profile, 1) or Profile(id=1)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/profile", status_code=204)
def delete_profile(session: DB):
    item = session.get(Profile, 1)
    if item:
        session.delete(item)
        session.commit()
    return Response(status_code=204)


@router.get("/facts", response_model=list[FactOut])
def facts(session: DB):
    return session.scalars(select(Fact).order_by(Fact.created_at, Fact.id)).all()


@router.post("/facts", response_model=FactOut, status_code=201)
def add_fact(data: FactData, session: DB):
    item = Fact(**data.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/facts/{id}", response_model=FactOut)
def update_fact(id: str, data: FactData, session: DB):
    item = require(session, Fact, id)
    # Changed content needs a fresh owner review; a second unchanged save can confirm it.
    changed = any(getattr(item, key) != getattr(data, key) for key in ("category", "content", "source"))
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    if changed:
        item.verified = False
    session.commit()
    session.refresh(item)
    return item


@router.delete("/facts/{id}", status_code=204)
def delete_fact(id: str, session: DB):
    session.delete(require(session, Fact, id))
    session.commit()
    return Response(status_code=204)


@router.get("/jobs", response_model=list[JobOut])
def jobs(session: DB):
    return [job_out(j, a) for j, a in session.execute(
        select(Job, Application).join(Application).order_by(Job.created_at.desc(), Job.id)
    )]


@router.post("/jobs", response_model=JobOut, status_code=201)
def add_job(data: JobData, session: DB, response: Response):
    existing = session.scalar(select(Job).where(Job.url == data.url))
    if existing:
        response.status_code = 200
        return job_out(existing, session.scalar(select(Application).where(Application.job_id == existing.id)))
    item = Job(**data.model_dump())
    session.add(item)
    try:
        session.flush()
        application = Application(job_id=item.id, status="DISCOVERED")
        session.add(application)
        session.flush()
        session.add(ApplicationEvent(application_id=application.id, from_status=None, to_status="DISCOVERED"))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "This job was added concurrently; refresh the list")
    session.refresh(item)
    return job_out(item, application)


@router.get("/jobs/{id}", response_model=JobOut)
def get_job(id: str, session: DB):
    item = require(session, Job, id)
    return job_out(item, session.scalar(select(Application).where(Application.job_id == id)))


@router.put("/jobs/{id}", response_model=JobOut)
def update_job(id: str, data: JobData, session: DB):
    item = require(session, Job, id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A job with that URL already exists")
    session.refresh(item)
    return job_out(item, session.scalar(select(Application).where(Application.job_id == id)))


@router.patch("/jobs/{id}/status", response_model=JobOut)
def change_status(id: str, data: StatusChange, session: DB):
    item = require(session, Job, id)
    application = session.scalar(select(Application).where(Application.job_id == id))
    old = application.status
    if old != data.expected_status:
        raise HTTPException(409, "Status changed elsewhere; refresh before saving")
    if old != data.status:
        # Compare-and-swap avoids lost status changes and incorrect history across tabs.
        from sqlalchemy import update
        result = session.execute(update(Application).where(
            Application.id == application.id, Application.status == old
        ).values(status=data.status))
        if result.rowcount != 1:
            session.rollback()
            raise HTTPException(409, "Status changed elsewhere; refresh before saving")
        session.add(ApplicationEvent(application_id=application.id, from_status=old, to_status=data.status))
        session.commit()
        session.refresh(application)
    return job_out(item, application)


@router.get("/jobs/{id}/events", response_model=list[EventOut])
def events(id: str, session: DB):
    require(session, Job, id)
    application = session.scalar(select(Application).where(Application.job_id == id))
    return session.scalars(select(ApplicationEvent).where(
        ApplicationEvent.application_id == application.id
    ).order_by(ApplicationEvent.created_at, ApplicationEvent.id)).all()
