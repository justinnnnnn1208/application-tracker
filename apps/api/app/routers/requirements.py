from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.models import Job, JobRequirements, Task
from app.routers.tracker import DB, require
from app.routers.workflows import TaskOut, enqueue
from app.schemas import StrictModel, as_utc
from app.services.requirements import configuration, validated
from app.services.sponsorship import snapshot

router = APIRouter()


class Request(StrictModel):
    job_id: str


@router.get('/jobs/{id}/requirements')
def requirements(id: str, session: DB):
    job = require(session, Job, id)
    row = session.get(JobRequirements, id)
    data = validated(job, row)
    return {'configured': configuration() is not None, 'has_description': bool(job.description.strip()),
            'state': 'not_extracted' if row is None else 'current' if data is not None else 'stale',
            'data': data.model_dump() if data is not None else None,
            'model': row.model if row else None, 'created_at': as_utc(row.created_at) if row else None,
            'source_chars': row.source_chars if row else None, 'truncated': row.truncated if row else False}


@router.post('/tasks/requirements', response_model=TaskOut, status_code=202)
def queue(data: Request, session: DB):
    job = require(session, Job, data.job_id)
    if not job.description.strip():
        raise HTTPException(409, 'Save the original vacancy description first; Notes alone are not model inputs.')
    if not configuration():
        raise HTTPException(409, 'Configure local Ollama before extracting requirements.')
    digest = snapshot(job)
    for task in session.scalars(select(Task).where(Task.kind == 'extract_requirements', Task.status.in_(['QUEUED', 'RUNNING']))):
        if task.payload == {'job_id': job.id, 'snapshot': digest}:
            return task
    return enqueue(session, 'extract_requirements', {'job_id': job.id, 'snapshot': digest})
