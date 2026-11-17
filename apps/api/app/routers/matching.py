from fastapi import APIRouter, HTTPException
from typing import Literal

from sqlalchemy import select
from app.db.models import Application, Job, MatchResult, Task
from app.routers.tracker import DB, require
from app.routers.workflows import enqueue, TaskOut
from app.schemas import StrictModel
from app.services.matching import inputs, fingerprint, ready, shared_inputs, active_for_matching

router = APIRouter()


class MatchRequest(StrictModel):
    job_id: str | None = None


@router.post("/tasks/match", response_model=TaskOut, status_code=202)
def queue_match(data: MatchRequest, session: DB):
    if data.job_id is None:
        ids = sorted(job.id for job, app in session.execute(select(Job, Application).join(Application)) if ready(job) and active_for_matching(job, app))
        if not ids:
            raise HTTPException(409, "No active jobs have enough role/summary details to score.")
        if len(ids) > 500:
            raise HTTPException(409, "Batch scoring supports up to 500 active jobs. Score individual jobs or archive completed rows first.")
        for task in session.scalars(select(Task).where(Task.kind == "match_jobs", Task.status.in_(["QUEUED", "RUNNING"]))):
            if task.payload.get("job_ids") == ids:
                return task
        return enqueue(session, "match_jobs", {"job_ids": ids})
    job = require(session, Job, data.job_id)
    if not ready(job):
        raise HTTPException(409, "Add the role title and vacancy description or Sheet Notes summary before matching.")
    return enqueue(session, "match_jobs", {"job_id": data.job_id})


@router.get("/jobs/{id}/match")
def match_result(id: str, session: DB):
    job = require(session, Job, id)
    row = session.get(MatchResult, id)
    if not row:
        return None
    return {"score": row.score, "breakdown": row.breakdown, "feedback": row.feedback, "stale": row.inputs_hash != fingerprint(inputs(session, job))}


@router.get("/matches")
def summaries(session: DB):
    rows = {row.job_id: row for row in session.scalars(select(MatchResult))}
    shared = shared_inputs(session)
    results = {}
    for job, application in session.execute(select(Job, Application).join(Application)):
        row = rows.get(job.id)
        state = "inactive" if not active_for_matching(job, application) else "needs_details" if not ready(job) else "not_scored" if row is None else "stale" if row.inputs_hash != fingerprint(inputs(session, job, shared)) else "current"
        results[job.id] = {"state": state, "score": row.score if state == "current" else None}
    return results


class Feedback(StrictModel):
    value: Literal["good", "bad"]


@router.post("/jobs/{id}/feedback")
def feedback(id: str, data: Feedback, session: DB):
    job = require(session, Job, id)
    row = session.get(MatchResult, id)
    if not row or row.inputs_hash != fingerprint(inputs(session, job)):
        raise HTTPException(409, "Calculate a current match before rating it")
    row.feedback = data.value
    session.commit()
    return {"saved": True}
