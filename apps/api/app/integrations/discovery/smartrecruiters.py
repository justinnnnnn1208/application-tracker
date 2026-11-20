"""First public company-postings page and detailed text; no candidate/form API."""
import html
import json
import re
from urllib.parse import urlsplit

from app.integrations.discovery.greenhouse import validate_board
from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import labelled_date, plain_html
from app.services.fetching import fetch_page
from app.services.identity import ats_identity

LIMIT = 20


def decode(body):
    try:
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ValueError('Expected API object')
        return value
    except (ValueError, TypeError):
        raise NeedsInput('SmartRecruiters returned invalid public data. No partial import was saved.') from None


def read_board(board, employer):
    board = validate_board(board)
    if not isinstance(employer, str) or not employer.strip() or len(employer) > 200:
        raise NeedsInput('Supply the employer name shown on the SmartRecruiters board.')
    base = f'https://api.smartrecruiters.com/v1/companies/{board}/postings'
    payload = decode(fetch_page(f'{base}?limit={LIMIT}&offset=0'))
    rows = payload.get('content')
    if not isinstance(rows, list) or len(rows) > LIMIT:
        raise NeedsInput('SmartRecruiters returned an invalid or oversized public page. No partial import was saved.')
    jobs, skipped, seen = [], 0, set()
    for row in rows:
        try:
            id = row['id']
            if not isinstance(id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', id) or id in seen:
                raise ValueError('Invalid/repeated API identity')
            seen.add(id)
        except (ValueError, KeyError, TypeError):
            skipped += 1
            continue
        # Never follow an arbitrary ref/apply URL to retrieve detailed content.
        detail = decode(fetch_page(f'{base}/{id}'))
        try:
            if detail['id'] != id or detail.get('company', {}).get('identifier', board) != board:
                raise ValueError('Mismatched company/posting')
            url = detail['applyUrl']
            parts = urlsplit(url)
            key = ats_identity(url)
            if parts.scheme != 'https' or not key or not key.startswith(f'smartrecruiters:{board}:'):
                raise ValueError('No supported public listing URL')
            sections = detail['jobAd']['sections']
            main = plain_html(html.unescape(sections['jobDescription']['text']))
            if not main:
                raise ValueError('No detailed vacancy text')
            texts = [main]
            for name in ('qualifications', 'additionalInformation'):
                if name in sections:
                    texts.append(plain_html(html.unescape(sections[name]['text'])))
            description = '\n\n'.join(text for text in texts if text)
            location = detail.get('location') or {}
            place = location.get('fullLocation') or ', '.join(location[key] for key in ('city', 'region', 'country') if location.get(key))
            text = ' '.join(description.split())
            jobs.append(JobData(url=url, company=employer.strip(), title=plain_html(detail['name']),
                                location=place, description=description,
                                deadline=labelled_date(text, r'Applications? deadline'),
                                start_date=labelled_date(text, r'Start date')))
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
    return jobs, skipped
