"""Explicit local review only. Source text never approves itself."""
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import Field, field_validator
from sqlalchemy import select

from app.db.models import Job, JobEligibility, JobSource, now
from app.routers.tracker import DB, require
from app.schemas import Nonempty, StrictModel
from app.services.sponsorship import evidence, snapshot
from app.services.urls import canonical_url

router = APIRouter()


class Review(StrictModel):
    status: Literal['CONFIRMED_YES', 'CONFIRMED_NO']
    evidence_quote: Nonempty = Field(min_length=10, max_length=5000)
    source_url: Nonempty = Field(max_length=2048)
    snapshot: str = Field(pattern=r'^[a-f0-9]{64}$')
    confirmed: Literal[True]

    @field_validator('source_url')
    @classmethod
    def url(cls, value):
        return canonical_url(value)


@router.get('/jobs/{id}/eligibility')
def get_evidence(id: str, session: DB):
    job = require(session, Job, id)
    return evidence(job, session.get(JobEligibility, id))


@router.put('/jobs/{id}/eligibility')
def review_evidence(id: str, data: Review, session: DB):
    job = require(session, Job, id)
    if data.snapshot != snapshot(job):
        raise HTTPException(409, 'Vacancy content changed. Reload and review the current description.')
    urls = {job.url, *session.scalars(select(JobSource.url).where(JobSource.job_id == id))}
    if data.source_url not in urls:
        raise HTTPException(422, 'Use a saved listing source for this job, not a company policy or licence page.')
    # Notes are owner summaries, not role-specific evidence. Keep the original quote.
    quote = ' '.join(data.evidence_quote.split())
    texts = [' '.join(text.split()) for text in (job.description, job.eligibility_requirements)]
    if not any(quote in text for text in texts):
        raise HTTPException(422, 'Quote must occur in the saved vacancy description or eligibility requirements. Notes alone cannot confirm sponsorship.')
    if 'sponsor' not in quote.lower():
        raise HTTPException(422, 'Quote the explicit role sponsorship statement, including its conditions.')
    row = session.get(JobEligibility, id) or JobEligibility(job_id=id)
    row.status = data.status
    row.evidence_quote = data.evidence_quote
    row.source_url = data.source_url
    row.source_hash = data.snapshot
    row.reviewed_at = now()
    session.add(row)
    session.commit()
    return evidence(job, row)


@router.delete('/jobs/{id}/eligibility', status_code=204)
def clear_evidence(id: str, session: DB):
    require(session, Job, id)
    row = session.get(JobEligibility, id)
    if row:
        row.status = 'UNVERIFIED'
        row.evidence_quote = row.source_url = row.source_hash = row.reviewed_at = None
        session.commit()
    return Response(status_code=204)
