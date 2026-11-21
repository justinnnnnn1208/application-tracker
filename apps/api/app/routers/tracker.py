from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Application, ApplicationEvent, Fact, Job, JobEligibility, Profile, Task
from app.db.session import get_session
from app.services.jobs import ensure_job
from app.services.sponsorship import effective_status, snapshot
from app.services.sponsor_register import match as register_match
from app.services.identity import ats_identity, find_existing, remember_source, possible_duplicates, AmbiguousIdentity
from app.db.models import JobSource
from app.schemas import EventOut, FactData, FactOut, JobData, JobOut, ProfileData, StatusChange, StrictModel, Nonempty
from app.services.urls import canonical_url

router = APIRouter()
DB = Annotated[Session, Depends(get_session)]


def require(session, model, id):
    item = session.get(model, id)
    if item is None:
        raise HTTPException(404, "Record not found")
    return item


def job_out(job, application, session):
    return JobOut.model_validate({
        **{key: getattr(job, key) for key in JobOut.model_fields if key not in {"status", "sponsorship_snapshot"}},
        "status": application.status,
        "sponsorship": effective_status(session, job),
        "sponsorship_snapshot": snapshot(job),
        "licensed_sponsor": register_match(session, job.company)[0],
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
    return [job_out(j, a, session) for j, a in session.execute(
        select(Job, Application).join(Application).order_by(Job.created_at.desc(), Job.id)
    )]


@router.post("/jobs", response_model=JobOut, status_code=201)
def add_job(data: JobData, session: DB, response: Response):
    try:
        item, created = ensure_job(session, data)
        session.commit()
    except (IntegrityError, AmbiguousIdentity):
        session.rollback()
        raise HTTPException(409, "A source URL or ATS identity is already linked; refresh and review the existing jobs") from None
    if not created:
        response.status_code = 200
    return job_out(item, session.scalar(select(Application).where(Application.job_id == item.id)), session)


@router.get("/jobs/{id}", response_model=JobOut)
def get_job(id: str, session: DB):
    item = require(session, Job, id)
    return job_out(item, session.scalar(select(Application).where(Application.job_id == id)), session)


@router.put("/jobs/{id}", response_model=JobOut)
def update_job(id: str, data: JobData, session: DB):
    item = require(session, Job, id)
    try:
        linked = find_existing(session, data.url)
        if linked and linked.id != id:
            raise HTTPException(409, "This source URL belongs to another tracked job")
        remember_source(session, item, data.url, "primary")
    except (AmbiguousIdentity, IntegrityError):
        session.rollback()
        raise HTTPException(409, "Ambiguous source identity; review before changing this URL") from None
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A job with that URL already exists")
    session.refresh(item)
    return job_out(item, session.scalar(select(Application).where(Application.job_id == id)), session)


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
    return job_out(item, application, session)


@router.get("/jobs/{id}/events", response_model=list[EventOut])
def events(id: str, session: DB):
    require(session, Job, id)
    application = session.scalar(select(Application).where(Application.job_id == id))
    return session.scalars(select(ApplicationEvent).where(
        ApplicationEvent.application_id == application.id
    ).order_by(ApplicationEvent.created_at, ApplicationEvent.id)).all()


@router.get("/jobs/{id}/sources")
def sources(id: str, session: DB):
    require(session, Job, id)
    return [{"id": row.id, "url": row.url, "method": row.method} for row in session.scalars(select(JobSource).where(JobSource.job_id == id).order_by(JobSource.created_at, JobSource.id))]


class SourceConfirmation(StrictModel):
    snapshot: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed: bool = Field(strict=True)


class SourceLink(SourceConfirmation):
    url: Nonempty = Field(max_length=2048)

    @field_validator('url')
    @classmethod
    def normalized_url(cls, value):
        value = canonical_url(value)
        if len(value) > 2048:
            raise ValueError('Source URL is too long')
        return value


def require_source_review(job, data, session):
    if not data.confirmed:
        raise HTTPException(422, 'Confirm that you reviewed this source change.')
    # Serialise review of this vacancy with a portable row write, without
    # changing any value. SQLite does not implement SELECT FOR UPDATE.
    session.execute(update(Job).where(Job.id == job.id).values(id=Job.id))
    session.refresh(job)
    if data.snapshot != snapshot(job):
        raise HTTPException(409, 'Vacancy changed. Reload the job and review its sources again.')


@router.post('/jobs/{id}/sources', status_code=201)
def link_source(id: str, data: SourceLink, session: DB, response: Response):
    job = require(session, Job, id)
    require_source_review(job, data, session)
    new_key = ats_identity(data.url)
    old_keys = {ats_identity(job.url)} | {ats_identity(url) for url in session.scalars(select(JobSource.url).where(JobSource.job_id == id))}
    for old_key in old_keys:
        if not old_key or not new_key or old_key == new_key:
            continue
        old_provider, old_board, _ = old_key.split(':')
        new_provider, new_board, _ = new_key.split(':')
        if (old_provider.removesuffix('-eu'), old_board) == (new_provider.removesuffix('-eu'), new_board):
            raise HTTPException(422, 'These are distinct known posting IDs or regions. Keep their applications separate.')
    try:
        existing = find_existing(session, data.url)
        if existing and existing.id != id:
            session.rollback()
            raise HTTPException(409, 'This listing belongs to another tracked job. No jobs or histories were merged.')
        if not existing:
            remember_source(session, job, data.url, 'owner_confirmed')
        else:
            response.status_code = 200
        session.commit()
    except (AmbiguousIdentity, IntegrityError):
        session.rollback()
        raise HTTPException(409, 'Source identity conflicts with existing records. No jobs or histories were merged.') from None
    row = session.scalar(select(JobSource).where(JobSource.url == data.url))
    return {'id': row.id, 'url': row.url, 'method': row.method}


@router.delete('/jobs/{id}/sources/{source_id}', status_code=204)
def unlink_source(id: str, source_id: str, data: SourceConfirmation, session: DB):
    job = require(session, Job, id)
    require_source_review(job, data, session)
    row = require(session, JobSource, source_id)
    if row.job_id != id:
        raise HTTPException(404, 'Source not found for this job.')
    if row.url == job.url or row.method != 'owner_confirmed':
        raise HTTPException(409, 'Only a secondary owner-reviewed link can be removed; saved primary/automatic provenance is retained.')
    evidence = session.get(JobEligibility, id)
    if evidence and evidence.source_url == row.url:
        raise HTTPException(409, 'This link supports a saved evidence review. Clear that review before removing the link.')
    identity = ats_identity(row.url)
    for task in session.scalars(select(Task).where(Task.kind == 'extract_url', Task.status.in_(['QUEUED', 'RUNNING']))):
        pending_url = task.payload.get('url')
        if pending_url == row.url or (identity and pending_url and ats_identity(pending_url) == identity):
            raise HTTPException(409, 'An import is pending for this link. Review its result before removing the link.')
    session.delete(row)
    session.commit()
    return Response(status_code=204)


@router.get("/jobs/{id}/duplicates")
def duplicates(id: str, session: DB):
    return possible_duplicates(session, require(session, Job, id))
