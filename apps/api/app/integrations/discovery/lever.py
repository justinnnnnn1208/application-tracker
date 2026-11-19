"""Read-only, bounded official Lever postings API; never application endpoints."""
import html
import json
from urllib.parse import urlsplit

from app.integrations.discovery.greenhouse import validate_board
from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import labelled_date, plain_html
from app.services.fetching import fetch_page
from app.services.identity import ats_identity

PAGE_SIZE = 100
MAX_PAGES = 20


def posting(row, board, employer, region):
    if not isinstance(row, dict) or not isinstance(row.get('id'), str):
        raise ValueError('Missing posting identity')
    url = row['hostedUrl']
    host = 'jobs.eu.lever.co' if region == 'eu' else 'jobs.lever.co'
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != host or len(parts.path.strip("/").split("/")) != 2 or ats_identity(url) != f"lever:{board}:{row['id'].lower()}":
        raise ValueError('Posting URL must match provider, board and ID')
    categories = row.get('categories') or {}
    if not isinstance(categories, dict):
        raise ValueError('Invalid categories')
    places = [categories.get('location', '')]
    all_places = categories.get('allLocations') or []
    if not isinstance(all_places, list) or len(all_places) > 50:
        raise ValueError('Invalid locations')
    places += all_places
    if any(not isinstance(place, str) for place in places):
        raise ValueError('Invalid location')
    description = row.get('descriptionPlain')
    if not isinstance(description, str):
        description = plain_html(html.unescape(row.get('description') or ''))
    sections = [description]
    lists = row.get('lists') or []
    if not isinstance(lists, list) or len(lists) > 100:
        raise ValueError('Invalid requirement lists')
    for section in lists:
        if not isinstance(section, dict):
            raise ValueError('Invalid list section')
        sections.extend([plain_html(section.get('text')), plain_html(html.unescape(section.get('content') or ''))])
    closing = row.get('additionalPlain')
    sections.append(closing if isinstance(closing, str) else plain_html(html.unescape(row.get('additional') or '')))
    description = '\n'.join(section for section in sections if section)
    text = ' '.join(description.split())
    return JobData(url=url, title=plain_html(row['text']), company=employer,
                   location='; '.join(dict.fromkeys(place for place in places if place)),
                   description=description,
                   deadline=labelled_date(text, r'Applications? deadline'),
                   start_date=labelled_date(text, r'Start date'))


def read_board(board, employer, region='global'):
    board = validate_board(board)
    if region not in {'global', 'eu'} or not isinstance(employer, str) or not employer.strip() or len(employer) > 200:
        raise NeedsInput('Choose the Lever region and supply the employer name shown on its board.')
    host = 'api.eu.lever.co' if region == 'eu' else 'api.lever.co'
    jobs, invalid, seen = [], 0, set()
    for page in range(MAX_PAGES):
        body = fetch_page(f'https://{host}/v0/postings/{board}?mode=json&skip={page * PAGE_SIZE}&limit={PAGE_SIZE}')
        try:
            rows = json.loads(body)
            if not isinstance(rows, list) or len(rows) > PAGE_SIZE:
                raise ValueError('Invalid page')
        except (ValueError, TypeError):
            raise NeedsInput('The public Lever API returned invalid or oversized posting data.') from None
        for row in rows:
            try:
                data = posting(row, board, employer.strip(), region)
                identity = ats_identity(data.url)
                if identity in seen:
                    raise NeedsInput('The board repeated or changed paginated postings. No jobs were imported; try manually later.')
                seen.add(identity)
                jobs.append(data)
            except (ValueError, KeyError, TypeError, AttributeError):
                invalid += 1
        if len(rows) < PAGE_SIZE:
            return jobs, invalid
    raise NeedsInput('The Lever board reached the page limit; completeness could not be verified. No partial import was saved.')
