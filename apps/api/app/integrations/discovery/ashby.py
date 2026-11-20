"""Bounded public posting-board data only; never private ATS or application APIs."""
import html
import json
from urllib.parse import urlsplit

from app.integrations.discovery.greenhouse import validate_board
from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import labelled_date, plain_html
from app.services.fetching import fetch_page
from app.services.identity import ats_identity


def read_board(board, employer):
    board = validate_board(board)
    if not isinstance(employer, str) or not employer.strip() or len(employer) > 200:
        raise NeedsInput('Supply the employer name shown on the Ashby board.')
    body = fetch_page(f'https://api.ashbyhq.com/posting-api/job-board/{board}')
    try:
        payload = json.loads(body)
        rows = payload['jobs']
        if payload.get('apiVersion') not in {None, '1', 1} or not isinstance(rows, list) or len(rows) > 2000:
            raise ValueError('Unsupported public board shape')
    except (ValueError, KeyError, TypeError):
        raise NeedsInput('Ashby returned invalid, oversized or unsupported public posting data.') from None
    jobs, skipped = [], 0
    for row in rows:
        try:
            if not isinstance(row, dict) or row.get('isListed') is not True or not isinstance(row.get('id'), str):
                raise ValueError('Only explicitly listed public postings are supported')
            url = row['jobUrl']
            parts = urlsplit(url)
            if parts.scheme != 'https' or parts.hostname != 'jobs.ashbyhq.com' or len(parts.path.strip('/').split('/')) != 2 or ats_identity(url) != f"ashby:{board}:{row['id'].lower()}":
                raise ValueError('Off-board or mismatched posting URL')
            description = row.get('descriptionPlain')
            if not isinstance(description, str):
                description = plain_html(html.unescape(row.get('descriptionHtml') or ''))
            location = row.get('location') or row.get('locationName') or ''
            if not isinstance(location, str):
                raise ValueError('Invalid location')
            text = ' '.join(description.split())
            jobs.append(JobData(url=url, company=employer.strip(), title=plain_html(row['title']),
                                location=location, description=description,
                                deadline=labelled_date(text, r'Applications? deadline'),
                                start_date=labelled_date(text, r'Start date')))
        except (ValueError, KeyError, TypeError, AttributeError):
            skipped += 1
    return jobs, skipped
