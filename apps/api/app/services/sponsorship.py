"""Owner-reviewed role evidence, separate from preference scores and licences."""
import hashlib
import json

from app.db.models import JobEligibility
from app.schemas import as_utc


def snapshot(job):
    fields = {key: getattr(job, key) for key in ('url', 'company', 'title', 'location', 'deadline', 'start_date', 'description', 'eligibility_requirements')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def evidence(job, row):
    current = bool(row and row.source_hash == snapshot(job) and row.reviewed_at and row.evidence_quote and row.source_url)
    return {
        'status': row.status if current else 'UNVERIFIED',
        'evidence_quote': row.evidence_quote if row else None,
        'source_url': row.source_url if row else None,
        'reviewed_at': as_utc(row.reviewed_at) if row and row.reviewed_at else None,
        'stale': bool(row and row.status != 'UNVERIFIED' and not current),
        'snapshot': snapshot(job),
    }


def effective_status(session, job):
    return evidence(job, session.get(JobEligibility, job.id))['status']
