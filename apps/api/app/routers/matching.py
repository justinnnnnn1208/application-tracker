from fastapi import APIRouter, HTTPException
from typing import Literal

from app.db.models import Job, MatchResult
from app.routers.tracker import DB, require
from app.routers.workflows import enqueue, TaskOut
from app.schemas import StrictModel
from app.services.matching import inputs, fingerprint, ready

router = APIRouter()


class MatchRequest(StrictModel):
    job_id: str


@router.post("/tasks/match", response_model=TaskOut, status_code=202)
def queue_match(data: MatchRequest, session: DB):
    job = require(session, Job, data.job_id)
    if not ready(job):
        raise HTTPException(409, "Add the role title and vacancy description before matching.")
    return enqueue(session, "match_jobs", {"job_id": data.job_id})


@router.get("/jobs/{id}/match")
def match_result(id: str, session: DB):
    job = require(session, Job, id)
    row = session.get(MatchResult, id)
    if not row:
        return None
    return {"score": row.score, "breakdown": row.breakdown, "feedback": row.feedback, "stale": row.inputs_hash != fingerprint(inputs(session, job))}


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
