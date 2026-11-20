"""Authoritative ATS identities; fuzzy text is a review hint, never an auto-merge."""
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import select

from app.db.models import Job, JobSource
from app.services.errors import NeedsInput
from app.services.urls import canonical_url


class AmbiguousIdentity(NeedsInput):
    pass


def ats_identity(url):
    parts = urlsplit(canonical_url(url))
    if parts.port is not None:
        return None
    path = parts.path.strip('/').split('/')
    if parts.hostname in {'reed.co.uk', 'www.reed.co.uk'} and len(path) == 3 and path[0] == 'jobs' and re.fullmatch(r'[0-9]{1,15}', path[2]) and int(path[2]) > 0:
        return f'reed:jobs:{int(path[2])}'
    if parts.hostname in {'boards.greenhouse.io', 'job-boards.greenhouse.io', 'boards.eu.greenhouse.io', 'job-boards.eu.greenhouse.io'}:
        if len(path) == 3 and re.fullmatch(r'[A-Za-z0-9_-]{1,100}', path[0]) and path[1] == 'jobs' and re.fullmatch(r'[0-9]{1,30}', path[2]):
            provider = 'greenhouse-eu' if '.eu.greenhouse.io' in parts.hostname else 'greenhouse'
            return f'{provider}:{path[0]}:{path[2]}'
        query = parse_qs(parts.query)
        if parts.path == '/embed/job_app' and len(query.get('for', [])) == len(query.get('token', [])) == 1 and re.fullmatch(r'[A-Za-z0-9_-]{1,100}', query['for'][0]) and re.fullmatch(r'[0-9]{1,30}', query['token'][0]):
            provider = "greenhouse-eu" if ".eu.greenhouse.io" in parts.hostname else "greenhouse"
            return f"{provider}:{query['for'][0]}:{query['token'][0]}"
    providers = {'jobs.lever.co': 'lever', 'jobs.eu.lever.co': 'lever-eu', 'jobs.ashbyhq.com': 'ashby'}
    if parts.hostname in providers and len(path) in {2, 3} and re.fullmatch(r'[A-Za-z0-9_-]{1,100}', path[0]) and (len(path) == 2 or path[2] in {'apply', 'application'}):
        if re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', path[1]):
            return f'{providers[parts.hostname]}:{path[0]}:{path[1].lower()}'
    return None


def remember_source(session, job, url, method):
    url = canonical_url(url)
    current = session.scalar(select(JobSource).where(JobSource.url == url))
    if current:
        if current.job_id != job.id:
            raise AmbiguousIdentity('This source URL is already linked to another tracked job. Review it before importing.')
        return
    session.add(JobSource(job_id=job.id, url=url, identity_key=ats_identity(url) or '', method=method))
    session.flush()


def find_existing(session, url):
    url = canonical_url(url)
    exact = session.scalar(select(Job).where(Job.url == url))
    if exact:
        remember_source(session, exact, url, 'primary')
        return exact
    alias = session.scalar(select(JobSource).where(JobSource.url == url))
    if alias:
        return session.get(Job, alias.job_id)
    key = ats_identity(url)
    if not key:
        return None
    # Old primary URLs are backfilled by migration; index their identities lazily.
    for source in session.scalars(select(JobSource).where(JobSource.identity_key.is_(None))):
        source.identity_key = ats_identity(source.url) or ''
    session.flush()
    ids = set(session.scalars(select(JobSource.job_id).where(JobSource.identity_key == key)))
    if len(ids) > 1:
        raise AmbiguousIdentity('Multiple existing jobs share this ATS identity. No histories were merged; review the records.')
    if ids:
        job = session.get(Job, ids.pop())
        remember_source(session, job, url, 'ats_id')
        return job
    return None


def normalized(value):
    return ' '.join(re.findall(r'\w+', value.casefold()))


def possible_duplicates(session, job):
    if job.title == 'Role not provided' or not job.location or job.company == 'Employer not provided':
        return []
    candidates = []
    identity = ats_identity(job.url)
    for other in session.scalars(select(Job).where(Job.id != job.id)):
        other_identity = ats_identity(other.url)
        if identity and other_identity and identity.rsplit(':', 1)[0] == other_identity.rsplit(':', 1)[0] and identity != other_identity:
            continue  # Distinct known requisitions are not a fuzzy duplicate hint.
        if normalized(other.company) != normalized(job.company) or normalized(other.location) != normalized(job.location) or other.title == 'Role not provided':
            continue
        if re.findall(r'\d+', other.title) != re.findall(r'\d+', job.title):
            continue  # Different programme year/level is not a close-title hint.
        ratio = SequenceMatcher(None, normalized(job.title), normalized(other.title)).ratio()
        if ratio >= .9:
            candidates.append({'id': other.id, 'title': other.title, 'company': other.company, 'location': other.location, 'similarity': round(ratio, 3)})
    return sorted(candidates, key=lambda row: (-row['similarity'], row['id']))[:10]
