"""Bounded read-only aggregator search; private API key never enters task/UI data."""
import html
import json
import os
import re
from urllib.parse import urlencode, urlsplit

from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import labelled_date, plain_html
from app.services.fetching import fetch_page
from app.services.identity import ats_identity

LIMIT = 20
BASE = 'https://www.reed.co.uk/api/1.0'


def configured():
    key = os.environ.get('REED_API_KEY', '').strip()
    return bool(key and len(key) <= 1024)


def job_id(value):
    value = str(value)
    if not re.fullmatch(r'[0-9]{1,15}', value) or int(value) <= 0:
        raise ValueError('Invalid public posting ID')
    return str(int(value))


def decode(body):
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError('Invalid API object')
        return data
    except (ValueError, TypeError):
        raise NeedsInput('Reed returned invalid public API data. No partial import was saved.') from None


def read_search(query):
    if not query.strip() or len(query) > 300:
        raise NeedsInput('Supply public job-search keywords, at most 300 characters.')
    if not configured():
        raise NeedsInput('Set REED_API_KEY privately before importing aggregator results. Never paste the key into chat or the browser.')
    auth = (os.environ['REED_API_KEY'].strip(), '')
    params = urlencode({'keywords': query.strip(), 'resultsToTake': LIMIT, 'resultsToSkip': 0})
    data = decode(fetch_page(f'{BASE}/search?{params}', auth=auth))
    rows = data.get('results')
    if not isinstance(rows, list) or len(rows) > LIMIT:
        raise NeedsInput('Reed returned an invalid or oversized search page. No partial import was saved.')
    jobs, skipped, seen = [], 0, set()
    for row in rows:
        try:
            id = job_id(row['jobId'])
            if id in seen:
                raise ValueError('Repeated search identity')
            seen.add(id)
        except (ValueError, KeyError, TypeError):
            skipped += 1
            continue
        # Fetch detailed API data, never treat a search excerpt as the full vacancy.
        detail = decode(fetch_page(f'{BASE}/jobs/{id}', auth=auth))
        try:
            if job_id(detail['jobId']) != id:
                raise ValueError('Mismatched detail record')
            url = detail.get('jobUrl') or row.get('jobUrl')
            if urlsplit(url).scheme != 'https' or ats_identity(url) != f'reed:jobs:{id}':
                raise ValueError('Off-site or mismatched listing')
            description = plain_html(html.unescape(detail.get('jobDescription') or ''))
            if not description:
                raise ValueError('No detailed vacancy text')
            text = ' '.join(description.split())
            jobs.append(JobData(url=url, company=plain_html(detail.get('employerName') or row.get('employerName')),
                                title=plain_html(detail.get('jobTitle') or row.get('jobTitle')),
                                location=detail.get('locationName') or row.get('locationName') or '',
                                description=description, deadline=labelled_date(text, r'Applications? deadline'),
                                start_date=labelled_date(text, r'Start date')))
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
    return jobs, skipped
